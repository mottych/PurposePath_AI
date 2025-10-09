# PurposePath AI Coaching - Revised Implementation Roadmap

**Document Version:** 2.0.0  
**Last Updated:** October 9, 2025  
**Status:** Active Implementation Guide  
**Based On:** AI_COACHING_ARCHITECTURE_DESIGN.md v1.0.0

---

## 🎯 Key Revisions from Original Plan

### Major Changes
1. **Testing Integration** - Tests written alongside implementation in each phase (not deferred to Phase 6)
2. **Observability First** - Structured logging and monitoring from Phase 1 (not Phase 7)
3. **Migration Strategy** - Clear approach for transitioning from current code to new architecture
4. **Multi-Tenancy Consolidation** - Single codebase with tenant-scoped queries
5. **Phase Reorganization** - 8 focused phases instead of scattered approach

### Development Principles
- ✅ **Bottom-Up Architecture** - Domain → Infrastructure → Services → API
- ✅ **Test-First Development** - Unit tests accompany every component
- ✅ **Incremental Migration** - Preserve existing functionality while refactoring
- ✅ **Quality Gates** - No phase advances without passing tests and type checks
- ✅ **GitHub Issues** - Every phase tracked with acceptance criteria

---

## 📋 Implementation Phases Overview

| Phase | Focus | Duration | Dependencies | Testing |
|-------|-------|----------|--------------|---------|
| **Phase 1** | Foundation & Domain Core | 2 weeks | None | Unit tests (70%+ coverage) |
| **Phase 2** | Domain Events & Exceptions | 1 week | Phase 1 | Unit tests (80%+ coverage) |
| **Phase 3** | Infrastructure Layer | 2 weeks | Phase 1-2 | Integration tests |
| **Phase 4** | Application Services | 2-3 weeks | Phase 1-3 | Unit + Integration |
| **Phase 5** | Analysis Services (One-Shot) | 2 weeks | Phase 1-4 | E2E tests |
| **Phase 6** | LangGraph Workflow Migration | 2 weeks | Phase 1-5 | Workflow tests |
| **Phase 7** | API Layer & Routes | 1-2 weeks | Phase 1-6 | API tests |
| **Phase 8** | Production Readiness | 1-2 weeks | Phase 1-7 | Performance tests |

**Total Estimated Duration**: 12-15 weeks

---

## Phase 1: Foundation & Domain Core

**Duration**: 2 weeks  
**GitHub Issue**: #2, #3, #4, #5  
**Status**: In Progress

### Objectives
Establish the foundational type system, domain value objects, entities, and domain services with complete test coverage and observability.

### Deliverables

#### 1.1 Core Type System (`coaching/src/core/types.py`)
```python
# Domain IDs with NewType for compile-time safety
ConversationId, TemplateId, AnalysisRequestId, UserId, TenantId

# ID factory functions
create_conversation_id(), create_template_id(), create_analysis_request_id()
```

**Tests**: `tests/unit/core/test_types.py`
- ✅ ID creation and uniqueness
- ✅ Type safety validation

#### 1.2 Enhanced Constants (`coaching/src/core/constants.py`)
```python
# Enums
CoachingTopic, AnalysisType, ConversationStatus, ConversationPhase, MessageRole

# Business Rules
PHASE_PROGRESS_WEIGHTS, PHASE_REQUIREMENTS, DEFAULT_LLM_MODELS
```

**Tests**: `tests/unit/core/test_constants.py`
- ✅ Enum completeness
- ✅ Business rule validation

#### 1.3 Domain Value Objects (`coaching/src/domain/value_objects/`)
- `message.py` - Message (role, content, timestamp, metadata)
- `conversation_context.py` - ConversationContext (phase, insights, progress)
- `alignment_score.py` - AlignmentScore, ComponentScores, FoundationAlignment
- `strategy_recommendation.py` - StrategyRecommendation
- `enriched_context.py` - EnrichedContext, BusinessFoundation, GoalContext

**Tests**: `tests/unit/domain/value_objects/test_*.py`
- ✅ Immutability enforcement
- ✅ Validation rules
- ✅ Business logic methods

#### 1.4 Domain Entities (`coaching/src/domain/entities/`)
- `conversation.py` - Conversation aggregate root with business rules
- `prompt_template.py` - PromptTemplate aggregate root
- `analysis_request.py` - AnalysisRequest value object

