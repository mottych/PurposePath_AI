# Implement Admin API Controller for Template & Model Management

## 🎯 Overview

Implement a comprehensive Admin API controller to enable template management, model configuration, usage analytics, and conversation monitoring through an Admin Portal. This feature is fully specified in `pp_ai_backend_specification.md` and includes 15+ endpoints for AI system administration.

## 📋 Complete Specification

**Reference:** `docs/Specifications/pp_ai_backend_specification.md` (780 lines)

### Endpoint Categories

1. **AI Model Management** (Lines 7-116)
   - List available LLM providers and models
   - Update model configuration and pricing

2. **Prompt Template Management** (Lines 119-461)
   - List coaching topics
   - List template versions
   - Get template for editing
   - Create new template version
   - Update existing template
   - Set latest version (activation)
   - Test template with sample data
   - Delete template version

3. **AI Usage Analytics** (Lines 518-627)
   - Get usage statistics by date range
   - Get model performance metrics
   - Aggregate by tenant, model, topic

4. **Conversation Management** (Lines 630-738)
   - List active conversations
   - Get conversation details with full history
   - Monitor completion status

## 🏗️ Implementation Phases

### Phase 1: Read-Only Endpoints (8-12 hours) ⭐ START HERE

**Goal:** Enable admins to view existing templates, models, and usage

**Endpoints:**
- `GET /api/v1/admin/ai/models` - List providers & models
- `GET /api/v1/admin/ai/topics` - List coaching topics  
- `GET /api/v1/admin/ai/prompts/{topic}/versions` - List template versions
- `GET /api/v1/admin/ai/prompts/{topic}/{version}` - Get template content
- `GET /api/v1/admin/ai/conversations` - List conversations
- `GET /api/v1/admin/ai/conversations/{id}` - Conversation details

**Infrastructure to Reuse:**
- ✅ `S3PromptRepository.list_by_topic()` - Exists
- ✅ `S3PromptRepository.get_by_topic()` - Exists
- ✅ `LLMServiceAdapter.get_available_models()` - Exists
- ✅ `ConversationRepository.find_by_tenant()` - Exists

**Files to Create:**
1. `coaching/src/api/routes/admin/__init__.py`
2. `coaching/src/api/routes/admin/models.py`
3. `coaching/src/api/routes/admin/templates.py`
4. `coaching/src/api/routes/admin/conversations.py`
5. `coaching/src/api/middleware/admin_auth.py`

---

### Phase 2: Template Editing (12-16 hours)

**Goal:** Enable creating and updating prompt templates

**Endpoints:**
- `POST /api/v1/admin/ai/prompts/{topic}/versions` - Create new version
- `PUT /api/v1/admin/ai/prompts/{topic}/{version}` - Update template

**New Infrastructure Needed:**
- `S3PromptRepository.create_version()` - Write to S3
- `S3PromptRepository.update_version()` - Update S3 object
- Template validation logic
- S3 bucket write permissions

**Files to Modify:**
1. `coaching/src/infrastructure/repositories/s3_prompt_repository.py` - Add write methods
2. `coaching/src/api/routes/admin/templates.py` - Add POST/PUT handlers

**Files to Create:**
3. `coaching/src/services/template_validation_service.py` - Validate template syntax
4. `coaching/src/services/audit_log_service.py` - Log admin actions

---

### Phase 3: Version Management (8-12 hours)

**Goal:** Activate, deactivate, and delete template versions

**Endpoints:**
- `POST /api/v1/admin/ai/prompts/{topic}/{version}/set-latest` - Activate version
- `DELETE /api/v1/admin/ai/prompts/{topic}/{version}` - Delete version
- `PUT /api/v1/admin/ai/models/{modelId}` - Update model config

**New Infrastructure Needed:**
- Version activation logic (update metadata)
- Prevent deleting active versions
- Model configuration storage (DynamoDB or S3)

**Files to Modify:**
1. `coaching/src/infrastructure/repositories/s3_prompt_repository.py` - Add version management
2. `coaching/src/api/routes/admin/templates.py` - Add version endpoints
3. `coaching/src/api/routes/admin/models.py` - Add model config

