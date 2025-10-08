# PurposePath Frontend Integration Guide

**Document Date:** September 23, 2025  
**Version:** 1.0  
**Purpose:** Comprehensive technical documentation for all backend integration specifications

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Service Architecture](#service-architecture)
4. [Account Service Endpoints](#account-service-endpoints)
5. [Coaching Service Endpoints](#coaching-service-endpoints)
6. [Traction Service Endpoints](#traction-service-endpoints)
7. [SSE/WebSocket Integration Points](#ssewebsocket-integration-points)
8. [Data Models](#data-models)
9. [Request/Response Conventions](#requestresponse-conventions)
10. [Error Handling](#error-handling)
11. [Environment Configuration](#environment-configuration)

## Overview

The PurposePath frontend integrates with three microservices:

- **Account Service**: Authentication, user management, billing, onboarding
- **Coaching Service**: AI-powered business coaching, insights, conversations
- **Traction Service**: Goals, strategies, KPIs, activity tracking, reports

### Base URLs

- Account: `https://api.{env}.purposepath.app/account/api/v1/`
- Coaching: `https://api.{env}.purposepath.app/coaching/api/v1/`
- Traction: `https://api.{env}.purposepath.app/traction/api/v1/`

## Authentication & Authorization

### Headers

All protected endpoints require:

```http
Authorization: Bearer <accessToken>
X-Tenant-Id: <tenantId>
```

### Special Headers

- `X-Frontend-Base-Url: <window.location.origin>` - Used on Account auth endpoints for email link generation

### Token Management

- Access tokens stored in `localStorage` as `accessToken`
- Refresh tokens stored in `localStorage` as `refreshToken`
- Automatic refresh on 401 responses via `/auth/refresh`

## Service Architecture

### Account Service

Handles authentication, user profiles, subscription management, and business onboarding.

### Coaching Service

Provides AI-powered business insights, strategic coaching, and conversation management.

### Traction Service

Manages goals, strategies, KPIs, activity tracking, and reporting with real-time updates.

## Account Service Endpoints

### Authentication Endpoints

#### POST `/api/v1/auth/login`

**Purpose**: User authentication  

**Payload**:

```json
{
  "email": "string",
  "password": "string"
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "user": "UserProfile",
    "tenant": "TenantInfo"
  }
}
```

#### POST `/api/v1/auth/google`

**Purpose**: Google OAuth authentication  

**Payload**:

```json
{
  "token": "string"
}
```

**Response**: Same as login

#### POST `/api/v1/auth/register`

**Purpose**: User registration  

**Payload**:

```json
{
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string?"
}
```

**Response**: Either tokens+user or verification required

#### POST `/api/v1/auth/forgot-password`

**Purpose**: Password reset initiation  

**Payload**:

```json
{
  "email": "string"
}
```

#### POST `/api/v1/auth/reset-password`

**Purpose**: Password reset completion  

**Payload**:

```json
{
  "token": "string",
  "new_password": "string"
}
```

#### POST `/api/v1/auth/refresh`

**Purpose**: Token refresh  

**Payload**:

```json
{
  "refresh_token": "string"
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string"
  }
}
```

#### POST `/api/v1/auth/resend-confirmation`

**Purpose**: Resend email confirmation  
**Query**: `?email=<email>`  
**Headers**: `X-Frontend-Base-Url`

#### POST `/api/v1/auth/confirm-email`

**Purpose**: Email confirmation  

**Payload**:

```json
{
  "token": "string"
}
```

#### GET `/api/v1/auth/confirm-email/validate`

**Purpose**: Validate confirmation token  
**Query**: `?token=<token>`

#### POST `/api/v1/auth/logout`

**Purpose**: User logout  
**Query**: `?refresh_token=<token>`

### Profile & Account Management

#### GET `/api/v1/user/profile`

**Purpose**: Get user profile  

**Response**:

```json
{
  "success": true,
  "data": {
    "user_id": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "avatar_url": "string?",
    "created_at": "string",
    "updated_at": "string",
    "status": "string",
    "email_verified": "boolean",
    "preferences": "object"
  }
}
```

#### PUT `/api/v1/user/profile`

**Purpose**: Update user profile  

**Payload**:

```json
{
  "first_name": "string?",
  "last_name": "string?",
  "phone": "string?",
  "avatar_url": "string?",
  "preferences": "object?"
}
```

#### GET `/api/v1/user/features`

**Purpose**: Get enabled features for user  

**Response**:

```json
{
  "success": true,
  "data": ["string"]
}
```

#### GET `/api/v1/user/limits`

**Purpose**: Get user quotas and limits  

**Response**:

```json
{
  "success": true,
  "data": {
    "goals": "number?"
  }
}
```

### Subscription & Billing

#### PUT `/api/v1/user/subscription`

**Purpose**: Update subscription  

**Payload**:

```json
{
  "plan": "monthly|yearly?",
  "tier": "string?"
}
```

#### POST `/api/v1/billing/portal`

**Purpose**: Get billing portal URL  

**Payload**:

```json
{
  "return_url": "string?"
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "url": "string"
  }
}
```

### User Lookups

#### GET `/api/v1/users/{id}`

**Purpose**: Get user by ID (for owner display)  
**Response**: User information

### Onboarding

#### GET `/api/v1/onboarding`

**Purpose**: Get onboarding data

#### PUT `/api/v1/onboarding`

**Purpose**: Update onboarding data  

**Payload**:

```json
{
  "businessName": "string",
  "address": "OnboardingAddress",
  "products": "OnboardingProduct[]",
  "step3": "OnboardingStep3",
  "step4": "OnboardingStep4"
}
```

#### POST `/api/v1/onboarding/products`

**Purpose**: Create product  

**Payload**:

```json
{
  "name": "string",
  "problem": "string"
}
```

#### PUT `/api/v1/onboarding/products/{id}`

**Purpose**: Update product

#### DELETE `/api/v1/onboarding/products/{id}`

**Purpose**: Delete product

## Coaching Service Endpoints

### Business Insights

#### GET `/api/v1/multitenant/conversations/business-data`

**Purpose**: Get business metrics data  
**Response**: BusinessMetrics object (may be wrapped in data envelope)

#### GET `/api/v1/insights/`

**Purpose**: Get coaching insights  
**Response**: Paginated insights array

### AI Coaching

#### POST `/api/v1/suggestions/onboarding`

**Purpose**: Get AI suggestions for onboarding  

**Payload**:

```json
{
  "kind": "niche|ica|valueProposition",
  "current": "string?"
}
```

#### POST `/api/v1/coaching/onboarding`

**Purpose**: Get coaching for onboarding topics  

**Payload**:

```json
{
  "topic": "coreValues|purpose|vision",
  "message": "string"
}
```

### Conversations

#### POST `/api/v1/conversations/initiate`

**Purpose**: Start new conversation  

**Payload**:

```json
{
  "topic": "string"
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "id": "string"
  }
}
```

#### POST `/api/v1/conversations/{id}/message`

**Purpose**: Send message to conversation  

**Payload**:

```json
{
  "message": "string"
}
```

**Response**: Flexible format, normalized by frontend

## Traction Service Endpoints

### Goals Management

#### GET `/api/v1/goals`

**Purpose**: List goals with filtering  

**Query Parameters**:

- `page`: number
- `size`: number  
- `sort`: string
- `ownerId`: string
- `status`: GoalStatus
- `valueTag`: string
- `horizon`: string
- `search`: string

**Response**:

```json
{
  "success": true,
  "data": "Goal[]",
  "pagination": {
    "page": "number",
    "limit": "number", 
    "total": "number",
    "totalPages": "number"
  }
}
```

#### POST `/api/v1/goals`

**Purpose**: Create new goal  

**Payload**:

```json
{
  "title": "string",
  "owner_id": "string",
  "horizon": "string",
  "value_tags": "string[]?"
}
```

**Response**:

```json
{
  "success": true,
  "data": "Goal"
}
```

#### GET `/api/v1/goals/{id}`

**Purpose**: Get goal details  

**Response**:

```json
{
  "success": true,
  "data": "GoalDetail"
}
```

#### POST `/api/v1/goals/{id}:close`

**Purpose**: Close a goal  

**Payload**:

```json
{
  "reason": "string?"
}
```

### Goal Activity & Notes

#### GET `/api/v1/goals/{id}/activity`

**Purpose**: Get goal activity feed  

**Response**:

```json
{
  "success": true,
  "data": "ActivityItem[]"
}
```

#### POST `/api/v1/goals/{id}/activity`

**Purpose**: Create activity entry  

**Payload**:

```json
{
  "type": "ActivityType",
  "text": "string",
  "title": "string?",
  "url": "string?"
}
```

**Response**:

```json
{
  "success": true,
  "data": "ActivityItem"
}
```

#### POST `/api/v1/goals/{id}/notes`

**Purpose**: Add note to goal  

**Payload**:

```json
{
  "note": "string",
  "attachments": "any[]?"
}
```

### KPI Management

#### GET `/api/v1/kpis`

**Purpose**: List KPIs with filtering  

**Query Parameters**:

- `page`: number
- `size`: number
- `search`: string
- `category`: string
- `ownerId`: string

#### GET `/api/v1/kpis/{id}`

**Purpose**: Get KPI details  
**Response**: Either `{ success, data: KPI }` or `{ success, data: { kpi, readings } }`

#### GET `/api/v1/kpis/{id}/readings`

**Purpose**: Get KPI readings  

**Query Parameters**:

- `page`: number
- `size`: number

#### POST `/api/v1/kpis/{id}/readings`

**Purpose**: Create KPI reading  

**Payload**:

```json
{
  "period": "string",
  "adjustedValue": "number?",
  "reason": "string?"
}
```

### KPI-Goal Linkage

#### POST `/api/v1/goals/{goalId}/kpis:link`

**Purpose**: Link KPI to goal (bulk style)  

**Payload**:

```json
{
  "kpi_id": "string",
  "threshold_pct": "number?"
}
```

#### POST `/api/v1/goals/{goalId}/kpis:unlink`

**Purpose**: Unlink KPI from goal (bulk style)  

**Payload**:

```json
{
  "kpi_id": "string"
}
```

#### POST `/api/v1/goals/{goalId}/kpis/{kpiId}:setThreshold`

**Purpose**: Set KPI threshold for goal  

**Payload**:

```json
{
  "threshold_pct": "number?"
}
```

#### GET `/api/v1/goals/{goalId}/kpis/{kpiId}:link`

**Purpose**: Get KPI link details  

**Response**:

```json
{
  "success": true,
  "data": {
    "thresholdPct": "number?"
  }
}
```

### Reports

#### GET `/api/v1/reports/company`

**Purpose**: Generate company report  

**Query Parameters**:

- `format`: "pdf|docx"
- `from`: string (optional)
- `to`: string (optional)

**Response**: Binary blob (PDF/DOCX file)

## SSE/WebSocket Integration Points

### Goal Activity Stream

#### GET `/api/v1/realtime/goals/{goalId}/activity`

**Purpose**: Real-time goal activity updates  
**Protocol**: Server-Sent Events (SSE)  

**Query Parameters**:

- `access_token`: JWT token for authentication
- `tenant`: Tenant ID
- `lastEventId`: Last received event ID (optional)

**Event Types**:

- `activity.created`: New activity item added
- `decision.created`: New decision recorded
- `attachment.created`: New attachment added
- `kpi.reading.created`: New KPI reading added

**Event Data Format**:

```json
{
  "type": "activity.created|decision.created|attachment.created|kpi.reading.created",
  "goalId": "string",
  "activity": {
    "id": "string",
    "text": "string", 
    "createdAt": "string",
    "title": "string?",
    "url": "string?"
  }
}
```

### Tenant-Wide Stream (Future)

#### GET `/api/v1/realtime/tenants/{tenantId}`

**Purpose**: Tenant-wide real-time updates  
**Protocol**: Server-Sent Events (SSE)  
**Status**: Defined in OpenAPI, not yet used by frontend

## Data Models

### Core User Types

#### User

```typescript
interface User {
  id: string;
  email: string;
  fullName: string;
  phone?: string;
  profileImage?: string;
  createdAt: string;
  updatedAt: string;
  isActive: boolean;
  emailVerified: boolean;
  phoneVerified: boolean;
}
```

#### UserProfile

```typescript
interface UserProfile extends User {
  preferences: UserPreferences;
  subscription: SubscriptionInfo;
}
```

#### UserPreferences

```typescript
interface UserPreferences {
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
    marketing: boolean;
  };
  timezone: string;
  language: string;
  theme: 'light' | 'dark' | 'auto';
}
```

### Authentication Types

#### LoginRequest

```typescript
interface LoginRequest {
  email: string;
  password: string;
}
```

#### RegisterRequest

```typescript
interface RegisterRequest {
  email: string;
  password: string;
  fullName: string;
  phone?: string;
}
```

#### AuthResponse

```typescript
interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: UserProfile;
}
```

### Strategic Planning Types

#### Goal

```typescript
interface Goal {
  id: string;
  intent: string;
  status: GoalStatus;
  ownerId: string;
  alignmentScore: number;
  alignmentExplanation: string;
  alignmentSuggestions: string[];
  strategies: Strategy[];
  kpis: GoalKPI[];
  createdAt: Date;
  updatedAt: Date;
}
```

#### Strategy

```typescript
interface Strategy {
  id: string;
  goalId: string;
  description: string;
  order: number;
  aiGenerated: boolean;
  validationScore?: number;
  validationFeedback?: string;
  status: StrategyStatus;
  createdAt: Date;
  updatedAt: Date;
}
```

#### SharedKPI

```typescript
interface SharedKPI {
  id: string;
  kpiId: string;
  name: string;
  unit: string;
  direction: KPIDirection;
  timeHorizons: TimeHorizon[];
  attachedGoalIds: string[];
  createdAt: Date;
  updatedAt: Date;
}
```

#### TimeHorizon

```typescript
interface TimeHorizon {
  id: string;
  type: TimeHorizonType;
  period: string;
  startValue: number;
  targetValue: number;
  currentValue?: number;
  currentValueDate?: Date;
  actualEndValue?: number;
  actualEndDate?: Date;
  progressUpdates: KPIProgressUpdate[];
  subHorizons: TimeHorizon[];
  parentHorizonId?: string;
  inheritedFromParent: boolean;
  propagatedToNext: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

### Activity Types

#### ActivityItem

```typescript
interface ActivityItem {
  id: string;
  goalId: string;
  type: ActivityType;
  title?: string;
  text: string;
  createdAt: string;
  authorId?: string;
  payload?: Record<string, any>;
}
```

#### ActivityType

```typescript
type ActivityType = 'weekly_review' | 'note' | 'system' | 'decision' | 'attachment';
```

### Business Foundation Types

#### BusinessFoundation

```typescript
interface BusinessFoundation {
  businessName: string;
  vision: string;
  purpose: string;
  coreValues: string[];
  targetMarket: string;
  valueProposition: string;
  address?: OnboardingAddress;
  products?: OnboardingProduct[];
  niche?: string;
  ica?: string;
}
```

#### OnboardingAddress

```typescript
interface OnboardingAddress {
  street: string;
  city: string;
  state: string;
  zip: string;
  country: string;
}
```

#### OnboardingProduct

```typescript
interface OnboardingProduct {
  id: string;
  name: string;
  problem: string;
}
```

### Coaching Types

#### BusinessMetrics

```typescript
interface BusinessMetrics {
  revenue: number;
  profitMargin: number;
  customerCount: number;
  employeeCount: number;
  marketShare: number;
  growthRate: number;
}
```

#### CoachingInsight

```typescript
interface CoachingInsight {
  id: string;
  title: string;
  description: string;
  category: 'strategy' | 'operations' | 'finance' | 'marketing' | 'leadership';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'in_progress' | 'completed';
  createdAt: string;
  updatedAt: string;
}
```

### Operations Types

#### Action

```typescript
interface Action {
  id: string;
  title: string;
  description: string;
  dateEntered: Date;
  startDate: Date;
  dueDate: Date;
  priority: ActionPriority;
  assignedPersonId: string;
  progress: number;
  status: ActionStatus;
  syncStatus?: 'synced' | 'pending' | 'error';
  connections: {
    goalIds: string[];
    strategyIds: string[];
    issueIds: string[];
  };
  kpiUpdates?: ActionKPIUpdate[];
  createdAt: Date;
  updatedAt: Date;
}
```

#### Issue

```typescript
interface Issue {
  id: string;
  title: string;
  description: string;
  dateReported: Date;
  reportedBy: string;
  businessImpact: IssueImpact;
  priority: number;
  status: IssueStatus;
  rootCauseAnalysis?: RootCauseAnalysis;
  relatedActionIds: string[];
  createdAt: Date;
  updatedAt: Date;
  resolvedAt?: Date;
}
```

### Subscription Types

#### SubscriptionInfo

```typescript
interface SubscriptionInfo {
  id: string;
  userId: string;
  plan: 'monthly' | 'yearly';
  status: 'active' | 'inactive' | 'cancelled' | 'past_due' | 'trialing';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  price: number;
  currency: string;
  paymentMethod?: PaymentMethod;
}
```

### Response Envelope Types

#### ApiResponse

```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}
```

#### PaginatedResponse

```typescript
interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

## Request/Response Conventions

### Request Format

- **Content-Type**: `application/json`
- **Field Casing**: snake_case for request payloads
- **Query Parameters**: snake_case
- **Path Parameters**: camelCase

### Response Format

- **Envelope**: `{ success: boolean, data?: T, error?: string }`
- **Field Casing**: Backend may return snake_case; frontend maps to camelCase
- **Dates**: ISO 8601 format strings
- **Pagination**: Consistent pagination object structure

### Casing Strategy

- **Requests**: Use snake_case (e.g., `new_password`, `refresh_token`, `owner_id`)
- **Responses**: Backend returns snake_case; frontend normalizes to camelCase where needed
- **OpenAPI**: snake_case in schemas with camelCase mapping in frontend

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes

- **200**: Success (with success flag in body)
- **401**: Unauthorized (triggers token refresh)
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **500**: Internal Server Error

### Frontend Error Handling

- Automatic token refresh on 401 responses
- Graceful degradation for unavailable services
- User-friendly error messages
- Retry logic for transient failures

## Environment Configuration

### Required Environment Variables

#### Frontend (.env)

```bash
# Service Base URLs
REACT_APP_ACCOUNT_API_URL=https://api.dev.purposepath.app/account/api/v1
REACT_APP_COACHING_API_URL=https://api.dev.purposepath.app/coaching/api/v1  
REACT_APP_TRACTION_API_URL=https://api.dev.purposepath.app/traction/api/v1

# Feature Flags
REACT_APP_MOCK_MODE=false
REACT_APP_MOCK_TRACTION=false
REACT_APP_FEATURE_REALTIME=true

# SSE Configuration
REACT_APP_SSE_BASE_URL=https://api.dev.purposepath.app/traction/api/v1
```

### Environment-Specific URLs

- **Development**: `api.dev.purposepath.app`
- **Staging**: `api.staging.purposepath.app`
- **Production**: `api.purposepath.app`

### Mock Mode

When `REACT_APP_MOCK_MODE=true` or service URLs are not configured:

- API calls return mock data
- No real network requests made
- Suitable for development and testing

---

*This document serves as the canonical reference for all frontend-backend integration points in the PurposePath application. For questions or updates, consult the development team.*
