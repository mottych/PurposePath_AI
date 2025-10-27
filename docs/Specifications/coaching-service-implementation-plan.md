# Coaching Service Implementation Plan

**Created:** October 27, 2025  
**Status:** Planning Phase  
**Priority:** High

---

## Executive Summary

This document outlines the comprehensive plan to align the Coaching Service implementation with the specification, fix URL routing issues, and implement missing endpoints. The work has been organized into 5 GitHub issues (#61-#65) that address all identified gaps.

## URL Structure Clarification

### Current Understanding
- **API Gateway:** `https://api.dev.purposepath.app`
- **Service Base URL:** `https://api.dev.purposepath.app/coaching/api/v1`
- **FastAPI `api_prefix`:** `/api/v1`

### Correct Routing Pattern
Since the base URL already includes `/coaching/api/v1`, endpoints should be defined as:
- ✅ Router prefix: `/coaching` → Full URL: `/coaching/api/v1/coaching/...`
- ✅ Router prefix: `/operations` → Full URL: `/coaching/api/v1/operations/...`
- ✅ Router prefix: `/insights` → Full URL: `/coaching/api/v1/insights/...`

## Implementation Phases

### Phase 1: Infrastructure & Routing (Issue #61)
**Priority:** Critical  
**Estimated Effort:** 4-6 hours  
**Dependencies:** None

#### Tasks
1. **Include Missing Routers in main.py**
   - Add `insights.router` with prefix `/insights`
   - Add `onboarding.router` (routes already have full paths)
   - Add `multitenant_conversations.router` with prefix `/multitenant/conversations`

2. **Clean Up Duplicate/Obsolete Files**
   - Archive `suggestions.py` (duplicate of onboarding.py)
   - Archive `website.py` (duplicate of onboarding.py)
   - Archive `coaching.py` (stub implementations only)

3. **Verification**
   - Test all endpoints appear in `/docs` Swagger UI
   - Verify no 404 errors on endpoint calls
   - Update integration tests

**Acceptance Criteria:**
- [ ] All 6 routers registered in main.py
- [ ] Duplicate files removed
- [ ] All endpoints accessible via Swagger
- [ ] No broken imports or circular dependencies

---

### Phase 2: Strategic Planning AI Endpoints (Issue #62)
**Priority:** High  
**Estimated Effort:** 16-20 hours  
**Dependencies:** Phase 1

#### Tasks
1. **Create New Coaching Router**
   - File: `coaching/src/api/routes/coaching_ai.py`
   - Prefix: `/coaching`
   - Move existing alignment logic from `analysis.py`

2. **Implement Missing Endpoints**
   - `POST /coaching/alignment-explanation` - Detailed AI explanation
   - `POST /coaching/alignment-suggestions` - Improvement suggestions
   - Enhance existing `POST /coaching/alignment-check`

3. **Service Layer Enhancements**
   - Add `get_detailed_explanation()` to AlignmentAnalysisService
   - Add `get_improvement_suggestions()` to AlignmentAnalysisService
   - Implement LLM prompts for rich, contextual responses

4. **Testing**
   - Unit tests for new service methods
   - Integration tests for endpoints
   - Test various goal/foundation combinations

**Acceptance Criteria:**
- [ ] Three alignment endpoints fully functional
- [ ] LLM integration provides quality responses
- [ ] Response times < 3 seconds
- [ ] Test coverage > 80%

**Endpoints Created:**
- `POST /coaching/alignment-check`
- `POST /coaching/alignment-explanation`
- `POST /coaching/alignment-suggestions`
- `POST /coaching/strategy-suggestions`
- `POST /coaching/kpi-recommendations`

---

### Phase 3: Operations AI - Strategic Alignment (Issue #63)
**Priority:** Medium  
**Estimated Effort:** 20-24 hours  
**Dependencies:** Phase 1

#### Tasks
1. **Create Operations AI Router**
   - File: `coaching/src/api/routes/operations_ai.py`
   - Prefix: `/operations`

2. **Implement Three New Endpoints**
   - `POST /operations/strategic-alignment` - Action-goal alignment analysis
   - `POST /operations/prioritization-suggestions` - AI priority optimization
   - `POST /operations/scheduling-suggestions` - Schedule optimization

3. **Create Service Layer**
   - File: `coaching/src/application/analysis/operations_ai_service.py`
   - Methods: `analyze_strategic_alignment()`, `suggest_prioritization()`, `optimize_scheduling()`

4. **Create Request/Response Models**
   - File: `coaching/src/api/models/operations.py`
   - All Pydantic models per specification

5. **LLM Integration**
   - Prompts for alignment scoring
   - Prompts for priority recommendations
   - Prompts for scheduling optimization

**Acceptance Criteria:**
- [ ] All three endpoints operational
- [ ] Service layer provides business logic
- [ ] LLM integration tested
- [ ] Response times < 5 seconds
- [ ] Test coverage > 80%

**Endpoints Created:**
- `POST /operations/strategic-alignment`
- `POST /operations/prioritization-suggestions`
- `POST /operations/scheduling-suggestions`

---

### Phase 4: Operations Analysis Refactoring (Issue #64)
**Priority:** Medium  
**Estimated Effort:** 12-16 hours  
**Dependencies:** Phase 3

#### Tasks
1. **Refactor Generic Operations Endpoint**
   - Keep SWOT in `POST /analysis/operations`
   - Extract root_cause to specialized endpoint
   - Extract action_plan to specialized endpoint

2. **Create Specialized Endpoints**
   - `POST /operations/root-cause-suggestions` - Enhanced with multiple methods
   - `POST /operations/action-suggestions` - Rich action plans

3. **Enhance Service Layer**
   - Add `suggest_root_cause_methods()` to OperationsAnalysisService
   - Add `generate_action_plan()` to OperationsAnalysisService
   - Pre-populate Five Whys questions
   - Generate SWOT elements specific to issues

4. **Migration Strategy**
   - Create new endpoints alongside old
   - Mark generic endpoint as deprecated
   - Provide frontend migration guide

**Acceptance Criteria:**
- [ ] Specialized endpoints created
- [ ] Rich AI-powered responses
- [ ] Backward compatibility maintained
- [ ] Migration guide documented

**Endpoints Created:**
- `POST /operations/root-cause-suggestions`
- `POST /operations/action-suggestions`

---

### Phase 5: Business Data Integration (Issue #65)
**Priority:** Medium  
**Estimated Effort:** 16-20 hours  
**Dependencies:** Phase 1

#### Tasks
1. **Register Multitenant Conversations Router**
   - Include in main.py (currently missing)
   - Endpoint: `GET /multitenant/conversations/business-data`

2. **Create Business Data Service**
   - File: `coaching/src/services/business_data_service.py`
   - Integrate with Account Service API
   - Integrate with Traction Service API

3. **Implement Data Aggregation**
   - Revenue data from Account/Billing
   - Customer data from Account Service
   - Operations data from Traction Service (goals, actions, issues)
   - Team data from Account Service

4. **Add Caching**
   - Redis-based caching (5-minute TTL)
   - Cache key: `business_data:{tenant_id}`
   - Handle cache misses gracefully

5. **Error Handling**
   - Handle service unavailability
   - Partial data fallbacks
   - Comprehensive logging

**Acceptance Criteria:**
- [ ] Endpoint accessible at correct URL
- [ ] Real data from Account/Traction services
- [ ] Caching implemented (5-min TTL)
- [ ] Graceful error handling
- [ ] Test coverage > 80%

**Endpoints Updated:**
- `GET /multitenant/conversations/business-data`

---

## GitHub Issues Created

| Issue # | Title | Priority | Estimated Effort |
|---------|-------|----------|------------------|
| [#61](https://github.com/mottych/PurposePath_AI/issues/61) | Include Missing Routers in Main Application | High | 4-6 hours |
| [#62](https://github.com/mottych/PurposePath_AI/issues/62) | Implement Missing Strategic Planning AI Endpoints | High | 16-20 hours |
| [#63](https://github.com/mottych/PurposePath_AI/issues/63) | Implement Operations AI Endpoints | Medium | 20-24 hours |
| [#64](https://github.com/mottych/PurposePath_AI/issues/64) | Refactor Operations Analysis Endpoints | Medium | 12-16 hours |
| [#65](https://github.com/mottych/PurposePath_AI/issues/65) | Update Business Data Endpoint | Medium | 16-20 hours |

**Total Estimated Effort:** 68-86 hours (approximately 2-3 weeks for one developer)

---

## Documentation Updates

### Specification Document Updated
- **File:** `docs/Specifications/backend-integration-coaching-service.md`
- **Version:** Updated to 3.1
- **Changes:**
  - Added URL structure clarification section
  - Updated all endpoint URLs to relative paths
  - Added "Full URL" notes for clarity
  - Documented that base URL includes `/coaching/api/v1`

### Frontend Impact
The frontend team should be notified that:
1. Base URL configuration is correct
2. All endpoints are relative to base URL
3. No changes needed to existing API client configuration
4. New endpoints will be available as implementation progresses

---

## Testing Strategy

### Unit Tests
- Service layer methods (all new business logic)
- LLM prompt quality and response parsing
- Data aggregation logic
- Caching mechanisms

### Integration Tests
- All new endpoints end-to-end
- Service-to-service communication (Account, Traction)
- Error scenarios (service unavailable, timeouts)
- Authentication/authorization flows

### Performance Tests
- LLM response times (target < 5 seconds)
- Concurrent request handling
- Cache hit/miss ratios
- API Gateway timeout resilience

---

## Deployment Plan

### Stage 1: Development
- Implement and test locally
- Use mock data for external services
- Verify all Swagger documentation

### Stage 2: Dev Environment
- Deploy to dev environment
- Test with real Account/Traction services
- Verify API Gateway routing
- Monitor CloudWatch logs

### Stage 3: Staging
- Full integration testing
- Load testing with realistic data
- Frontend integration verification
- Security review

### Stage 4: Production
- Blue-green deployment
- Gradual rollout (feature flags)
- Monitor error rates and latencies
- Rollback plan ready

---

## Risk Mitigation

### Technical Risks
1. **LLM Response Times**
   - Risk: AI calls may exceed timeout limits
   - Mitigation: Implement async processing for long-running requests, add caching

2. **Service Dependencies**
   - Risk: Account/Traction service unavailability
   - Mitigation: Implement circuit breakers, graceful degradation, cached fallbacks

3. **Breaking Changes**
   - Risk: URL changes may break existing integrations
   - Mitigation: Maintain backward compatibility, deprecation warnings, migration guides

### Process Risks
1. **Scope Creep**
   - Risk: Additional requirements discovered during implementation
   - Mitigation: Stick to specification, document new requirements for future phases

2. **Timeline Slippage**
   - Risk: Estimates may be optimistic
   - Mitigation: Implement in priority order, allow for 20% buffer time

---

## Success Metrics

### Code Quality
- [ ] All new code has >80% test coverage
- [ ] No critical or high-severity linting errors
- [ ] MyPy type checking passes
- [ ] All security scans pass

### Functionality
- [ ] All 16+ endpoints operational
- [ ] Swagger UI documentation complete
- [ ] Frontend integration successful
- [ ] No regressions in existing functionality

### Performance
- [ ] API response times within SLA (95th percentile < 5s)
- [ ] Cache hit ratio > 70% for business data
- [ ] Zero 5xx errors in production (first week)
- [ ] Successful load test at 100 RPS

---

## Next Steps

1. **Immediate (Week 1)**
   - Start with Issue #61 (Infrastructure & Routing)
   - Set up development environment
   - Create feature branch: `feature/coaching-service-alignment`

2. **Short-term (Weeks 2-3)**
   - Implement Issue #62 (Strategic Planning AI)
   - Implement Issue #63 (Operations AI)
   - Continuous testing and documentation

3. **Medium-term (Week 4)**
   - Implement Issue #64 (Operations Refactoring)
   - Implement Issue #65 (Business Data)
   - Integration testing with frontend

4. **Final (Week 5)**
   - Code review and refinement
   - Deployment to dev environment
   - Frontend team handoff and support

---

## Questions for Stakeholders

1. Should we maintain backward compatibility for the generic `/analysis/operations` endpoint?
2. What is the priority order if timeline is compressed?
3. Are there any existing frontend integrations that need special consideration?
4. What are the SLAs for LLM response times?
5. Do we need feature flags for gradual rollout?

---

**Document Maintained By:** Development Team  
**Last Updated:** October 27, 2025  
**Next Review:** Upon completion of Phase 1