**Files to Create:**
4. `coaching/src/domain/entities/model_config.py` - Model configuration entity

---

### Phase 4: Testing & Analytics (8-10 hours)

**Goal:** Test templates before deployment, view usage analytics

**Endpoints:**
- `POST /api/v1/admin/ai/prompts/{topic}/{version}/test` - Test template
- `GET /api/v1/admin/ai/usage` - Usage statistics
- `GET /api/v1/admin/ai/models/{modelId}/metrics` - Model metrics

**New Infrastructure Needed:**
- Template testing framework (render + LLM call)
- Usage analytics queries (requires Phase: Token Tracking)
- Aggregate usage by date range, model, topic

**Files to Create:**
1. `coaching/src/services/template_testing_service.py` - Test templates
2. `coaching/src/api/routes/admin/analytics.py` - Analytics endpoints

---

## 📁 Complete File Structure

```
coaching/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   └── admin/
│   │   │       ├── __init__.py              [NEW - Phase 1]
│   │   │       ├── models.py                [NEW - Phase 1 & 3]
│   │   │       ├── templates.py             [NEW - Phase 1, 2, 3]
│   │   │       ├── conversations.py         [NEW - Phase 1]
│   │   │       └── analytics.py             [NEW - Phase 4]
│   │   └── middleware/
│   │       └── admin_auth.py                [NEW - Phase 1]
│   ├── services/
│   │   ├── template_validation_service.py   [NEW - Phase 2]
│   │   ├── template_testing_service.py      [NEW - Phase 4]
│   │   └── audit_log_service.py             [NEW - Phase 2]
│   ├── domain/
│   │   └── entities/
│   │       └── model_config.py              [NEW - Phase 3]
│   └── infrastructure/
│       └── repositories/
│           └── s3_prompt_repository.py      [MODIFY - Phase 2 & 3]
```

## 🔧 Phase 1 Implementation Details (START HERE)

### Step 1: Admin Auth Middleware

```python
# coaching/src/api/middleware/admin_auth.py

from fastapi import HTTPException, Depends
from coaching.src.api.auth import get_current_context
from shared.models.multitenant import RequestContext, Permission

async def require_admin(
    context: RequestContext = Depends(get_current_context)
) -> RequestContext:
    """Require admin permission for endpoint access."""
    
    if Permission.ADMIN not in context.permissions:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return context
```

### Step 2: Models Router

```python
# coaching/src/api/routes/admin/models.py

from fastapi import APIRouter, Depends
from coaching.src.api.middleware.admin_auth import require_admin
from coaching.src.services.llm_service_adapter import LLMServiceAdapter
from shared.models.schemas import ApiResponse

router = APIRouter(prefix="/api/v1/admin/ai/models", tags=["admin", "models"])

@router.get("/", response_model=ApiResponse[Dict[str, Any]])
async def list_models(
    context: RequestContext = Depends(require_admin),
    llm_service: LLMServiceAdapter = Depends(get_llm_service)
):
    """List all available LLM providers and models."""
    
    providers = []
    
    # Get available models
    models = await llm_service.get_available_models()
    
    # Format response per spec
    bedrock_provider = {
        "name": "bedrock",
        "displayName": "Amazon Bedrock",
        "isActive": True,
        "models": [
            {
                "id": model_id,
                "name": _format_model_name(model_id),
                "provider": "Anthropic",
                "version": _extract_version(model_id),
                "capabilities": ["text_generation", "conversation", "analysis"],
                "maxTokens": 200000,
                "costPer1kTokens": _get_model_pricing(model_id),
                "isActive": True,
                "isDefault": model_id == "anthropic.claude-3-5-sonnet-20241022-v2:0"
            }
            for model_id in models
        ]
    }
    
    providers.append(bedrock_provider)
    
    return ApiResponse(
        success=True,
        data={
            "providers": providers,
            "defaultProvider": "bedrock",
            "defaultModel": "anthropic.claude-3-5-sonnet-20241022-v2:0"
        }
    )
```

### Step 3: Templates Router (Read-Only)