**Tests**: `tests/unit/domain/entities/test_*.py`
- ✅ Aggregate invariants
- ✅ Business rule enforcement
- ✅ State transitions

#### 1.5 Domain Services (`coaching/src/domain/services/`)
- `alignment_calculator.py` - Alignment scoring algorithm
- `phase_transition_service.py` - Conversation phase management
- `completion_validator.py` - Conversation completion rules

**Tests**: `tests/unit/domain/services/test_*.py`
- ✅ Calculation correctness
- ✅ Edge cases
- ✅ Business rule validation

#### 1.6 Observability Foundation (`coaching/src/infrastructure/observability/`)
- `logger.py` - Structured logging with structlog
- `metrics.py` - Custom metrics collection
- `tracer.py` - AWS X-Ray integration stubs

**Tests**: `tests/unit/infrastructure/observability/test_*.py`
- ✅ Log context propagation
- ✅ PII redaction
- ✅ Metric recording

### Migration Strategy
- **Preserve** existing `coaching/src/models/conversation.py`
- **Create** new `coaching/src/domain/entities/conversation.py`
- **Add** deprecation warnings to old models
- **Implement** `coaching/src/adapters/conversation_adapter.py` to bridge old/new

### Acceptance Criteria
- [ ] All domain value objects immutable and validated
- [ ] Conversation aggregate enforces all business rules
- [ ] Domain services isolated from infrastructure
- [ ] 70%+ unit test coverage
- [ ] Mypy passes with strict mode
- [ ] Structured logging working in all layers
- [ ] Zero `dict[str, Any]` in domain layer

### Definition of Done
- [ ] GitHub issues #2, #3, #4, #5 closed
- [ ] All tests passing (pytest)
- [ ] No type errors (mypy --strict)
- [ ] No lint errors (ruff check)
- [ ] Code formatted (black)
- [ ] Documentation updated
- [ ] PR reviewed and merged

---

## Phase 2: Domain Events & Exceptions

**Duration**: 1 week  
**GitHub Issue**: #TBD (New)  
**Dependencies**: Phase 1

### Objectives
Implement domain events for observability and business analytics, plus domain-specific exceptions.

### Deliverables

#### 2.1 Domain Events (`coaching/src/domain/events/`)
- `conversation_events.py`
  - ConversationInitiated, MessageAdded, PhaseTransitioned
  - ConversationCompleted, ConversationPaused
- `analysis_events.py`
  - AnalysisRequested, AnalysisCompleted, AnalysisFailed

**Tests**: `tests/unit/domain/events/test_*.py`
- ✅ Event creation
- ✅ Event serialization
- ✅ Timestamp handling

#### 2.2 Domain Exceptions (`coaching/src/domain/exceptions/`)
- `conversation_exceptions.py`
  - ConversationNotFound, InvalidPhaseTransition, ConversationNotActive
- `analysis_exceptions.py`
  - InvalidAnalysisRequest, EnrichmentFailed

**Tests**: `tests/unit/domain/exceptions/test_*.py`
- ✅ Exception hierarchy
- ✅ Error messages
- ✅ Exception context

### Acceptance Criteria
- [ ] All domain events inherit from base DomainEvent
- [ ] Events include correlation IDs for tracing
- [ ] Exceptions are specific and actionable
- [ ] 80%+ test coverage
- [ ] Events logged via structured logger

---

## Phase 3: Infrastructure Layer

**Duration**: 2 weeks  
**GitHub Issue**: #6, #7  
**Dependencies**: Phase 1, 2

### Objectives
Implement infrastructure adapters (repositories, LLM providers, external clients) with proper abstractions.

### Deliverables

#### 3.1 Repository Interfaces (`coaching/src/domain/ports/`)
- `conversation_repository_port.py` - ConversationRepositoryPort protocol
- `prompt_repository_port.py` - PromptRepositoryPort protocol
- `insights_repository_port.py` - InsightsRepositoryPort protocol

#### 3.2 Repository Implementations (`coaching/src/infrastructure/repositories/`)
- Refactor existing `conversation_repository.py` to implement port
- Refactor `prompt_repository.py` to use new domain entities
- Add `redis_conversation_cache.py` for session caching

**Tests**: `tests/integration/repositories/test_*.py`
- ✅ DynamoDB CRUD operations
- ✅ S3 template retrieval
- ✅ Redis caching
- ✅ Multi-tenancy scoping

