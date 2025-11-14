# LLM Topic Architecture - Plain English Explanation

## Overview

The LLM Topic system is designed to make AI coaching conversations simple and maintainable. Instead of hardcoding prompts and model settings in code, everything is stored in a database and can be updated without deploying new code.

## How It Works

### The Big Picture

When a user starts a coaching conversation, they only need to specify what topic they want to discuss (like "core values" or "purpose"). The system then:

1. Looks up that topic in the database
2. Gets all the prompt text from cloud storage
3. Knows which AI model to use and how to configure it
4. Starts the conversation with the right prompts

Everything the system needs to know about a topic is stored together in one place.

## Key Concepts

### Topics

A **topic** is a complete package that contains everything needed for an AI conversation:

- **Identity**: What it's called and what category it belongs to
- **Prompts**: The actual text that guides the AI's behavior
- **Model Settings**: Which AI model to use and how to tune it
- **Parameters**: What information can be customized in the prompts

### Example Topics

You might have:
- "Core Values Coaching" - A conversational session to explore personal values
- "Core Values Assessment" - A structured evaluation of values
- "Purpose Discovery" - Helping users find their purpose
- "Vision Planning" - Creating a future vision

Each topic can use different AI models, different prompts, and different settings, even if they're in the same category.

### Categories vs Topics

- **Category**: A broad grouping (e.g., "core_values", "purpose", "vision")
- **Topic**: A specific use case within that category

For example:
- Category: "core_values"
  - Topic: "core_values_coaching"
  - Topic: "core_values_assessment"
  - Topic: "core_values_quick_check"

This allows you to have multiple different experiences within the same subject area.

## What's Stored Where

### Database (DynamoDB)

Stores the topic configuration:
- Topic name and description
- Which AI model to use (e.g., Claude 3.5 Sonnet)
- Model settings (temperature, max tokens, etc.)
- Where to find the prompt files
- What parameters are allowed
- Whether the topic is active

### Cloud Storage (S3)

Stores the actual prompt text as markdown files:
- `system.md` - Instructions that define the AI's role and behavior
- `user.md` - The initial message shown to the user

This separation means you can edit prompt text without touching the database.

### Code

The code only needs to:
1. Ask for a topic by name
2. Load the configuration from the database
3. Load the prompts from cloud storage
4. Pass everything to the AI model

## Benefits

### 1. No Code Deployment for Prompt Changes

Want to improve how the AI coaches on core values? Just update the markdown file in cloud storage. No code changes, no deployment, no downtime.

### 2. Easy A/B Testing

Create two versions of the same topic (e.g., "core_values_v1" and "core_values_v2") and test which works better. Switch between them by changing which one is active.

### 3. Topic Reuse

The same topic can be used in multiple places:
- Web application
- Mobile app
- Admin tools
- API integrations

Everyone gets the same consistent experience.

### 4. Flexible Model Selection

Different topics can use different AI models:
- Quick assessments might use a faster, cheaper model
- Deep coaching sessions might use the most powerful model
- Simple tasks might use an older model to save costs

### 5. Clear Ownership

Each topic owns its complete configuration. There's no confusion about which model or settings to use - it's all defined in the topic.

## User Experience

### Starting a Conversation

**User perspective:**
1. User clicks "Start Core Values Coaching"
2. System shows them a welcome message
3. Conversation begins

**What happens behind the scenes:**
1. Frontend sends: `{ "topic": "core_values_coaching" }`
2. Backend looks up "core_values_coaching" in database
3. Backend loads prompts from cloud storage
4. Backend calls AI model with the topic's settings
5. Backend returns the AI's response

### Topic Selection

Users never see topic IDs. They see friendly names:
- Database stores: `topic_id: "core_values_coaching"`
- User sees: "Core Values - Coaching Session"

The mapping is handled automatically.

## Administration

### Adding a New Topic

To add a new coaching topic:

1. **Define the topic** in the database:
   - Choose a unique ID (e.g., "goals_planning")
   - Set the display name ("Goal Planning Session")
   - Choose which AI model to use
   - Set model parameters (temperature, max tokens)
   - Define what parameters are allowed

2. **Create prompt files** in cloud storage:
   - Write `system.md` with AI behavior instructions
   - Write `user.md` with the initial user message
   - Upload to the correct folder

3. **Activate the topic**:
   - Set `is_active: true`
   - Users can now select it

### Updating a Topic

To change an existing topic:

- **Change prompts**: Edit the markdown files in cloud storage
- **Change model settings**: Update the topic in the database
- **Change model**: Update which model code the topic uses
- **Deactivate**: Set `is_active: false` to hide from users

### Topic Versioning

You can version topics by creating copies:
- `core_values_coaching` (original)
- `core_values_coaching_v2` (improved version)

Then switch between them or run both simultaneously.

## System Flow

```
User Request
    ↓
Topic Lookup (Database)
    ↓
Prompt Loading (Cloud Storage)
    ↓
AI Model Call (with topic's settings)
    ↓
Response to User
```

Everything is dynamic and configurable at each step.

## Data Flow

### Request Flow
1. User initiates conversation with topic name
2. System validates topic exists and is active
3. System loads topic configuration
4. System loads prompt content
5. System prepares AI model call with topic's settings
6. System sends request to AI
7. System returns response

### Update Flow
1. Admin updates topic in database OR updates prompt file
2. Cache is cleared (if applicable)
3. Next request uses updated configuration/prompts
4. No code deployment needed

## Security & Access

- Topics can be marked active/inactive
- Inactive topics are not available to users
- Prompt files are stored securely in cloud storage
- Database access is controlled by IAM permissions
- API endpoints require authentication

## Scalability

- Topics are cached for fast access
- Prompt files are cached after first load
- Database queries are efficient (single lookup by topic ID)
- Cloud storage access is optimized
- Multiple topics can be served simultaneously

## Maintenance

### Regular Tasks
- Review and update prompt text for quality
- Monitor which topics are most used
- Adjust model settings based on usage patterns
- Add new topics as needed
- Archive unused topics

### Monitoring
- Track topic usage metrics
- Monitor AI model costs per topic
- Measure conversation success rates by topic
- Identify topics that need improvement

## Future Enhancements

Possible future improvements:
- Topic templates for quick topic creation
- Prompt version history
- Automated prompt testing
- Multi-language prompt support
- Topic usage analytics dashboard
- Recommendation engine for topic selection
