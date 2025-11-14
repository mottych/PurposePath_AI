# Deprecation Notices

This document tracks deprecated features and their migration paths.

## Version 1.5.0 Deprecations

### PromptTemplate Entity (Deprecated)

**Status:** Deprecated in v1.5.0, will be removed in v2.0.0

**Reason:** Replaced by the unified LLMTopic system which provides better architecture and clearer ownership.

**Migration Path:**

```python
# OLD (Deprecated)
from coaching.src.domain.entities.prompt_template import PromptTemplate

template = PromptTemplate(
    template_id="core_values_v1",
    name="Core Values Discovery",
    topic=CoachingTopic.CORE_VALUES,
    phase=ConversationPhase.EXPLORATION,
    system_prompt="You are a coach...",
    template_text="Let's explore {topic}...",
    variables=["topic"]
)

# NEW (Recommended)
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.repositories.topic_repository import TopicRepository

# Get topic from repository
topic_repo = TopicRepository(...)
topic = await topic_repo.get_topic_by_id("core_values_coaching")

# Get prompt content via PromptService
from coaching.src.services.prompt_service import PromptService

prompt_service = PromptService(topic_repo, s3_storage, cache)
prompt = await prompt_service.get_prompt(
    topic_id="core_values_coaching",
    prompt_type="system",
    parameters={"user_name": "John"}
)
```

**What Changed:**
- Prompts are now stored in S3 as markdown files
- Topics own their model configuration directly
- No more phase-based templates
- Cleaner separation of concerns

---

### LLMConfiguration Entity (Deprecated)

**Status:** Deprecated in v1.5.0, will be removed in v2.0.0

**Reason:** Topics now own their model configuration directly. The old configuration system with `template_id` references created unnecessary indirection.

**Migration Path:**

```python
# OLD (Deprecated)
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration

config = LLMConfiguration(
    config_id="config_123",
    interaction_code="core_values_coaching",
    template_id="core_values_v1",  # ❌ Wrong architecture
    model_code="claude-3-5-sonnet",
    temperature=0.7,
    max_tokens=2000
)

# NEW (Recommended)
from coaching.src.domain.entities.llm_topic import LLMTopic

topic = LLMTopic(
    topic_id="core_values_coaching",
    topic_name="Core Values Discovery",
    topic_type="coaching",
    category="core_values",
    model_code="claude-3-5-sonnet-20241022",  # Model config owned by topic
    temperature=0.7,
    max_tokens=2000,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    # ... prompts, parameters, etc.
)
```

**What Changed:**
- Model configuration is now part of LLMTopic
- No more `template_id` field
- Topics are the single source of truth
- Simpler, more intuitive architecture

---

### Old Admin Configuration Routes (Deprecated)

**Status:** Deprecated in v1.5.0, will be removed in v2.0.0

**Affected Endpoints:**
- `POST /api/v1/admin/configurations`
- `GET /api/v1/admin/configurations`
- `PUT /api/v1/admin/configurations/{config_id}`
- `DELETE /api/v1/admin/configurations/{config_id}`

**Replacement:** Use new topic-based admin endpoints

**New Endpoints:**
- `GET /api/v1/admin/topics` - List all topics
- `GET /api/v1/admin/topics/{topic_id}` - Get topic details
- `POST /api/v1/admin/topics` - Create new topic
- `PUT /api/v1/admin/topics/{topic_id}` - Update topic
- `DELETE /api/v1/admin/topics/{topic_id}` - Delete topic
- `GET /api/v1/admin/topics/{topic_id}/prompts/{prompt_type}` - Get prompt content
- `PUT /api/v1/admin/topics/{topic_id}/prompts/{prompt_type}` - Update prompt
- `POST /api/v1/admin/topics/{topic_id}/prompts` - Create prompt
- `DELETE /api/v1/admin/topics/{topic_id}/prompts/{prompt_type}` - Delete prompt
- `GET /api/v1/admin/models` - List available models
- `POST /api/v1/admin/topics/validate` - Validate topic config

See `docs/Specifications/admin_ai_specifications.md` for full API documentation.

---

## Migration Timeline

- **v1.5.0** (Current): Deprecation warnings added, both systems functional
- **v1.6.0**: Old system marked as legacy, warnings become more prominent
- **v2.0.0**: Old system removed entirely

## Questions?

If you have questions about migrating from deprecated features, please:
1. Review the migration examples above
2. Check the specification documents in `docs/Specifications/`
3. Contact the development team

## Suppressing Warnings (Not Recommended)

If you need to temporarily suppress deprecation warnings:

```python
import warnings

# Suppress all deprecation warnings (not recommended)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress specific warnings (better)
warnings.filterwarnings(
    "ignore",
    message="PromptTemplate is deprecated",
    category=DeprecationWarning
)
```

**Note:** Suppressing warnings does not prevent removal in v2.0.0. Please migrate as soon as possible.
