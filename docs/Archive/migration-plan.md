# PurposePath Migration Plan: Python to C# Backend

## Executive Summary

This document outlines the comprehensive migration strategy from the current Python-based microservices to a hybrid architecture where:
- **Python services remain**: Coaching Service (AI/ML functionality with LangChain/LangGraph)
- **C# services replace**: Account Service and Traction Service (business logic, data management)
- **Shared infrastructure**: DynamoDB database, AWS Lambda/Serverless deployment

## Current Architecture Analysis

Based on the frontend integration guide analysis, we have identified three main services:

### 1. Account Service (🔄 MIGRATE TO C#)
**Current Python Implementation Location**: `/account/`
**Responsibilities**:
- Authentication & Authorization (JWT tokens)
- User Management & Profile
- Tenant Management (Multi-tenancy)
- Subscription & Billing (Stripe integration)
- Onboarding flow management

**Migration Priority**: **HIGH** - Core business logic with no AI dependencies

### 2. Coaching Service (✅ KEEP PYTHON)
**Current Location**: `/coaching/`
**Responsibilities**:
- AI-powered business insights
- LangChain/LangGraph conversations
- Strategic coaching recommendations
- Business metrics analysis

**Migration Decision**: **REMAIN PYTHON** - Heavy AI/ML dependencies, LangChain integration

### 3. Traction Service (🔄 MIGRATE TO C#)
**Current Python Implementation Location**: `/traction/`
**Responsibilities**:
- Goals & Strategy Management
- KPI tracking and reporting
- Real-time activity feeds (SSE)
- Company report generation

**Migration Priority**: **HIGH** - Complex business logic, better suited for C# DDD patterns

## Domain Model Analysis

### Core Domains Identified from Frontend Guide

#### 1. **Identity & Access Management Domain**
**Entities**:
- User (with UserProfile, UserPreferences)
- Tenant/Organization
- Authentication tokens
- Authorization permissions

**Value Objects**:
- Email, UserId, TenantId
- AuthTokens (AccessToken, RefreshToken)
- UserPreferences, NotificationSettings

#### 2. **Subscription & Billing Domain**
**Entities**:
- Subscription
- PaymentMethod
- BillingCycle

**Value Objects**:
- SubscriptionId, Money, BillingPeriod
- SubscriptionStatus, SubscriptionTier

#### 3. **Strategic Planning Domain**
**Entities**:
- Goal (with GoalDetail)
- Strategy
- KPI (SharedKPI with TimeHorizon)
- ActivityItem

**Value Objects**:
- GoalId, StrategyId, KPIId
- GoalStatus, StrategyStatus, KPIDirection
- TimeHorizonType, ActivityType

#### 4. **Business Foundation Domain**
**Entities**:
- BusinessFoundation
- OnboardingProduct
- BusinessAddress

**Value Objects**:
- BusinessName, Vision, Purpose
- CoreValues, TargetMarket, ValueProposition

#### 5. **Operations Domain**
**Entities**:
- Action
- Issue
- Report

**Value Objects**:
- ActionId, IssueId, Priority
- ActionStatus, IssueStatus

## Migration Phases

### Phase 1: Foundation & Account Service (Sprint 1-3)

#### Sprint 1: Core Domain Setup
**Deliverables**:
1. **Identity & Access Management Domain**
   - User aggregate with proper DDD patterns
   - Authentication/Authorization value objects
   - Repository interfaces (no implementations yet)

2. **Subscription Domain**
   - Subscription aggregate
   - Billing value objects
   - Stripe integration interfaces

**GitHub Issues**:
- Setup C# solution architecture with Clean Architecture layers
- Implement User aggregate with strong typing
- Create Authentication domain services
- Design Subscription domain model

#### Sprint 2: Infrastructure Layer
**Deliverables**:
1. **Repository Implementations**
   - DynamoDB User repository
   - DynamoDB Subscription repository
   - Data model mapping (Domain ↔ Persistence)

2. **External Service Integration**
   - Stripe payment processing
   - AWS Cognito integration (if needed)
   - Email service integration

**GitHub Issues**:
- Implement DynamoDB repositories with proper mapping
- Create Stripe service integration
- Setup AWS Lambda deployment pipeline
- Configure environment-specific settings

#### Sprint 3: Application Services & API Layer
**Deliverables**:
1. **Application Services**
   - UserService, AuthenticationService
   - SubscriptionService, BillingService
   - CQRS pattern implementation

