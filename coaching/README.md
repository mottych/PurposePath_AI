# PurposePath Coaching Service

AI-powered coaching conversations service powered by Amazon Bedrock.

## Features

- **Multi-topic Coaching**: Core Values, Purpose, Vision, and Goals
- **Conversational AI**: Powered by Amazon Bedrock (Claude, Llama)
- **Session Management**: Persistent conversations with memory management
- **Scalable Architecture**: Serverless AWS infrastructure
- **Template System**: Flexible prompt management with versioning

## Quick Start

### Prerequisites

- Python 3.11+
- uv package manager
- AWS CLI configured

### Setup

```bash
# Create virtual environment and install dependencies
uv venv --python 3.11
uv pip install -e .[dev]

# Start development server
uv run uvicorn src.api.main:app --reload

# Access the API
# - API Documentation: http://localhost:8000/docs
# - Health Check: http://localhost:8000/api/v1/health
```

## API Endpoints

### Conversations

- `POST /api/v1/conversations/initiate` - Start new coaching conversation
- `POST /api/v1/conversations/{id}/message` - Send message
- `GET /api/v1/conversations/{id}` - Get conversation details
- `POST /api/v1/conversations/{id}/pause` - Pause conversation
- `POST /api/v1/conversations/{id}/resume` - Resume conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `GET /api/v1/conversations/user/{user_id}` - List user conversations

### Health

- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/ready` - Readiness check with dependencies

## Usage Examples

### Starting a Coaching Session

```python
import httpx

# Initialize conversation
response = httpx.post("http://localhost:8000/api/v1/conversations/initiate", json={
    "user_id": "user_123",
    "topic": "core_values",
    "context": {},
    "language": "en"
})

conversation = response.json()
print(f"Started conversation: {conversation['conversation_id']}")
```

### Sending a Message

```python
# Send user message
response = httpx.post(
    f"http://localhost:8000/api/v1/conversations/{conversation_id}/message",
    json={
        "user_message": "I feel most fulfilled when I'm helping others grow in their careers.",
        "metadata": {}
    }
)

ai_response = response.json()
print(f"AI: {ai_response['ai_response']}")
```

## Coaching Topics

### Core Values Discovery

Helps users identify 5-7 fundamental values through structured exploration:
- Motivation and energy sources
- Aversions and frustrations
- Relationship patterns
- Decision-making principles

### Purpose Identification

Guides users to discover their life purpose by exploring:
- Passions and interests
- Desired impact
- Natural strengths
- Legacy aspirations

### Vision Creation

Supports users in crafting compelling future visions:
- Long-term goals
- Success definitions
- Ideal outcomes
- Aspirational scenarios

### Goal Setting

Helps users set and structure achievable goals:
- SMART criteria application
- Priority identification
- Resource assessment
- Obstacle planning

## Development

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test pattern
uv run pytest -k "test_conversation"

# Generate coverage report
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Code formatting
uv run black src/

# Linting
uv run ruff check src/ --fix

# Type checking
uv run mypy src/
```

## Configuration

### Environment Variables

- `STAGE`: Deployment stage (dev/staging/prod)
- `DYNAMODB_TABLE`: DynamoDB table name
- `PROMPTS_BUCKET`: S3 bucket for prompts
- `REDIS_HOST`: Redis host
- `BEDROCK_MODEL_ID`: Default Bedrock model

### Prompt Templates

Templates are stored as YAML files in the `prompts/` directory:

```yaml
topic: core_values
version: 1.0.0
system_prompt: |
  You are an expert executive coach...

initial_message: |
  Welcome! I'm excited to help you...

question_bank:
  - category: motivation
    questions:
      - "What energizes you most?"
      - "When do you feel most alive?"

llm_config:
  model: anthropic.claude-3-sonnet-20240229-v1:0
  temperature: 0.7
  max_tokens: 2000
```