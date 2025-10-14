# All GitHub Issues - Copy-Paste Templates

Delete all existing issues, then create these 14 issues in order.

---

## Issue #1: Phase 1.1 - Core Type System

**Title**: Phase 1.1: Implement Core Type System, Constants & Observability Foundation

**Labels**: enhancement, critical-priority, phase-1, foundation

**Body**:
```markdown
## 🎯 Objective
Implement foundational type system with domain IDs, enums, constants, and observability foundation.

## 📦 Deliverables
1. **Core Type System** (`coaching/src/core/types.py`)
   - Domain IDs: ConversationId, TemplateId, AnalysisRequestId, UserId, TenantId
   - Factory functions for ID creation

2. **Enhanced Constants** (`coaching/src/core/constants.py`)
   - Enums: CoachingTopic, AnalysisType, ConversationStatus, ConversationPhase, MessageRole
   - Business rules: PHASE_PROGRESS_WEIGHTS, PHASE_REQUIREMENTS, DEFAULT_LLM_MODELS

3. **Observability Foundation** (`coaching/src/infrastructure/observability/`)
   - logger.py - Structured logging with structlog
   - metrics.py - Custom metrics collection
   - tracer.py - AWS X-Ray integration stubs

## 🧪 Testing
- Unit tests (70%+ coverage)
- Type safety validation
- PII redaction tests

## ✅ Acceptance Criteria
- [ ] All domain IDs use NewType
- [ ] Structured logging working
- [ ] 70%+ test coverage
- [ ] Mypy strict passes

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 1.1

## ⏱️ Duration
3-4 days
```

---

## Issue #2: Phase 1.2 - Domain Value Objects

**Title**: Phase 1.2: Implement Domain Value Objects

**Labels**: enhancement, high-priority, phase-1, domain-layer

**Body**:
```markdown
## 🎯 Objective
Implement immutable domain value objects (Message, AlignmentScore, EnrichedContext, etc.).

## 📦 Deliverables
1. Message (`message.py`)
2. Conversation Context (`conversation_context.py`)
3. Alignment Score (`alignment_score.py`)
4. Strategy Recommendation (`strategy_recommendation.py`)
5. Enriched Context (`enriched_context.py`)

## 🧪 Testing
- Unit tests (80%+ coverage)
- Immutability enforcement
- Validation rules

## ✅ Acceptance Criteria
- [ ] All value objects immutable (frozen=True)
- [ ] Complete validation rules
- [ ] 80%+ test coverage
- [ ] Mypy strict passes

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 1.2

## 🔗 Dependencies
- Depends on: #1

## ⏱️ Duration
4-5 days
```

---

## Issue #3: Phase 1.3 - Domain Entities

**Title**: Phase 1.3: Implement Domain Entities (Aggregate Roots)

**Labels**: enhancement, high-priority, phase-1, domain-layer

**Body**:
```markdown
## 🎯 Objective
Implement domain entities as aggregate roots with business rules (Conversation, PromptTemplate, AnalysisRequest).

## 📦 Deliverables
1. **Conversation Entity** (`conversation.py`)
   - Business rules enforcement
   - Domain events emission
   - Phase transitions
   - TTL management

2. **Prompt Template Entity** (`prompt_template.py`)
   - Version management
   - Publication rules

3. **Analysis Request** (`analysis_request.py`)

## 🧪 Testing
- Unit tests (80%+ coverage)
- Aggregate invariants
- Business rule enforcement
- Domain events

## ✅ Acceptance Criteria
- [ ] Conversation enforces all business rules
- [ ] Domain events emitted correctly
- [ ] 80%+ test coverage
- [ ] Mypy strict passes

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 1.3
- docs/Guides/clean-architecture-ddd-guidelines.md

## 🔗 Dependencies
- Depends on: #1, #2

## ⏱️ Duration
5-6 days
```

---

## Issue #4: Phase 1.4 - Domain Services

**Title**: Phase 1.4: Implement Domain Services

**Labels**: enhancement, high-priority, phase-1, domain-layer

**Body**:
```markdown
## 🎯 Objective
Implement domain services for complex business logic (AlignmentCalculator, PhaseTransitionService, CompletionValidator).

## 📦 Deliverables
1. **Alignment Calculator** (`alignment_calculator.py`)
   - Score calculation algorithm
   - Weighted component scoring

2. **Phase Transition Service** (`phase_transition_service.py`)
   - Transition validation
   - Progress calculation

3. **Completion Validator** (`completion_validator.py`)
   - Completion readiness checks
   - Requirements validation

## 🧪 Testing
- Unit tests (85%+ coverage)
- Business logic correctness
- Edge cases

## ✅ Acceptance Criteria
- [ ] All services stateless
- [ ] No infrastructure dependencies
- [ ] 85%+ test coverage
- [ ] Mypy strict passes

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 1.4

## 🔗 Dependencies
- Depends on: #1, #2, #3
- Completes Phase 1

## ⏱️ Duration
4-5 days
```