2. **API Controllers**
   - Authentication endpoints
   - User profile management
   - Subscription management
   - Onboarding flow

**GitHub Issues**:
- Implement authentication flow (login, register, refresh)
- Create user profile management endpoints
- Build subscription management API
- Setup API documentation (OpenAPI/Swagger)

### Phase 2: Traction Service Migration (Sprint 4-6)

#### Sprint 4: Strategic Planning Domain
**Deliverables**:
1. **Goal Management Domain**
   - Goal aggregate with strategies
   - KPI management with time horizons
   - Goal-KPI relationship modeling

2. **Activity Tracking Domain**
   - Activity feed implementation
   - Real-time event sourcing
   - Decision and attachment tracking

**GitHub Issues**:
- Design Goal aggregate with complex business rules
- Implement KPI tracking with time-based projections
- Create activity feed domain model
- Setup event sourcing infrastructure

#### Sprint 5: Operations Domain
**Deliverables**:
1. **Action Management**
   - Action planning and tracking
   - Progress monitoring
   - Cross-domain relationships (Goal ↔ Action)

2. **Issue Management**
   - Issue tracking and resolution
   - Root cause analysis
   - Impact assessment

**GitHub Issues**:
- Implement Action aggregate with complex workflows
- Create Issue tracking system
- Build cross-domain relationship management
- Setup progress tracking mechanisms

#### Sprint 6: Reporting & Real-time Features
**Deliverables**:
1. **Report Generation**
   - Company report compilation
   - PDF/DOCX generation
   - Data aggregation services

2. **Real-time Features**
   - SSE implementation for activity feeds
   - WebSocket infrastructure
   - Event-driven updates

**GitHub Issues**:
- Build report generation system
- Implement Server-Sent Events for real-time updates
- Create data aggregation services
- Setup event-driven architecture

### Phase 3: Integration & Optimization (Sprint 7-8)

#### Sprint 7: Python-C# Integration
**Deliverables**:
1. **Service Communication**
   - Inter-service communication patterns
   - Shared data contracts
   - Event-driven integration

2. **Data Consistency**
   - Cross-service transactions
   - Eventual consistency patterns
   - Conflict resolution strategies

**GitHub Issues**:
- Setup inter-service communication
- Implement shared event bus
- Create data synchronization mechanisms
- Build integration testing suite

#### Sprint 8: Performance & Production Readiness
**Deliverables**:
1. **Performance Optimization**
   - Database query optimization
   - Caching strategies
   - Connection pooling

2. **Production Setup**
   - CI/CD pipeline completion
   - Monitoring and logging
   - Security hardening

**GitHub Issues**:
- Optimize database performance
- Setup comprehensive monitoring
- Complete security audit
- Finalize deployment automation

## Domain Model Separation Strategy

### Current Issues (Python → C# Improvements)

1. **Dictionary Usage Elimination**
   - Current: Extensive use of `dict` types
   - Target: Strong typing with value objects and DTOs

2. **Persistence Model Confusion**
   - Current: Mixed domain/persistence concerns
   - Target: Clear separation between domain and data models

3. **Business Logic Scattering**
   - Current: Business rules in services and repositories
   - Target: Business rules in domain entities only

### C# Domain Model Design Principles

#### 1. **Pure Domain Layer**
```csharp
// ✅ Pure domain logic - no external dependencies
public class User : BaseEntity
{
    public UserId Id { get; private set; }
    public Email Email { get; private set; }
    public TenantId TenantId { get; private set; }
    
    public void ActivateAccount()
    {
        // Business rule: Can't activate deleted users
        if (Status == UserStatus.Deleted)
            throw new DomainException("Cannot activate deleted user");
            
        Status = UserStatus.Active;
        AddDomainEvent(new UserActivatedEvent(Id));
    }
}
```

#### 2. **Separate Persistence Models**
```csharp
// Domain Model (rich behavior)
public class Subscription : BaseEntity { ... }

// Data Model (persistence only)
public class SubscriptionDataModel
{
    [DynamoDBHashKey]
    public string Id { get; set; }
    
    [DynamoDBRangeKey]
    public string TenantId { get; set; }
    
    public string Status { get; set; }
    // ... other persistence-specific attributes
}
```

