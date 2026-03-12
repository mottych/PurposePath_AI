# AI Debug Logging

## Overview

The AI execution engine now includes comprehensive debug logging that can be enabled to troubleshoot issues with AI requests, parameter enrichment, template rendering, and responses.

## Enabling Debug Logging

Set the environment variable `AI_DEBUG_LOGGING=true` to enable detailed logging:

```bash
# In Lambda environment variables
AI_DEBUG_LOGGING=true

# Or locally
export AI_DEBUG_LOGGING=true
```

## What Gets Logged

When debug logging is enabled, the following information is logged at each step of the AI execution:

### 1. **Execution Start**
- Topic ID
- Response model
- Input parameters
- User ID, Tenant ID
- User tier

### 2. **Topic Configuration**
- Topic name
- Temperature and max_tokens settings
- Tier level
- Model configuration (default/premium/ultimate)

### 3. **Prompt Templates Loaded**
- System prompt template (from S3)
- User prompt template (from S3)

### 4. **Parameter Enrichment**
- **Before enrichment**: Original request parameters
- Whether template processor is available
- **After enrichment**: Enriched parameters
- List of newly added keys from enrichment

### 5. **Prompt Rendering**
- Rendered system prompt (with parameters injected)
- Rendered user prompt (with parameters injected)

### 6. **Response Format Injection**
- Response model schema
- Final system prompt (with response format instructions)

### 7. **LLM Call**
- Model code and resolved model name
- Temperature and max_tokens
- Messages being sent
- System prompt
- Whether response schema is provided

### 8. **LLM Response**
- Model used
- Finish reason
- Token usage
- **Full response content**

### 9. **Response Serialization**
- Response model type
- Serialized response data

### 10. **Execution Summary**
- Input vs enriched parameters comparison
- Model used and tokens consumed
- Response type

## Log Format

All debug logs are structured JSON with an `ai_debug` field:

```json
{
  "ai_debug": "Starting AI execution",
  "topic_id": "alignment_check",
  "response_model": "AlignmentCheckResponse",
  "input_parameters": {
    "goal_id": "db1f3932-108d-46e8-bb2f-4ec3e9366a66"
  },
  "user_id": "user-123",
  "tenant_id": "tenant-456",
  "user_tier": "ultimate"
}
```

## Viewing Logs

### CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/coaching-dev --follow --format short

# Search for AI debug logs
aws logs filter-pattern '{$.ai_debug = *}' \
  --log-group-name /aws/lambda/coaching-dev \
  --start-time $(date -u -d '10 minutes ago' +%s)000

# Search for specific topic
aws logs filter-pattern '{$.topic_id = "alignment_check"}' \
  --log-group-name /aws/lambda/coaching-dev \
  --start-time $(date -u -d '10 minutes ago' +%s)000
```

### Local Development

When running locally with `AI_DEBUG_LOGGING=true`, debug logs will appear in your console output.

## Example Debug Session

Here's what you'll see for an alignment_check request:

```
1. Starting AI execution
   - topic_id: alignment_check
   - input_parameters: {goal_id: "..."}

2. Topic configuration loaded
   - temperature: 0.5, max_tokens: 2048
   - model: gpt-4o

3. Prompt templates loaded
   - system_prompt: "You are an expert strategic alignment analyst..."
   - user_prompt: "Analyze the alignment of this goal..."

4. Starting parameter enrichment
   - has_template_processor: true
   - parameters_before_enrichment: {goal_id: "..."}

5. Parameter enrichment completed
   - enriched_keys: [goalIntent, businessName, vision, purpose, coreValues, strategies_for_goal]
   - parameters_after_enrichment: {goal_id: "...", goalIntent: "...", ...}

6. Prompts rendered with parameters
   - rendered_user_prompt: "Analyze the alignment of this goal\n\nGOAL INTENT:\nDrive business growth..."

7. Calling LLM
   - model: gpt-4o
   - temperature: 0.5
   - system_prompt: "You are an expert strategic alignment analyst..."

8. LLM response received
   - finish_reason: stop
   - tokens: 245
   - response_content: "{\"alignmentScore\": 85, ...}"

9. Response serialization completed
   - serialized_response: {alignmentScore: 85, explanation: "..."}

10. AI execution completed successfully
```

## Troubleshooting Common Issues

### Issue: Parameters not being enriched
**Look for:** "Parameter enrichment completed" log
**Check:** 
- Are `enriched_keys` empty?
- Is `has_template_processor: false`?
- Do enriched parameters contain expected values?

### Issue: OpenAI schema validation errors
**Look for:** "Response format injected" log
**Check:**
- `response_schema` structure
- Does it have all properties in `required`?
- Are there `$ref` with extra keys?

### Issue: Missing template parameters
**Look for:** "Prompts rendered with parameters" log
**Check:**
- Are there `{placeholder}` names still in rendered prompts?
- Compare `enriched_parameters` with what's used in templates

### Issue: Unexpected AI responses
**Look for:** "LLM response received" log
**Check:**
- `response_content` - what did the AI actually return?
- Compare with expected schema
- Check if response follows prompt instructions

## Performance Impact

Debug logging adds minimal overhead:
- Log statements only execute when `AI_DEBUG_LOGGING=true`
- Long strings (>2000 chars) are automatically truncated in logs
- Structured logging is efficient

**Recommendation:** Enable only when actively debugging, disable in production to reduce log volume and costs.

## Security Note

Debug logs may contain sensitive data:
- User parameters
- Business data
- AI prompts and responses

**Important:** 
- Only enable debug logging in development/staging environments
- Review logs before sharing
- Consider data privacy requirements