#### 3.3 LLM Provider Abstraction (`coaching/src/infrastructure/llm/providers/`)
- `base.py` - LLMProviderStrategy protocol
- `bedrock.py` - BedrockClaudeProvider, BedrockLlamaProvider
- `anthropic.py` - AnthropicProvider (backup)
- `manager.py` - LLMProviderManager (factory)

**Tests**: `tests/integration/llm/test_*.py`
- ✅ Provider initialization
- ✅ Response generation
- ✅ Streaming support
- ✅ Error handling and retries

#### 3.4 External Service Clients (`coaching/src/infrastructure/external/`)
- `step_functions/client.py` - Step Functions orchestration client
- `business_api/client.py` - .NET Business API client
- Circuit breaker and retry implementations

**Tests**: `tests/integration/external/test_*.py` (with mocks)
- ✅ Step Functions execution
- ✅ Business API calls
- ✅ Circuit breaker activation
- ✅ Retry logic

#### 3.5 Cache Implementations (`coaching/src/infrastructure/cache/`)
- `redis_cache.py` - Production Redis cache
- `in_memory_cache.py` - Testing/development cache

**Tests**: `tests/integration/cache/test_*.py`
- ✅ Cache hit/miss
- ✅ TTL expiration
- ✅ Eviction policies

### Migration Strategy
- **Refactor** existing repositories to implement new ports
- **Add adapter layer** for backward compatibility
- **Gradually migrate** service layer to use new repositories

### Acceptance Criteria
- [ ] All repositories implement port interfaces
- [ ] LLM providers interchangeable via strategy pattern
- [ ] External clients have circuit breakers
- [ ] 70%+ integration test coverage
- [ ] Observability hooks in all infrastructure

---

## Phase 4: Application Services

**Duration**: 2-3 weeks  
**GitHub Issue**: #15  
**Dependencies**: Phase 1-3

### Objectives
Refactor and implement service layer using new domain and infrastructure components.

### Deliverables

#### 4.1 Conversation Services (`coaching/src/services/conversation/`)
- Refactor `conversation_service.py` to use domain entities
- `conversation_flow_service.py` - Phase transition orchestration
- `conversation_memory_service.py` - Memory summarization
- Consolidate multi-tenant logic into main service

**Tests**: `tests/unit/services/conversation/test_*.py`
- ✅ Service orchestration
- ✅ Dependency injection
- ✅ Error handling

#### 4.2 LLM Services (`coaching/src/services/llm/`)
- Refactor `llm_service.py` to use provider manager
- `response_parser_service.py` - Structured output parsing
- Mark `llm_service_adapter.py` as deprecated

**Tests**: `tests/unit/services/llm/test_*.py`
- ✅ Provider selection
- ✅ Response parsing
- ✅ Token tracking

#### 4.3 Prompt Services (`coaching/src/services/prompt/`)
- `prompt_service.py` - Template retrieval (refactored)
- `prompt_builder_service.py` - Prompt construction
- `template_engine.py` - Placeholder resolution

**Tests**: `tests/unit/services/prompt/test_*.py`
- ✅ Template loading
- ✅ Placeholder injection
- ✅ Version management

#### 4.4 Cache Service (`coaching/src/services/cache_service.py`)
- Refactor to use infrastructure cache implementations
- Add metrics for cache hit rates

**Tests**: `tests/unit/services/test_cache_service.py`

### Acceptance Criteria
- [ ] All services use dependency injection
- [ ] Services depend on ports, not implementations
- [ ] Multi-tenancy consolidated
- [ ] 75%+ test coverage
- [ ] All deprecated code marked

---

## Phase 5: Analysis Services (One-Shot)

**Duration**: 2 weeks  
**GitHub Issue**: #8, #9, #10  
**Dependencies**: Phase 1-4

### Objectives
Implement one-shot analysis services with context enrichment.

### Deliverables

#### 5.1 Enrichment Services (`coaching/src/services/enrichment/`)
- `enrichment_service.py` - Main orchestrator
- `step_function_client.py` - Step Functions interface
- `business_api_client.py` - .NET API client wrapper
- Enrichment strategies:
  - `alignment_enrichment.py`
  - `coaching_enrichment.py`
  - `operations_enrichment.py`

**Tests**: `tests/unit/services/enrichment/test_*.py` (with mocks)
- ✅ Context enrichment
- ✅ Strategy selection
- ✅ Caching

