# LLM Service Configuration Integration - Design Document

**Issue:** #72  
**Date:** October 29, 2025  
**Author:** AI Assistant  
**Status:** Implementation Ready

---

## Executive Summary

This document outlines the integration of the configuration-driven LLM system (#67-71) into the runtime LLM service. The goal is to replace hardcoded model IDs and templates with dynamic configuration lookup at runtime.

---

## Current State Analysis

### Existing Architecture

```
LLMService
├── Uses DEFAULT_LLM_MODELS dict (hardcoded)
├── Loads templates via PromptService
├── Provider management via ProviderManager
└── Workflow orchestration via WorkflowOrchestrator
```

### Problems

1. **Hardcoded Model IDs:**
   ```python
   # Line 91-93 in llm_service.py
   model_id = DEFAULT_LLM_MODELS.get(
       CoachingTopic(topic), 
       "anthropic.claude-3-sonnet-20240229-v1:0"
   )
   ```

2. **No Tier-Based Configuration:** Cannot serve different models to free vs premium users

3. **No Admin Control:** Admins cannot change models/templates without code deployment

4. **No Registry Validation:** Model codes not validated against MODEL_REGISTRY

---

## Target Architecture

### New Service Structure

```
LLMService
├── LLMConfigurationService (NEW - tier-based resolution)
├── LLMTemplateService (NEW - template rendering)
├── ProviderManager (existing)
└── WorkflowOrchestrator (existing)
```

### Configuration Flow

```
User Request
    ↓
Interaction Code + User Tier
    ↓
LLMConfigurationService.resolve_configuration()
    ├── Try tier-specific config (e.g., "premium")
    └── Fallback to default config (tier=None)
    ↓
Configuration {model_code, template_id, temperature, ...}
    ↓
LLMTemplateService.render_template()
    ├── Fetch metadata from DynamoDB
    ├── Fetch content from S3
    └── Render with Jinja2
    ↓
ProviderManager.get_provider(model_code)
    ↓
LLM Response
```

---

## Design Decisions

### 1. Backward Compatibility

**Decision:** Maintain backward compatibility during transition

**Approach:**
- Keep existing method signatures
- Add optional `interaction_code` parameter
- Use feature flag for gradual rollout
- Deprecated methods warn but still work

```python
async def generate_coaching_response(
    self,
    conversation_id: str,
    topic: str,  # Legacy - maps to interaction_code
    user_message: str,
    conversation_history: list[dict[str, str]],
    business_context: dict[str, Any] | None = None,
    # NEW PARAMETERS
    interaction_code: str | None = None,  # Preferred
    user_tier: str | None = None,  # For config resolution
    use_config_lookup: bool = True,  # Feature flag
) -> LLMResponse:
    """Generate coaching response."""
    
    # Use new system if enabled
    if use_config_lookup and interaction_code:
        return await self._generate_with_config(
            interaction_code=interaction_code,
            user_tier=user_tier,
            ...
        )
    
    # Legacy path (will be deprecated)
    return await self._generate_legacy(topic, ...)
```

### 2. Configuration Caching

**Decision:** Cache resolved configurations (5-minute TTL)

**Rationale:**
- Reduces DynamoDB queries
- Configuration changes take effect within 5 minutes
- Cache invalidation on config updates

**Implementation:** Already handled by `LLMConfigurationService`

### 3. Template Rendering Strategy

**Decision:** Render templates at request time, cache rendered results

**Rationale:**
- Templates may use request-specific parameters
- Caching rendered templates reduces Jinja2 overhead
- Template content cached separately (10-minute TTL)

**Implementation:** Already handled by `LLMTemplateService`

### 4. Provider Selection

**Decision:** Map `model_code` to provider dynamically

**Approach:**
```python
from coaching.src.core.llm_models import get_model

model = get_model(config.model_code)  # Validates against registry
provider_class_name = model.provider_class  # e.g., "BedrockLLMProvider"

# Get provider from manager
provider = self.provider_manager.get_provider(model.provider.value)
```

### 5. Error Handling

**Decision:** Graceful degradation with fallbacks

**Error Hierarchy:**
1. **ConfigurationNotFoundError** → Use default configuration
2. **TemplateNotFoundError** → Use legacy prompt service
3. **ProviderError** → Use provider manager's fallback chain

---

## Implementation Phases

### Phase 1: Service Integration (Constructor)

**Goal:** Inject configuration services into LLMService

**Changes:**
```python
# coaching/src/services/llm_service.py

class LLMService:
    def __init__(
        self,
        provider_manager: ProviderManager,
        workflow_orchestrator: WorkflowOrchestrator,
        prompt_service: PromptService,
        # NEW DEPENDENCIES
        config_service: LLMConfigurationService,
        template_service: LLMTemplateService,
        tenant_id: str | None = None,
        user_id: str | None = None,
        default_provider: str = "bedrock",
        fallback_providers: list[str] | None = None,
    ):
        self.config_service = config_service
        self.template_service = template_service
        # ... existing code ...
```

**Files Modified:**
- `coaching/src/services/llm_service.py`
- `coaching/src/api/dependencies.py`

### Phase 2: Configuration Lookup Methods

**Goal:** Add helper methods for configuration resolution

**New Methods:**
```python
async def _resolve_configuration(
    self,
    interaction_code: str,
    user_tier: str | None = None,
) -> LLMConfiguration:
    """Resolve configuration with fallback."""
    try:
        config = await self.config_service.resolve_configuration(
            interaction_code=interaction_code,
            tier=user_tier,
        )
        logger.info(
            "Configuration resolved",
            interaction_code=interaction_code,
            config_id=config.config_id,
            model_code=config.model_code,
        )
        return config
    except ConfigurationNotFoundError as e:
        logger.warning(
            "Configuration not found, using defaults",
            interaction_code=interaction_code,
            tier=user_tier,
            error=str(e),
        )
        # Return default configuration
        return self._get_default_configuration(interaction_code)

async def _render_template(
    self,
    template_id: str,
    parameters: dict[str, Any],
) -> str:
    """Render template with parameters."""
    try:
        rendered = await self.template_service.render_template(
            template_id=template_id,
            parameters=parameters,
        )
        return rendered
    except TemplateNotFoundError:
        logger.warning("Template not found, using legacy prompts")
        # Fallback to legacy prompt service
        return None
```

### Phase 3: Update generate_coaching_response

**Goal:** Add configuration-driven path to main method

**Implementation:**
```python
async def generate_coaching_response(
    self,
    conversation_id: str,
    topic: str,
    user_message: str,
    conversation_history: list[dict[str, str]],
    business_context: dict[str, Any] | None = None,
    # NEW PARAMETERS
    interaction_code: str | None = None,
    user_tier: str | None = None,
    template_parameters: dict[str, Any] | None = None,
    use_config_lookup: bool = True,
) -> LLMResponse:
    """Generate coaching response."""
    
    # NEW: Configuration-driven path
    if use_config_lookup and interaction_code:
        # Resolve configuration
        config = await self._resolve_configuration(interaction_code, user_tier)
        
        # Render template
        system_prompt = None
        if config.template_id and template_parameters:
            system_prompt = await self._render_template(
                template_id=config.template_id,
                parameters=template_parameters,
            )
        
        # Get provider based on model
        model = get_model(config.model_code)
        provider = self.provider_manager.get_provider(model.provider.value)
        
        # Generate response
        response = await provider.generate(
            messages=conversation_history,
            model=config.model_code,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=system_prompt,
        )
        
        logger.info(
            "Config-driven response generated",
            interaction_code=interaction_code,
            config_id=config.config_id,
        )
        
        return response
    
    # LEGACY: Existing path (unchanged)
    template = await self.prompt_service.get_template(topic)
    model_id = DEFAULT_LLM_MODELS.get(
        CoachingTopic(topic), 
        "anthropic.claude-3-sonnet-20240229-v1:0"
    )
    # ... rest of existing code ...
```

### Phase 4: Update All Service Methods

**Methods to Update:**
- `generate_coaching_response()` ✅ (Phase 3)
- `generate_single_shot_analysis()`
- `generate_insights()`
- Any other LLM generation methods

**Pattern for Each:**
1. Add `interaction_code` and `user_tier` parameters
2. Add `use_config_lookup` feature flag
3. Implement config-driven path
4. Keep legacy path for backward compatibility

### Phase 5: Update Dependencies

**Goal:** Wire up configuration services in dependency injection

**Changes to dependencies.py:**
```python
async def get_config_service() -> LLMConfigurationService:
    """Get configuration service."""
    config_repo = await get_llm_configuration_repository()
    cache_service = await get_cache_service()
    
    return LLMConfigurationService(
        configuration_repository=config_repo,
        cache_service=cache_service,
    )

async def get_template_service() -> LLMTemplateService:
    """Get template service."""
    template_repo = await get_template_metadata_repository()
    s3_client = get_s3_client_singleton()
    cache_service = await get_cache_service()
    
    return LLMTemplateService(
        template_repository=template_repo,
        s3_client=s3_client,
        cache_service=cache_service,
    )

async def get_llm_service(
    provider_manager: ProviderManager = Depends(get_provider_manager),
    workflow_orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
    prompt_service: PromptService = Depends(get_prompt_service),
    config_service: LLMConfigurationService = Depends(get_config_service),
    template_service: LLMTemplateService = Depends(get_template_service),
    context: RequestContext = Depends(get_current_context),
) -> LLMService:
    """Get LLM service with configuration support."""
    return LLMService(
        provider_manager=provider_manager,
        workflow_orchestrator=workflow_orchestrator,
        prompt_service=prompt_service,
        config_service=config_service,
        template_service=template_service,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
    )
```

### Phase 6: Testing

**Unit Tests:**
- Test configuration resolution (with/without tier)
- Test template rendering
- Test fallback behavior
- Test legacy path still works
- Mock all external services

**Integration Tests:**
- Test end-to-end with real configurations
- Test cache behavior
- Test configuration changes take effect
- Test multi-tenant scenarios

---

## Migration Strategy

### Step 1: Add Feature Flag

```python
# coaching/src/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    use_llm_config_system: bool = Field(
        default=False,
        description="Enable configuration-driven LLM system"
    )
```

### Step 2: Gradual Rollout

1. **Week 1:** Deploy with feature flag OFF, validate no regressions
2. **Week 2:** Enable for staging environment, monitor
3. **Week 3:** Enable for 10% of production users (canary)
4. **Week 4:** Enable for 50% of production users
5. **Week 5:** Enable for 100% of production users
6. **Week 6:** Remove legacy code paths

### Step 3: Monitoring

**Metrics to Track:**
- Configuration lookup latency
- Template rendering latency
- Cache hit rates
- Fallback frequency
- Error rates

---

## Risk Mitigation

### Risk 1: Performance Degradation

**Mitigation:**
- Implement aggressive caching (already done)
- Monitor P95 latency closely
- Keep legacy path as fallback

### Risk 2: Configuration Not Found

**Mitigation:**
- Default configurations for all interactions
- Fallback to legacy system
- Alerts on repeated failures

### Risk 3: Breaking Changes

**Mitigation:**
- Maintain backward compatibility
- Feature flag for gradual rollout
- Comprehensive integration tests

---

## Success Criteria

1. ✅ Zero hardcoded model IDs in code
2. ✅ All LLM calls use configuration lookup
3. ✅ Tier-based model selection works
4. ✅ Admin can change configs without deployment
5. ✅ P95 latency < 200ms for config lookup
6. ✅ Cache hit rate > 80%
7. ✅ All existing tests pass
8. ✅ Zero production errors after rollout

---

## Timeline

- **Phase 1-2:** 1 day
- **Phase 3-4:** 2 days
- **Phase 5:** 1 day
- **Phase 6:** 1 day
- **Total:** 5 days

---

## Appendix A: Interaction Code Constants

Create a new file for type-safe interaction codes:

```python
# coaching/src/core/interaction_codes.py
"""Type-safe interaction code constants."""

from typing import Final

# Coaching interactions
COACHING_RESPONSE: Final[str] = "COACHING_RESPONSE"
ALIGNMENT_EXPLANATION: Final[str] = "ALIGNMENT_EXPLANATION"
ALIGNMENT_SUGGESTIONS: Final[str] = "ALIGNMENT_SUGGESTIONS"

# Analysis interactions
ALIGNMENT_ANALYSIS: Final[str] = "ALIGNMENT_ANALYSIS"
STRATEGY_ANALYSIS: Final[str] = "STRATEGY_ANALYSIS"
KPI_ANALYSIS: Final[str] = "KPI_ANALYSIS"

# Operations interactions
STRATEGIC_ALIGNMENT: Final[str] = "STRATEGIC_ALIGNMENT"
ROOT_CAUSE_ANALYSIS: Final[str] = "ROOT_CAUSE_ANALYSIS"
ACTION_SUGGESTIONS: Final[str] = "ACTION_SUGGESTIONS"
PRIORITIZATION_SUGGESTIONS: Final[str] = "PRIORITIZATION_SUGGESTIONS"
SCHEDULING_SUGGESTIONS: Final[str] = "SCHEDULING_SUGGESTIONS"

# Insights interactions
INSIGHTS_GENERATION: Final[str] = "INSIGHTS_GENERATION"

# Onboarding interactions
ONBOARDING_SUGGESTIONS: Final[str] = "ONBOARDING_SUGGESTIONS"
WEBSITE_SCAN: Final[str] = "WEBSITE_SCAN"

__all__ = [
    "COACHING_RESPONSE",
    "ALIGNMENT_EXPLANATION",
    "ALIGNMENT_SUGGESTIONS",
    "ALIGNMENT_ANALYSIS",
    "STRATEGY_ANALYSIS",
    "KPI_ANALYSIS",
    "STRATEGIC_ALIGNMENT",
    "ROOT_CAUSE_ANALYSIS",
    "ACTION_SUGGESTIONS",
    "PRIORITIZATION_SUGGESTIONS",
    "SCHEDULING_SUGGESTIONS",
    "INSIGHTS_GENERATION",
    "ONBOARDING_SUGGESTIONS",
    "WEBSITE_SCAN",
]
```

---

**End of Design Document**