```python
# coaching/src/api/routes/admin/templates.py

from fastapi import APIRouter, Depends, HTTPException
from coaching.src.api.middleware.admin_auth import require_admin
from coaching.src.services.prompt_service import PromptService

router = APIRouter(prefix="/api/v1/admin/ai", tags=["admin", "templates"])

@router.get("/topics")
async def list_topics(
    context: RequestContext = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service)
):
    """List all coaching topics with template metadata."""
    
    # Get all templates from S3
    templates = await prompt_service.list_all_templates()
    
    # Group by topic
    topics_map = {}
    for template in templates:
        topic = template.topic
        if topic not in topics_map:
            topics_map[topic] = {
                "topic": topic,
                "displayName": _format_topic_name(topic),
                "description": template.metadata.get("description", ""),
                "category": template.metadata.get("category", "coaching"),
                "hasTemplates": True,
                "templateCount": 0,
                "latestVersion": None,
                "lastUpdated": None
            }
        
        topics_map[topic]["templateCount"] += 1
        
        if template.is_active:
            topics_map[topic]["latestVersion"] = template.version
            topics_map[topic]["lastUpdated"] = template.created_at
    
    return ApiResponse(
        success=True,
        data=list(topics_map.values())
    )

@router.get("/prompts/{topic}/versions")
async def list_versions(
    topic: str,
    context: RequestContext = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service)
):
    """List all versions of templates for a topic."""
    
    templates = await prompt_service.list_versions_for_topic(topic)
    
    if not templates:
        raise HTTPException(status_code=404, detail=f"Topic '{topic}' not found")
    
    versions = [
        {
            "version": template.version,
            "isLatest": template.is_active,
            "createdAt": template.created_at,
            "createdBy": template.metadata.get("created_by", "system"),
            "description": template.metadata.get("description", ""),
            "templateId": f"tmpl_{topic}_{template.version.replace('.', '_')}",
            "status": "active" if template.is_active else "archived"
        }
        for template in templates
    ]
    
    return ApiResponse(
        success=True,
        data={
            "topic": topic,
            "versions": versions
        }
    )

@router.get("/prompts/{topic}/{version}")
async def get_template(
    topic: str,
    version: str,
    context: RequestContext = Depends(require_admin),
    prompt_service: PromptService = Depends(get_prompt_service)
):
    """Get detailed template content for editing."""
    
    template = await prompt_service.get_template_version(topic, version)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{topic}' version '{version}' not found"
        )
    
    # Format per spec
    response_data = {
        "templateId": f"tmpl_{topic}_{version.replace('.', '_')}",
        "topic": topic,
        "version": version,
        "isLatest": template.is_active,
        "metadata": template.metadata,
        "systemPrompt": template.system_prompt,
        "userPromptTemplate": template.template_text,
        "parameters": _extract_parameters(template),
        "conversationFlow": template.metadata.get("conversationFlow", {}),
        "examples": template.metadata.get("examples", []),
        "createdAt": template.created_at,
        "createdBy": template.metadata.get("created_by", "system"),
        "lastModifiedAt": template.metadata.get("last_modified_at", template.created_at),
        "lastModifiedBy": template.metadata.get("last_modified_by", "system")
    }
    
    return ApiResponse(success=True, data=response_data)
```

### Step 4: Register Admin Routes

```python
# coaching/src/api/main.py

from coaching.src.api.routes.admin import models, templates, conversations

# Add admin routes
app.include_router(models.router)
app.include_router(templates.router)
app.include_router(conversations.router)
```

## ✅ Acceptance Criteria

### Phase 1: Read-Only
- [ ] GET /admin/ai/models returns all available models with pricing
- [ ] GET /admin/ai/topics returns all coaching topics
- [ ] GET /admin/ai/prompts/{topic}/versions lists all versions
- [ ] GET /admin/ai/prompts/{topic}/{version} returns full template
- [ ] GET /admin/ai/conversations lists conversations with filters
- [ ] GET /admin/ai/conversations/{id} returns full history
- [ ] All endpoints require admin permission
- [ ] 403 returned for non-admin users

