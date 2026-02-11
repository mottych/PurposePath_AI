# PurposePath Admin Portal - API Endpoints Index

## Overview

This document provides a comprehensive index of all API endpoints used by the PurposePath Admin Portal. The portal integrates with two main API services:

- **Main Admin API**: `https://api.dev.purposepath.app/admin/api/v1`
- **Coaching/AI API**: `https://api.dev.purposepath.app/coaching/api/v1/admin`

## Authentication & Authorization

### Google OAuth Endpoints (External)

- `GET https://accounts.google.com/o/oauth2/v2/auth` - Initiate OAuth flow
- `POST https://oauth2.googleapis.com/token` - Exchange code for tokens / Refresh tokens
- `GET https://www.googleapis.com/oauth2/v2/userinfo` - Get user info from Google

### Admin Validation

- `POST /auth/validate` - Validate admin user and Portal Admins group membership

## Main Admin API Endpoints

### User Management

- `GET /admin/users` - Get paginated list of users with filters
- `GET /admin/users/{userId}` - Get detailed user information with activity history
- `POST /admin/users/{userId}/unlock` - Unlock user account (reset failed login attempts)
- `POST /admin/users/{userId}/suspend` - Suspend user account
- `POST /admin/users/{userId}/reactivate` - Reactivate suspended user account

### Subscriber Management

- `GET /admin/subscribers` - Get paginated list of subscribers with filters
- `GET /admin/subscribers/{tenantId}` - Get detailed subscriber information

### Subscription Operations

- `POST /subscriptions/{tenantId}/extend-trial` - Extend trial period for a tenant
- `POST /subscriptions/{tenantId}/apply-discount` - Apply discount to subscription
- `POST /subscriptions/{tenantId}/extend-billing` - Extend billing period
- `POST /subscriptions/{tenantId}/grant-feature` - Grant ad-hoc feature to tenant
- `POST /subscriptions/{tenantId}/designate-test` - Designate tenant as test account
- `GET /subscriptions/{tenantId}/audit-log` - Get subscription audit log

### Discount Code Management

- `GET /admin/discount-codes` - Get paginated list of discount codes
- `GET /admin/discount-codes/{id}` - Get discount code by ID
- `GET /admin/discount-codes/{id}/usage` - Get discount code usage history
- `POST /admin/discount-codes` - Create new discount code
- `PATCH /admin/discount-codes/{id}` - Update existing discount code
- `POST /admin/discount-codes/{id}/enable` - Enable discount code
- `POST /admin/discount-codes/{id}/disable` - Disable discount code
- `DELETE /admin/discount-codes/{id}` - Delete discount code
- `POST /admin/discount-codes/validate` - Validate discount code

### Plan/Tier Management

- `GET /admin/plans` - Get paginated list of plans
- `GET /admin/plans/{id}` - Get plan by ID
- `POST /admin/plans` - Create new plan
- `PATCH /admin/plans/{id}` - Update existing plan
- `POST /admin/plans/{id}/deactivate` - Deactivate plan
- `POST /admin/plans/{id}/validate` - Validate plan updates
- `GET /admin/plans/{id}/affected-subscribers` - Get affected subscribers for plan changes
- `DELETE /admin/plans/{id}` - Delete plan (only if no subscribers)

### System Settings

- `GET /admin/settings` - Get all settings with optional filtering
- `GET /admin/settings/{key}` - Get specific setting by key
- `PATCH /admin/settings/{key}` - Update setting value
- `POST /admin/settings/{key}/validate` - Validate setting value
- `POST /admin/settings/{key}/reset` - Reset setting to default value

### Email Template Management