#### 5.2 Analysis Services (`coaching/src/services/analysis/`)
- `base_analysis_service.py` - Template method pattern
- `alignment_service.py` - Alignment scoring, explanation, suggestions
- `strategy_service.py` - Strategy recommendations
- `kpi_service.py` - KPI recommendations
- `swot_service.py` - SWOT analysis
- `root_cause_service.py` - Root cause and five whys
- `action_plan_service.py` - Action planning

**Tests**: `tests/unit/services/analysis/test_*.py`
- ✅ Analysis workflows
- ✅ Prompt building
- ✅ Response parsing

#### 5.3 E2E Tests (`tests/e2e/analysis/`)
- Complete analysis flows
- Context enrichment integration
- LLM integration (test models)

### Acceptance Criteria
- [ ] All 7 analysis types implemented
- [ ] Context enrichment working
- [ ] Mock Step Functions for local dev
- [ ] 80%+ test coverage
- [ ] E2E tests passing

---

## Phase 6: LangGraph Workflow Migration

**Duration**: 2 weeks  
**GitHub Issue**: #18  
**Dependencies**: Phase 1-5

### Objectives
Refactor existing LangGraph workflows to use new architecture.

### Deliverables

#### 6.1 Workflow Refactoring (`coaching/src/workflows/`)
- Refactor `coaching_workflow.py` to use domain entities
- Refactor `analysis_workflow.py` to use analysis services
- Update workflow templates:
  - `conversation_workflow_template.py`
  - `analysis_workflow_template.py`
- Deprecate `orchestrator.py` if redundant

**Tests**: `tests/unit/workflows/test_*.py`
- ✅ Workflow state management
- ✅ Node transitions
- ✅ Error handling

#### 6.2 Workflow Templates (`coaching/src/workflows/templates/`)
- Create topic-specific workflows (if needed):
  - Core values, Purpose, Vision, Goals

**Tests**: `tests/e2e/workflows/test_*.py`
- ✅ Complete workflow execution
- ✅ State persistence

### Acceptance Criteria
- [ ] All workflows use new domain/services
- [ ] Workflow tests passing
- [ ] No breaking changes to API

---

## Phase 7: API Layer & Routes

**Duration**: 1-2 weeks  
**GitHub Issue**: #TBD (New)  
**Dependencies**: Phase 1-6

### Objectives
Complete API routes using new services and add comprehensive endpoint tests.

### Deliverables

#### 7.1 API Routes (`coaching/src/api/routes/`)
- Refactor `conversations.py` to use new conversation service
- Implement `alignment.py` - Alignment endpoints
- Implement `strategy.py` - Strategy endpoints
- Implement `kpi.py` - KPI endpoints
- Implement `operations.py` - SWOT, root cause, action plan
- Update `insights.py`
- Consolidate multi-tenant endpoints

**Tests**: `tests/integration/api/test_*.py`
- ✅ All endpoints
- ✅ Request validation
- ✅ Response formatting
- ✅ Error handling

#### 7.2 API Documentation
- Update OpenAPI schemas
- Add request/response examples
- Document error codes

### Acceptance Criteria
- [ ] All planned endpoints implemented
- [ ] API tests 90%+ coverage
- [ ] OpenAPI docs complete
- [ ] Multi-tenant consolidation done

---

## Phase 8: Production Readiness

**Duration**: 1-2 weeks  
**GitHub Issue**: #20 (updated)  
**Dependencies**: Phase 1-7

### Objectives
Production deployment preparation with full observability and infrastructure.

### Deliverables

#### 8.1 Observability Enhancement
- Complete CloudWatch integration
- AWS X-Ray tracing (replace stubs)
- Custom metrics dashboards
- Alert configuration

**Tests**: Observability validation
- ✅ Logs aggregated correctly
- ✅ Traces complete
- ✅ Metrics accurate

#### 8.2 Infrastructure (`infra/`)
- AWS SAM templates updated
- Step Functions state machines
- CloudFormation for observability
- Environment-specific configs

**Tests**: Infrastructure validation
- ✅ SAM build successful
- ✅ Local testing works
- ✅ Deployment succeeds

#### 8.3 CI/CD Pipeline (`.github/workflows/`)
- Automated testing on PR
- Type checking and linting gates
- Deployment pipelines (dev/staging/prod)
- Rollback procedures

#### 8.4 Performance & Load Testing
- Load tests with realistic scenarios
- Performance profiling
- Token cost optimization
- Caching strategy validation

