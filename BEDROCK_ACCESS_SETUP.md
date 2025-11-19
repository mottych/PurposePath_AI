# AWS Bedrock Anthropic Model Access Setup Guide

## Current Situation

AWS has updated their Bedrock access model:
- ✅ **All serverless foundation models are automatically enabled**
- ✅ No manual "Model access" page needed anymore
- ⚠️ **Exception:** Anthropic models require first-time use case submission

---

## Error You're Seeing

```
ResourceNotFoundException: Model use case details have not been submitted
for this account. Fill out the Anthropic use case details form before using
the model.
```

**This means:** You need to submit use case details to Anthropic **one time per AWS account**.

---

## Solution: Two Methods

### Method 1: Using AWS Console (Easiest)

1. **Open AWS Bedrock Console**
   - Navigate to: https://console.aws.amazon.com/bedrock/
   - Select Region: **us-east-1** (or your configured region)

2. **Access the Model Catalog**
   - Click **"Model catalog"** in the left sidebar
   - Or go directly to: https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/models

3. **Select an Anthropic Model**
   - Find any Anthropic Claude model:
     - `Claude 3.5 Sonnet` (recommended)
     - `Claude 3 Sonnet` (what you're currently using)
     - `Claude 3 Haiku` (faster, cheaper)
   - Click on the model card

4. **Open in Playground**
   - Click **"Open in Playground"** button
   - This will prompt you to submit use case details

5. **Submit Use Case Form**
   - Fill out the form with your business information:
     - **Company Name:** Your company name
     - **Use Case:** "AI-powered business coaching platform"
     - **Description:**
       ```
       We provide AI-powered coaching services to help businesses
       align their purpose, vision, and operations. The AI analyzes
       business websites, provides strategic insights, and offers
       personalized coaching guidance.
       ```
     - **Expected Monthly Usage:** Start with "Low" or "Medium"

6. **Submit and Wait**
   - Click **Submit**
   - Access is granted **immediately** after successful submission
   - If there's a delay, wait 15-30 minutes

---

### Method 2: Using AWS CLI/API

If you prefer programmatic access:

```bash
# Ensure you have AWS CLI configured
aws configure

# Submit use case details using API
aws bedrock put-use-case-for-model-access \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --use-case "AI-powered business coaching and strategic analysis platform" \
  --region us-east-1
```

---

## Required IAM Permissions

### Check Your Current Permissions

Run this command to verify you have the necessary permissions:

```bash
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

### Required Permissions

Your IAM user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel",
        "bedrock:PutUseCaseForModelAccess"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "aws-marketplace:Subscribe"
      ],
      "Resource": "*"
    }
  ]
}
```

### Create/Update IAM Policy

If you need to add these permissions:

1. **Go to IAM Console:** https://console.aws.amazon.com/iam/
2. **Navigate to:** Policies → Create policy
3. **Use JSON editor** and paste the policy above
4. **Name it:** `BedrockAnthropicAccess`
5. **Attach to your user/role**

---

## Verification Steps

### Step 1: Verify IAM Permissions

```bash
# Test if you can list Bedrock models
aws bedrock list-foundation-models --region us-east-1

# You should see a list of models including Anthropic ones
```

### Step 2: Check Use Case Submission Status

After submitting the use case form, verify access:

```bash
# Try to invoke a simple prompt
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
  --region us-east-1 \
  output.txt

# If successful, you'll see a response in output.txt
cat output.txt
```

### Step 3: Run Our Test Script

```bash
cd /c/Projects/XBS/PurposePath/PurposePath_Api/pp_ai
source .venv/Scripts/activate
python test_website_scan.py
```

**Expected result:** All tests should pass including "AI Website Scanning"

---

## Troubleshooting

### Error: "Access Denied"

**Problem:** IAM permissions insufficient

**Solution:**
1. Check IAM policy includes `bedrock:InvokeModel`
2. Check AWS Marketplace subscription permissions
3. Ensure you're using the correct AWS region

### Error: "Use case details not submitted"

**Problem:** Form not submitted or not processed

**Solution:**
1. Revisit AWS Bedrock Console → Model Catalog
2. Open any Anthropic model in Playground
3. Complete the use case form again
4. Wait 15-30 minutes if just submitted

### Error: "Model not found"

**Problem:** Wrong model ID or region

**Solution:**
1. Verify model ID: `anthropic.claude-3-sonnet-20240229-v1:0`
2. Verify region: `us-east-1`
3. Check available models:
   ```bash
   aws bedrock list-foundation-models --region us-east-1 | grep anthropic
   ```

---

## Alternative: Use a Different Model

If you want to test immediately without waiting for Anthropic approval:

### Option 1: Use Amazon Titan (No form required)

Update your configuration to use Amazon's Titan model:

```python
# In test script or configuration
model_id = "amazon.titan-text-express-v1"  # Instead of Anthropic
```

### Option 2: Use OpenAI via Bedrock

If you have OpenAI configured:

```bash
export OPENAI_API_KEY="sk-..."
```

Then update provider to use OpenAI instead of Bedrock.

---

## Quick Start Checklist

- [ ] Open AWS Bedrock Console (us-east-1)
- [ ] Navigate to Model Catalog
- [ ] Click on any Anthropic Claude model
- [ ] Click "Open in Playground"
- [ ] Fill out use case form:
  - Company name
  - Use case: AI business coaching
  - Expected usage
- [ ] Submit form
- [ ] Wait for confirmation (immediate or up to 30 min)
- [ ] Run test script: `python test_website_scan.py`
- [ ] Verify all tests pass ✅

---

## Expected Timeline

| Step | Duration |
|------|----------|
| Fill out form | 2-5 minutes |
| AWS processing | Immediate to 30 minutes |
| First API call | Instant once approved |

---

## Support Resources

- **AWS Bedrock Documentation:** https://docs.aws.amazon.com/bedrock/
- **Anthropic on Bedrock:** https://docs.anthropic.com/claude/docs/claude-on-amazon-bedrock
- **Model IDs Reference:** https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html

---

## After Access is Granted

Once you have access, no code changes are needed:

1. ✅ Run `python test_website_scan.py` - should fully pass
2. ✅ Deploy to production
3. ✅ Test the endpoint:
   ```bash
   POST https://api.dev.purposepath.app/coaching/api/v1/website/scan
   ```

**The feature is ready to go!** 🚀