- `GET /admin/email-templates` - Get all email templates
- `GET /admin/email-templates/{key}` - Get email template by key
- `PUT /admin/email-templates/{key}` - Update email template
- ~~`POST /admin/email-templates/validate`~~ - **DEPRECATED** - Validation now done client-side with RazorLight utilities (Issue #7)
- ~~`POST /admin/email-templates/{key}/preview`~~ - **DEPRECATED** - Preview now generated client-side with RazorLight (Issue #7)

**Note**: As of Issue #7 implementation, template validation and preview are performed client-side using RazorLight validation utilities and variable replacement. The deprecated endpoints remain available for backward compatibility but are not actively used by the admin portal.

### Feature Management

- `GET /admin/features` - Get all available features
- `GET /admin/features/tiers` - Get all subscription tiers for feature matrix
- `PUT /admin/features/tiers/{tierId}` - Update features for specific tier
- `POST /admin/features/tiers/{tierId}/validate` - Validate tier feature updates
- `GET /admin/features/tenants/{tenantId}/grants` - Get tenant-specific feature grants
- `POST /admin/features/tenants/{tenantId}/grants` - Add feature grant to tenant
- `DELETE /admin/features/tenants/{tenantId}/grants/{feature}` - Remove feature grant from tenant
- `GET /admin/features/tenants/{tenantId}/effective` - Get effective features for tenant

### AI Model & Prompt Management

- `GET /admin/ai/models` - Get all AI models
- `GET /admin/ai/prompts` - Get all prompt templates
- `GET /admin/ai/prompts/{id}` - Get prompt template by ID
- `POST /admin/ai/prompts` - Create new prompt template
- `PUT /admin/ai/prompts/{id}` - Update prompt template
- `DELETE /admin/ai/prompts/{id}` - Delete prompt template
- `POST /admin/ai/prompts/{id}/test` - Test prompt with sample data
- `PATCH /admin/ai/prompts/{id}/activate` - Set prompt version as active
- `GET /admin/ai/prompts/{id}/versions` - Get all versions of prompt template

### Audit Logging

- `GET /admin/audit-logs` - Get audit logs with filters and pagination
- `GET /admin/audit-logs/{id}` - Get specific audit log entry
- `GET /admin/audit-logs/export` - Export audit logs to CSV
- `GET /admin/audit-logs/action-types` - Get available action types for filtering

### LLM (Language Model Management)

#### Interactions

- `GET /admin/llm/interactions` - Get paginated list of LLM interactions with filters
- `GET /admin/llm/interactions/{code}` - Get detailed interaction information by code

#### Models

- `GET /admin/llm/models` - Get all available LLM models
- `GET /admin/llm/models/{code}` - Get specific LLM model details by code

#### Templates

- `GET /admin/llm/templates` - Get all prompt templates
- `GET /admin/llm/templates/{topic}/versions` - Get all versions of a prompt template
- `GET /admin/llm/templates/{topic}/versions/{version}` - Get specific template version details
- `GET /admin/llm/templates/{topic}/latest` - Get latest version of a template
- `POST /admin/llm/templates/{topic}/versions/{version}/set-latest` - Set a version as the latest
- `POST /admin/llm/templates/{topic}/versions/{version}/test` - Test a template version with sample data
- `GET /admin/llm/templates/{topic}/versions/{version}/parameters` - Get template parameters
- `POST /admin/llm/templates/{topic}/versions/{version}/validate-compatibility` - Validate template compatibility

#### Configurations

- `GET /admin/llm/configurations` - Get all LLM configurations
- `GET /admin/llm/configurations/{id}` - Get specific configuration details
- `POST /admin/llm/configurations/{id}/activate` - Activate a configuration
- `POST /admin/llm/configurations/{id}/deactivate` - Deactivate a configuration
- `POST /admin/llm/configurations/validate` - Validate configuration data
- `POST /admin/llm/configurations/bulk-deactivate` - Bulk deactivate configurations
- `GET /admin/llm/configurations/{id}/dependencies` - Get configuration dependencies

#### Dashboard

- `GET /admin/llm/dashboard/metrics` - Get LLM usage metrics
- `GET /admin/llm/dashboard/trends` - Get usage trends over time
- `GET /admin/llm/dashboard/health` - Get system health status
- `POST /admin/llm/dashboard/validate-system` - Validate system configuration
- `GET /admin/llm/dashboard/quick-stats` - Get quick statistics summary
- `GET /admin/llm/dashboard/activity` - Get recent activity feed

## Coaching/AI API Endpoints

Currently, the AI API client (`aiApiClient`) is configured to use the coaching API base URL (`https://api.dev.purposepath.app/coaching/api/v1/admin`), but based on the codebase analysis, all AI-related endpoints are actually using the main API client and the `/admin/ai/*` paths on the main API.

The coaching API client appears to be set up for future use but is not currently utilized in the codebase.

## HTTP Methods Summary

- **GET**: Data retrieval, listing, filtering
- **POST**: Creating new resources, triggering actions, validation
- **PUT**: Full resource updates (email templates, prompt templates)
- **PATCH**: Partial resource updates (discount codes, plans, settings, prompt activation)
- **DELETE**: Resource deletion

## Authentication Headers

All requests to protected endpoints require:

- `Authorization: Bearer {access_token}` - JWT access token from Google OAuth
- `X-CSRF-Token: {csrf_token}` - CSRF protection for state-changing operations (POST, PUT, PATCH, DELETE)

## Common Query Parameters

- `page` - Page number for pagination (default: 1)
- `pageSize` - Items per page (default: 50, options: 25, 50, 100, 200)
- `search` - Text search filter
- `status` - Status-based filtering
- Various entity-specific filters per endpoint

## Error Handling

All endpoints return standardized error responses with appropriate HTTP status codes:

- `400` - Bad Request
- `401` - Unauthorized (triggers token refresh)
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Validation Error
- `500+` - Server Errors

## Rate Limiting & Retry Logic

- Request timeout: 30 seconds
- Automatic retry with exponential backoff (max 3 retries)
- Token refresh handling for expired access tokens
- CSRF token management for state-changing operations
