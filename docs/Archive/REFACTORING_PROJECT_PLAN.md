# 🚀 PurposePath Coaching Service Refactoring Project Plan

## 📋 Project Overview

**Objective**: Refactor the coaching service to implement clean microservices architecture with proper data boundaries and integration patterns.

**Duration**: 4-6 weeks (estimated)

**Team**: AI Development Team + .NET API Team (coordination)

---

## 🎯 Big Picture Vision

### Current State Analysis
- **Python Coaching Service**: Monolithic approach trying to own business data
- **Schema Synchronization Problem**: Complex and error-prone to maintain
- **Tight Coupling**: Coaching service depends on business database schema
- **Testing Challenges**: Difficult to test in isolation

### Target State Vision
- **Clean Microservices**: Each service owns its domain completely
- **API-First Integration**: Services communicate via well-defined contracts
- **Flexible Data Access**: Choose integration pattern based on use case
- **Independent Deployment**: Services evolve separately without breaking changes

---

## 🗺️ Architecture Transformation

### Before (Current):
```
┌─────────────────┐    ┌─────────────────┐
│  Coaching API   │    │   .NET API      │
│                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Conversations│ │    │ │   Users     │ │
│ │   Table     │ │    │ │   Table     │ │
│ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Business Data│ │◄──►│ │   Goals     │ │ Schema
│ │   Table     │ │    │ │   Table     │ │ Sync
│ └─────────────┘ │    │ └─────────────┘ │ Issues
└─────────────────┘    └─────────────────┘
```

### After (Target):
```
┌─────────────────┐    ┌─────────────────┐
│  Coaching API   │    │   .NET API      │
│                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Conversations│ │    │ │   Users     │ │
│ │   Table     │ │    │ │   Table     │ │
│ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │ ┌─►│ ┌─────────────┐ │
│ │  Sessions   │ │ │  │ │Business Data│ │
│ │   Table     │ │ │  │ │   Table     │ │
│ └─────────────┘ │ │  │ └─────────────┘ │
└─────────────────┘ │  └─────────────────┘
         │          │
         │          │ API Calls
    ┌────▼──────────▼─────┐
    │  Step Functions     │
    │   Orchestrator      │
    └─────────────────────┘
```

---

## 📅 Project Phases

### **Phase 1: Foundation & Planning** (Week 1)
**Goal**: Establish proper development framework and planning

**Deliverables**:
- ✅ Updated development instructions
- ✅ Git branching strategy implemented
- ✅ GitHub issues workflow established
- ✅ Project plan and architecture vision documented
- 📋 GitHub issues created for all phases

**Acceptance Criteria**:
- All team members trained on new workflow
- Development environment properly configured
- All future work tracked via GitHub issues

---

### **Phase 2: API Contracts & Models** (Week 2)
**Goal**: Define clean data contracts and remove tight coupling

**Tasks**:
1. Create Pydantic models for business context integration
2. Design API contracts for coaching service
3. Remove direct business-data table dependencies
4. Update CloudFormation templates

**Deliverables**:
- `BusinessContext` Pydantic models
- `CoachingRequest/Response` contracts
- Updated `template.yaml` (remove business-data table)
- API specification documentation

**Acceptance Criteria**:
- All models use Pydantic (no `dict[str, Any]`)
- Comprehensive test coverage for models
- API contracts documented and validated
- No lint/type errors

---

### **Phase 3: .NET Integration Layer** (Week 3)
**Goal**: Build business data API in .NET service

**Tasks** (Coordination with .NET team):
1. Create business context API endpoint
2. Implement data aggregation logic
3. Add authentication and authorization
4. Performance optimization and caching

**Deliverables**:
- `GET /api/v1/business-context` endpoint
- Business data aggregation service
- API documentation and examples
- Performance benchmarks

**Acceptance Criteria**:
- API endpoint functional and tested
- Sub-200ms response time for lightweight requests
- Proper error handling and logging
- Authentication integrated

---

### **Phase 4: Step Functions Orchestrator** (Week 4)
**Goal**: Implement orchestration for complex coaching scenarios

**Tasks**:
1. Deploy Step Functions state machine
2. Implement error handling and fallbacks
3. Add monitoring and logging
4. Integration testing

**Deliverables**:
- Step Functions definition deployed
- Monitoring dashboard
- Integration test suite
- Error handling documentation