---

## Issue #5: Phase 2 - Domain Events and Exceptions

**Title**: Phase 2: Implement Domain Events and Exceptions

**Labels**: enhancement, high-priority, phase-2, domain-layer

**Body**:
```markdown
## 🎯 Objective
Implement domain events for observability and domain-specific exceptions.

## 📦 Deliverables
1. **Domain Events** (`coaching/src/domain/events/`)
   - Base event class with correlation IDs
   - Conversation events (Initiated, MessageAdded, Completed, etc.)
   - Analysis events (Requested, Completed, Failed)

2. **Domain Exceptions** (`coaching/src/domain/exceptions/`)
   - Conversation exceptions (NotFound, InvalidTransition, NotActive)
   - Analysis exceptions (InvalidRequest, EnrichmentFailed)

## 🧪 Testing
- Unit tests (80%+ coverage)
- Event serialization
- Exception hierarchy

## ✅ Acceptance Criteria
- [ ] All events inherit from DomainEvent
- [ ] Events include correlation IDs
- [ ] Exceptions are specific and actionable
- [ ] 80%+ test coverage

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 2

## 🔗 Dependencies
- Depends on: Phase 1 complete (#1-4)

## ⏱️ Duration
1 week
```

---

## Issue #6: Phase 3.1 - Repository and Service Ports

**Title**: Phase 3.1: Define Repository and Service Port Interfaces

**Labels**: enhancement, high-priority, phase-3, infrastructure

**Body**:
```markdown
## 🎯 Objective
Define port interfaces (protocols) for repositories and external services.

## 📦 Deliverables
1. **Repository Ports** (`coaching/src/domain/ports/`)
   - ConversationRepositoryPort
   - PromptRepositoryPort
   - InsightsRepositoryPort

2. **Service Ports**
   - LLMProviderPort
   - EnrichmentServicePort
   - CacheServicePort

## 🧪 Testing
- Protocol type checking
- Method signature validation

## ✅ Acceptance Criteria
- [ ] All ports use typing.Protocol
- [ ] Complete type hints
- [ ] No implementation details
- [ ] Mypy strict passes

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 3.1

## 🔗 Dependencies
- Depends on: Phase 1-2 complete

## ⏱️ Duration
2-3 days
```

---

## Issue #7: Phase 3.2 - Infrastructure Adapters

**Title**: Phase 3.2: Implement Infrastructure Adapters

**Labels**: enhancement, high-priority, phase-3, infrastructure

**Body**:
```markdown
## 🎯 Objective
Implement adapters for repositories, LLM providers, external clients, and caching.

## 📦 Deliverables
1. **Repository Implementations**
   - Refactor conversation_repository.py (DynamoDB)
   - Refactor prompt_repository.py (S3)
   - insights_repository.py

2. **Cache Implementations** (NEW - consolidates old #10)
   - redis_cache.py (production)
   - in_memory_cache.py (testing)

3. **LLM Provider Abstraction**
   - BaseProvider, BedrockProvider, AnthropicProvider
   - LLMProviderManager (factory)

4. **External Service Clients**
   - Step Functions client
   - Business API client
   - Circuit breakers and retries

## 🧪 Testing
- Integration tests (70%+ coverage)
- DynamoDB operations
- LLM provider integration
- Circuit breaker tests

## ✅ Acceptance Criteria
- [ ] All repositories implement ports
- [ ] LLM providers interchangeable
- [ ] External clients have circuit breakers
- [ ] 70%+ integration test coverage

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 3.2

## 🔗 Dependencies
- Depends on: #6 (ports)

## ⏱️ Duration
2 weeks
```

---

## Issue #8: Phase 4 - Application Services

**Title**: Phase 4: Implement Application Services Layer

**Labels**: enhancement, high-priority, phase-4, service-layer

**Body**:
```markdown
## 🎯 Objective
Refactor and implement service layer using new domain and infrastructure components.

## 📦 Deliverables
1. **Conversation Services**
   - Refactor conversation_service.py
   - conversation_flow_service.py
   - conversation_memory_service.py

2. **LLM Services**
   - Refactor llm_service.py
   - response_parser_service.py

3. **Prompt Services** (NEW - consolidates old #14)
   - prompt_service.py (refactored)
   - prompt_builder_service.py
   - Context injection logic

4. **Insights Services**
   - insights_service.py (refactored)

## 🧪 Testing
- Unit + Integration tests
- Service orchestration
- Dependency injection
- Error handling

## ✅ Acceptance Criteria
- [ ] All services use new domain/infrastructure
- [ ] Multi-tenant logic consolidated
- [ ] 80%+ test coverage
- [ ] Mypy strict passes

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 4

## 🔗 Dependencies
- Depends on: Phase 1-3 complete

## ⏱️ Duration
2-3 weeks
```