**Tests**: Performance tests
- ✅ P95 latency < 2s
- ✅ 10k concurrent users
- ✅ Token costs within budget

#### 8.5 Documentation
- Deployment runbooks
- Troubleshooting guides
- ADRs for major decisions
- Migration guide from old code

### Acceptance Criteria
- [ ] All observability working in prod
- [ ] CI/CD pipelines operational
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Old code removed (if applicable)

---

## 🧪 Testing Strategy (Cross-Phase)

### Test Pyramid Adherence
- **70% Unit Tests** - Domain logic, services, utilities
- **20% Integration Tests** - Repositories, APIs, external clients
- **10% E2E Tests** - Complete user flows

### Quality Gates (Every Phase)
```bash
# Pre-commit checks
black src/ tests/
ruff check src/ tests/ --fix
mypy src/

# Test execution
pytest tests/ -v --cov=src --cov-report=html

# Coverage threshold
pytest --cov=src --cov-fail-under=75
```

### Test Data Management
- Use `factory_boy` for test data factories
- Pytest fixtures for common setups
- `httpx.mock` for external API mocking
- Automatic cleanup in teardown

---

## 🔄 Migration Strategy

### Backward Compatibility Approach

#### Stage 1: Parallel Implementation (Phases 1-4)
- New domain/infrastructure alongside existing code
- Adapters bridge old/new implementations
- Feature flags toggle between implementations

#### Stage 2: Gradual Migration (Phases 5-6)
- New features use only new architecture
- Old features refactored incrementally
- Deprecation warnings added

#### Stage 3: Consolidation (Phase 7-8)
- API layer fully migrated
- Old code marked deprecated
- Documentation updated

#### Stage 4: Cleanup (Post-Phase 8)
- Remove deprecated code
- Remove adapter layers
- Final optimization

### File Organization During Migration
```
coaching/src/
├── domain/          # ✅ New Clean Architecture
├── infrastructure/  # ✅ New Clean Architecture
├── services/        # 🔄 Gradually refactored
├── api/             # 🔄 Gradually refactored
├── models/          # ⚠️ Deprecated (adapters to domain)
├── adapters/        # 🆕 Bridge old/new during migration
└── legacy/          # ⚠️ Old code preserved until migration complete
```

---

## 📊 Success Metrics

### Phase Completion Criteria
Each phase must meet:
- ✅ All GitHub issues closed
- ✅ Test coverage targets met
- ✅ Type checking passes (mypy --strict)
- ✅ Linting passes (ruff)
- ✅ Documentation updated
- ✅ PR reviewed and approved

### Overall Project Metrics
- **Code Quality**: 85%+ test coverage, 0 critical vulnerabilities
- **Performance**: P95 < 2s API, P95 < 5s total
- **Reliability**: 99.9% uptime, < 0.1% error rate
- **Maintainability**: All `dict[str, Any]` replaced with types

---

## 📅 Timeline Summary

| Milestone | Target Date | Phases | Status |
|-----------|-------------|--------|--------|
| **Foundation Complete** | Week 3 | Phase 1-2 | 🟡 In Progress |
| **Infrastructure Ready** | Week 5 | Phase 3 | 🔲 Not Started |
| **Services Refactored** | Week 8 | Phase 4 | 🔲 Not Started |
| **Analysis Services Live** | Week 10 | Phase 5 | 🔲 Not Started |
| **Workflows Migrated** | Week 12 | Phase 6 | 🔲 Not Started |
| **API Complete** | Week 13 | Phase 7 | 🔲 Not Started |
| **Production Ready** | Week 15 | Phase 8 | 🔲 Not Started |

---

## 🎯 Next Actions

### Immediate (This Week)
1. **Close Issue #2** - Complete core type system
2. **Advance Issue #3** - Implement value objects
3. **Create new issues** for Phase 2, 7, 8
4. **Setup observability** foundation in Phase 1

### Short Term (Next 2 Weeks)
1. **Complete Phase 1** - All foundation components
2. **Start Phase 2** - Domain events/exceptions
3. **Begin Phase 3** - Infrastructure planning

### Medium Term (Weeks 3-8)
1. **Complete Phases 2-4** - Full architecture foundation
2. **Begin analysis services**
3. **Start workflow migration**

---

**Document Status**: ✅ Revised and Ready for Implementation  
**Maintained By**: Development Team  
**Review Frequency**: Bi-weekly  
**Last Reviewed**: October 9, 2025