**Acceptance Criteria**:
- Orchestrator handles all error scenarios
- End-to-end integration tests pass
- Performance metrics within targets
- Proper logging and monitoring

---

### **Phase 5: Coaching Service Refactoring** (Week 5)
**Goal**: Update coaching service to use new integration patterns

**Tasks**:
1. Refactor API endpoints to accept business context
2. Implement dual integration patterns (payload + orchestrated)
3. Remove direct database access to business tables
4. Update AI prompting with business context

**Deliverables**:
- Refactored coaching API endpoints
- Business context integration logic
- Updated AI prompting system
- Migration guide

**Acceptance Criteria**:
- All endpoints support both integration patterns
- AI responses use business context effectively
- No direct business database access remaining
- Comprehensive test coverage

---

### **Phase 6: Testing & Validation** (Week 6)
**Goal**: Comprehensive testing and production readiness

**Tasks**:
1. End-to-end integration testing
2. Performance testing and optimization
3. Security validation
4. Documentation completion

**Deliverables**:
- Complete test suite (unit + integration)
- Performance test results
- Security audit results
- Production deployment guide

**Acceptance Criteria**:
- 95%+ test coverage
- All performance targets met
- Security requirements satisfied
- Production deployment successful

---

## 🔄 Integration Patterns

### Pattern A: Frontend Payload
```typescript
// Use for: Quick coaching, known context, real-time chat
const request = {
  message: "Help with goal prioritization",
  business_context: {
    user: { name: "John", role: "CEO" },
    goals: [{ id: "1", title: "Revenue Growth" }]
  }
}
```

### Pattern B: Step Functions Orchestration  
```bash
# Use for: Strategic analysis, complex insights, comprehensive coaching
Frontend → Step Functions → .NET API → Coaching API → Response
```

---

## 📊 Success Metrics

### Technical Metrics
- **Test Coverage**: >95% for all new code
- **Response Time**: <200ms for lightweight requests, <2s for orchestrated
- **Error Rate**: <1% for all API calls
- **Type Safety**: 100% Pydantic models (no dict[str, Any])

### Business Metrics
- **Development Velocity**: 50% faster feature delivery
- **Bug Reduction**: 80% fewer integration-related bugs
- **Deployment Frequency**: Independent service deployments
- **Maintainability**: Clear ownership and boundaries

---

## 🚨 Risk Mitigation

### Technical Risks
- **API Latency**: Implement caching and optimize queries
- **Service Dependencies**: Build comprehensive error handling and fallbacks
- **Data Consistency**: Use proper transaction patterns and validation

### Process Risks
- **Coordination**: Regular sync meetings with .NET team
- **Testing**: Comprehensive integration test suites
- **Rollback**: Maintain backward compatibility during migration

---

## 🛠️ Tools & Infrastructure

### Development Tools
- **Version Control**: Git with feature branch workflow
- **Issue Tracking**: GitHub Issues with proper labels
- **Testing**: pytest with coverage reporting
- **Code Quality**: black, ruff, mypy

### Infrastructure
- **Cloud Platform**: AWS (Lambda, Step Functions, DynamoDB)
- **Monitoring**: CloudWatch, AWS X-Ray
- **CI/CD**: GitHub Actions
- **Documentation**: Markdown in repository

---

## 👥 Team Responsibilities

### AI Development Team
- Coaching service refactoring
- API contract implementation
- Step Functions orchestrator
- Testing and validation

### .NET API Team
- Business context API endpoint
- Data aggregation optimization
- Authentication integration
- Performance tuning

### DevOps/Platform Team
- Infrastructure deployment
- Monitoring setup
- CI/CD pipeline configuration
- Security validation

---

## 📈 Progress Tracking

### Weekly Milestones
- **Week 1**: Foundation complete, issues created
- **Week 2**: API contracts and models implemented
- **Week 3**: .NET integration ready
- **Week 4**: Step Functions deployed and tested
- **Week 5**: Coaching service refactored
- **Week 6**: Production ready and deployed

### Quality Gates
Each phase requires:
- ✅ All tests passing
- ✅ Code review completed
- ✅ Documentation updated
- ✅ GitHub issues closed
- ✅ No lint/type errors

---

**Next Steps**: Create GitHub issues for each phase and begin Phase 2 execution.