---

## Issue #9: Phase 5.1 - Analysis Services

**Title**: Phase 5.1: Implement Analysis Services (Alignment, Strategy, KPI)

**Labels**: enhancement, high-priority, phase-5, analysis

**Body**:
```markdown
## 🎯 Objective
Implement one-shot analysis services for alignment scoring, strategy recommendations, KPI suggestions, SWOT, root cause, and action planning.

## 📦 Deliverables
1. **Analysis Services** (`coaching/src/services/analysis/`)
   - alignment_service.py - Alignment scoring, explanation, suggestions
   - strategy_service.py - Strategy recommendations
   - kpi_service.py - KPI recommendations
   - swot_service.py - SWOT analysis
   - root_cause_service.py - Root cause and five whys
   - action_plan_service.py - Action planning

## 🧪 Testing
- Unit tests (80%+ coverage)
- Analysis workflows
- Prompt building
- Response parsing

## ✅ Acceptance Criteria
- [ ] All 6+ analysis types implemented
- [ ] Structured outputs
- [ ] 80%+ test coverage
- [ ] E2E tests passing

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 5.1

## 🔗 Dependencies
- Depends on: Phase 1-4 complete

## ⏱️ Duration
1-1.5 weeks
```

---

## Issue #10: Phase 5.2 - Context Enrichment Services

**Title**: Phase 5.2: Implement Context Enrichment Services

**Labels**: enhancement, high-priority, phase-5, integration

**Body**:
```markdown
## 🎯 Objective
Implement business context enrichment via Step Functions and .NET Business API integration.

## 📦 Deliverables
1. **Enrichment Service** (`coaching/src/services/enrichment/`)
   - enrichment_orchestrator.py - Main orchestrator
   - business_foundation_enricher.py
   - goal_context_enricher.py
   - operations_context_enricher.py

2. **Step Functions Integration**
   - State machine definitions
   - Lambda task handlers
   - Error handling

3. **Mock Implementation**
   - Local development mocks
   - Testing infrastructure

## 🧪 Testing
- Integration tests
- Step Functions mocking
- Context assembly tests

## ✅ Acceptance Criteria
- [ ] Context enrichment working
- [ ] Mock Step Functions for local dev
- [ ] 80%+ test coverage
- [ ] E2E tests passing

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 5.2

## 🔗 Dependencies
- Depends on: #9, Phase 1-4

## ⏱️ Duration
1 week
```

---

## Issue #11: Phase 6 - LangGraph Workflows

**Title**: Phase 6: Refactor and Extend LangGraph Workflows

**Labels**: enhancement, medium-priority, phase-6, workflows

**Body**:
```markdown
## 🎯 Objective
Refactor existing LangGraph workflows to use new architecture.

## 📦 Deliverables
1. **Workflow Refactoring** (`coaching/src/workflows/`)
   - Refactor coaching_workflow.py
   - Refactor analysis_workflow.py
   - Update conversation_workflow_template.py
   - Update analysis_workflow_template.py

2. **Topic-Specific Workflows**
   - Core values, Purpose, Vision, Goals workflows

## 🧪 Testing
- Workflow state management tests
- Node transition tests
- E2E workflow tests

## ✅ Acceptance Criteria
- [ ] All workflows use new domain/services
- [ ] Workflow tests passing
- [ ] No breaking changes to API
- [ ] State persistence working

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 6

## 🔗 Dependencies
- Depends on: Phase 1-5 complete

## ⏱️ Duration
2 weeks
```

---

## Issue #12: Phase 7 - API Layer and Routes

**Title**: Phase 7: Implement Complete API Layer and Routes

**Labels**: enhancement, high-priority, phase-7, api-layer

**Body**:
```markdown
## 🎯 Objective
Complete API routes using new services and add comprehensive endpoint tests. Consolidates API routes and middleware.

## 📦 Deliverables
1. **API Routes** (`coaching/src/api/routes/`) - (consolidates old #16)
   - Refactor conversations.py
   - alignment.py - Alignment endpoints
   - strategy.py - Strategy endpoints
   - kpi.py - KPI endpoints
   - operations.py - SWOT, root cause, action plan
   - insights.py (update)
   - Consolidate multi-tenant endpoints

2. **API Middleware** - (consolidates old #17)
   - Logging middleware
   - Authentication middleware
   - Error handling middleware
   - Rate limiting middleware
   - CORS configuration

3. **API Documentation**
   - OpenAPI schemas
   - Request/response examples
   - Error codes documentation

## 🧪 Testing
- API tests (90%+ coverage)
- All endpoints tested
- Request validation
- Response formatting
- Error handling

## ✅ Acceptance Criteria
- [ ] All planned endpoints implemented
- [ ] Middleware fully functional
- [ ] API tests 90%+ coverage
- [ ] OpenAPI docs complete
- [ ] Multi-tenant consolidation done

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 7

## 🔗 Dependencies
- Depends on: Phase 1-6 complete

## ⏱️ Duration
1-2 weeks
```