#### 3. **Strong Value Objects**
```csharp
// Instead of: Dictionary<string, object> or primitive obsession
public record Money(decimal Amount, string Currency)
{
    public static Money Zero(string currency) => new(0, currency);
    public Money Add(Money other) => 
        Currency == other.Currency 
            ? new(Amount + other.Amount, Currency)
            : throw new InvalidOperationException("Currency mismatch");
}
```

## API Alignment Strategy

### Frontend Integration Compatibility

Based on the frontend integration guide, we need to maintain exact API compatibility:

#### 1. **Request/Response Formats**
- **Maintain**: `{ success: boolean, data?: T, error?: string }` envelope
- **Preserve**: snake_case in request payloads
- **Convert**: Backend can return snake_case, frontend maps to camelCase

#### 2. **Endpoint Preservation**
All existing endpoints must remain functional during migration:
- Authentication: `/api/v1/auth/*`
- User Management: `/api/v1/user/*`
- Goals: `/api/v1/goals/*`
- KPIs: `/api/v1/kpis/*`
- Real-time: `/api/v1/realtime/*`

#### 3. **Data Model Mapping**
```csharp
// API Response DTOs match frontend expectations exactly
public record UserResponse(
    string user_id,        // snake_case for API compatibility
    string email,
    string first_name,
    string last_name,
    string status,
    bool email_verified,
    DateTime created_at,
    DateTime? updated_at
);

// Internal domain uses proper C# conventions
public class User : BaseEntity
{
    public UserId Id { get; private set; }          // Strong typing
    public Email Email { get; private set; }        // Value object
    public string FirstName { get; private set; }   // PascalCase
    // ...
}
```

## Technical Architecture Decisions

### 1. **Database Strategy**
- **Shared DynamoDB**: Single database accessed by both Python and C# services
- **Table Design**: Maintain existing table structure during migration
- **Consistency**: Use DynamoDB transactions for cross-service operations

### 2. **Deployment Architecture**
- **C# Services**: AWS Lambda with .NET 9 runtime
- **Python Services**: Keep existing Lambda deployment
- **API Gateway**: Route requests based on service responsibility
- **Shared Resources**: DynamoDB, S3, SES, Stripe webhooks

### 3. **Inter-Service Communication**
- **Synchronous**: Direct HTTP calls for immediate operations
- **Asynchronous**: SQS/SNS for event-driven updates
- **Shared Events**: Domain events published to shared event bus

### 4. **Security Model**
- **JWT Tokens**: Generated by C# Account Service
- **Shared Authentication**: Python services validate C# tokens
- **Tenant Isolation**: Multi-tenant security at database level

## Migration Risks & Mitigation

### High Risk Items
1. **Data Migration Complexity**
   - **Risk**: Complex DynamoDB data transformation
   - **Mitigation**: Blue-green deployment with data validation

2. **Real-time Feature Compatibility**
   - **Risk**: SSE implementation differences
   - **Mitigation**: Maintain exact event format compatibility

3. **Performance Regression**
   - **Risk**: C# cold start times vs Python
   - **Mitigation**: Proper Lambda optimization, keep-warm strategies

### Medium Risk Items
1. **Inter-service Dependencies**
   - **Mitigation**: Circuit breaker patterns, graceful degradation

2. **Complex Business Logic Migration**
   - **Mitigation**: Extensive unit testing, behavior-driven testing

## Success Metrics

### Technical Metrics
- **Performance**: <500ms API response times maintained
- **Reliability**: 99.9% uptime during migration
- **Code Quality**: >90% test coverage for domain logic

### Business Metrics
- **Zero Downtime**: No user-facing service interruptions
- **Feature Parity**: 100% API compatibility maintained
- **Data Integrity**: Zero data loss during migration

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|------------|
| Phase 1 | 6 weeks | Account Service (C#) |
| Phase 2 | 6 weeks | Traction Service (C#) |
| Phase 3 | 4 weeks | Integration & Production |
| **Total** | **16 weeks** | **Complete Migration** |

## Next Steps

1. ✅ Create comprehensive DDD guidelines (COMPLETED)
2. 🔄 **Create detailed GitHub issues for each sprint**
3. 🔄 **Setup C# solution with proper DDD structure**
4. 🔄 **Validate domain layer dependencies**
5. 🔄 **Begin Phase 1 implementation**

This migration plan ensures a systematic, risk-mitigated transition to a hybrid architecture that leverages the strengths of both Python (AI/ML) and C# (enterprise business logic) while maintaining zero downtime and full API compatibility.