### Phase 2: Template Editing
- [ ] POST /admin/ai/prompts/{topic}/versions creates new version
- [ ] PUT /admin/ai/prompts/{topic}/{version} updates template
- [ ] Template validation prevents invalid syntax
- [ ] S3 write operations succeed
- [ ] Audit logs record all changes
- [ ] Error handling for S3 failures

### Phase 3: Version Management
- [ ] POST /admin/ai/prompts/{topic}/{version}/set-latest activates version
- [ ] DELETE /admin/ai/prompts/{topic}/{version} deletes version
- [ ] Cannot delete active version
- [ ] PUT /admin/ai/models/{modelId} updates model config
- [ ] Version changes logged

### Phase 4: Testing & Analytics
- [ ] POST /admin/ai/prompts/{topic}/{version}/test tests template
- [ ] GET /admin/ai/usage returns usage statistics
- [ ] GET /admin/ai/models/{modelId}/metrics returns performance
- [ ] Analytics aggregated correctly
- [ ] Test results include token usage and cost

## 🧪 Testing Requirements

### Phase 1 Tests
```python
# tests/unit/test_admin_models.py

async def test_list_models_requires_admin():
    """Test admin permission required."""
    
async def test_list_models_returns_bedrock_provider():
    """Test models endpoint returns correct structure."""
    
# tests/unit/test_admin_templates.py

async def test_list_topics():
    """Test topics listing."""
    
async def test_list_versions_for_topic():
    """Test version listing."""
    
async def test_get_template_content():
    """Test template retrieval."""
```

### Integration Tests
```python
# tests/integration/test_admin_api.py

async def test_admin_workflow():
    """Test complete admin workflow: list → get → update → activate."""
```

## 📊 Monitoring

### Metrics
- Admin API call counts
- Template creation/update frequency
- Template testing usage
- Version activation events

### Logs
```python
logger.info("Admin template updated", admin_user=user_id, topic=topic, version=version)
logger.info("Template version activated", topic=topic, version=version, previous_version=prev_version)
logger.error("Template validation failed", topic=topic, errors=validation_errors)
```

## 🔗 Dependencies

### Phase 1
- ✅ S3PromptRepository (read methods exist)
- ✅ LLMServiceAdapter (exists)
- ✅ ConversationRepository (exists)
- ⚠️ Admin auth middleware (new)

### Phase 2
- ⚠️ S3 write permissions
- ⚠️ Template validation logic
- ⚠️ Audit logging

### Phase 3
- ⚠️ Version management logic
- ⚠️ Model config storage

### Phase 4
- ⚠️ Token usage tracking (separate issue)
- ⚠️ Usage analytics service

## 📈 Estimated Effort

| Phase | Estimate | Priority |
|-------|----------|----------|
| Phase 1: Read-Only | 8-12 hrs | **HIGH** ⭐ |
| Phase 2: Editing | 12-16 hrs | HIGH |
| Phase 3: Version Mgmt | 8-12 hrs | MEDIUM |
| Phase 4: Testing & Analytics | 8-10 hrs | MEDIUM |
| **TOTAL** | **36-50 hrs** | - |

## 🚀 Deployment Strategy

1. **Phase 1:** Deploy read-only endpoints first → Unblock admin portal UI development
2. **Phase 2:** Add editing capabilities → Enable template iteration
3. **Phase 3:** Add version management → Enable safe rollbacks
4. **Phase 4:** Add testing & analytics → Complete admin experience

## 📚 References

- **Full Spec:** `docs/Specifications/pp_ai_backend_specification.md` (780 lines)
- **S3 Repository:** `coaching/src/infrastructure/repositories/s3_prompt_repository.py`
- **LLM Service:** `coaching/src/services/llm_service_adapter.py`
- **Conversation Repo:** `coaching/src/infrastructure/repositories/dynamodb_conversation_repository.py`

## 👥 Assignees

- **Phase 1:** Backend Developer + Frontend Developer (parallel work possible)
- **Phase 2-4:** Backend Developer

## 🏷️ Labels

`feature`, `admin-api`, `templates`, `high-priority`, `backend`, `epic`

---

**Created:** 2025-10-21  
**Status:** Ready for Implementation  
**Priority:** HIGH  
**Type:** Epic (4 phases)