---

## Issue #13: Phase 8 - Production Readiness

**Title**: Phase 8: Production Readiness (Infrastructure, CI/CD, Observability)

**Labels**: enhancement, critical-priority, phase-8, deployment, infrastructure

**Body**:
```markdown
## 🎯 Objective
Production deployment preparation with full observability and infrastructure.

## 📦 Deliverables
1. **Observability Enhancement**
   - CloudWatch integration
   - AWS X-Ray tracing (replace stubs)
   - Custom metrics dashboards
   - Alert configuration

2. **Infrastructure** (`infra/`)
   - AWS SAM templates updated
   - Step Functions state machines
   - CloudFormation for observability
   - Environment-specific configs

3. **CI/CD Pipeline** (`.github/workflows/`)
   - Automated testing on PR
   - Type checking and linting gates
   - Deployment pipelines (dev/staging/prod)
   - Rollback procedures

4. **Performance & Load Testing**
   - Load tests
   - Performance profiling
   - Token cost optimization
   - Caching strategy validation

5. **Documentation**
   - Deployment runbooks
   - Troubleshooting guides
   - ADRs
   - Migration guide

## 🧪 Testing
- Observability validation
- Infrastructure validation
- Performance tests (P95 < 2s)
- Load tests (10k concurrent users)

## ✅ Acceptance Criteria
- [ ] All observability working in prod
- [ ] CI/CD pipelines operational
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Old code removed

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Phase 8

## 🔗 Dependencies
- Depends on: Phase 1-7 complete

## ⏱️ Duration
1-2 weeks
```

---

## Issue #14: Testing Strategy (Cross-Cutting)

**Title**: Testing Strategy: Comprehensive Coverage Across All Phases

**Labels**: enhancement, critical-priority, testing, cross-cutting

**Body**:
```markdown
## 🎯 Objective
Comprehensive testing strategy integrated across all phases (not a separate phase).

## 📦 Deliverables
1. **Test Infrastructure**
   - Pytest configuration
   - Test data factories (factory_boy)
   - Fixtures and mocking utilities
   - Coverage configuration

2. **Test Pyramid Implementation**
   - 70% Unit Tests
   - 20% Integration Tests
   - 10% E2E Tests

3. **Quality Gates**
   - Pre-commit hooks (black, ruff, mypy)
   - Coverage thresholds (75%+)
   - Type checking enforcement
   - Automated test runs

4. **Testing Documentation**
   - Testing guidelines
   - Mocking patterns
   - Test data management
   - Coverage reports

## 🧪 Test Types
- Unit tests for all domain/service logic
- Integration tests for repositories/APIs
- E2E tests for complete user flows
- Performance tests for optimization

## ✅ Acceptance Criteria
- [ ] Test infrastructure set up
- [ ] Pre-commit hooks configured
- [ ] 75%+ coverage across codebase
- [ ] All quality gates passing
- [ ] CI/CD integration complete

## 📚 References
- docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md - Testing Strategy

## 🔗 Dependencies
- Applies to all phases

## ⏱️ Duration
Ongoing (integrated into each phase)
```

---

## 🎯 Summary

After deleting all issues, create these 14 in order:
1. Phase 1.1 - Core Types & Observability
2. Phase 1.2 - Value Objects
3. Phase 1.3 - Entities
4. Phase 1.4 - Domain Services
5. Phase 2 - Events & Exceptions
6. Phase 3.1 - Ports
7. Phase 3.2 - Adapters (includes caching)
8. Phase 4 - Application Services (includes prompts)
9. Phase 5.1 - Analysis Services
10. Phase 5.2 - Context Enrichment
11. Phase 6 - LangGraph Workflows
12. Phase 7 - API Layer (includes middleware)
13. Phase 8 - Production Readiness
14. Testing Strategy (cross-cutting)

**Key Consolidations**:
- Old #10 (Caching) → Now part of #7 (Phase 3.2)
- Old #14 (Prompts) → Now part of #8 (Phase 4)
- Old #16 + #17 (API Routes + Middleware) → Now #12 (Phase 7)
- Old #19 (Testing Phase 6) → Now #14 (Cross-cutting)
