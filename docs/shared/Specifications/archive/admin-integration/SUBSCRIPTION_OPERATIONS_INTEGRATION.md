# Subscription Operations Service Integration Guide

## Service Overview

- **Service Name**: Subscription Operations Service
- **Base URL**: `{config.apiBaseUrl}/subscriptions`
- **Primary File**: `src/services/subscriptionService.ts`
- **Hook File**: `src/hooks/useSubscriptions.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Extend Trial Period

```http
Method: POST
URL: /subscriptions/{tenantId}/extend-trial
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  tenantId: string;  // Tenant ID
}
```

**Request Body:**

```typescript
interface TrialExtensionRequest {
  newTrialEndDate: string;  // ISO date string (must be future date)
  reason: string;           // Reason for extension (required, min 10 chars)
}
```

**Response:**

```typescript
interface ApiResponse<void> {
  success: boolean;
  data?: null;
  error?: string;
}
```

**Usage Example:**

```typescript
const request: TrialExtensionRequest = {
  newTrialEndDate: '2024-02-15T23:59:59.000Z',
  reason: 'Customer requested extension due to integration delays'
};
```

### 2. Apply Discount to Subscription

```http
Method: POST
URL: /subscriptions/{tenantId}/apply-discount
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  tenantId: string;  // Tenant ID
}
```

**Request Body:**

```typescript
interface DiscountApplicationRequest {
  discountType: 'percentage' | 'fixed_amount';
  discountValue: number;           // Percentage (1-100) or amount in cents
  duration?: {
    startDate: string;             // ISO date string (default: now)
    endDate?: string;              // ISO date string (optional, null = permanent)
  };
  reason: string;                  // Reason for discount (required)
}
```

**Response:**

```typescript
interface ApiResponse<void> {
  success: boolean;
  data?: null;
  error?: string;
}
```

**Usage Examples:**

```typescript
// Percentage discount
const percentageDiscount: DiscountApplicationRequest = {
  discountType: 'percentage',
  discountValue: 25,  // 25% off
  duration: {
    startDate: '2024-01-01T00:00:00.000Z',
    endDate: '2024-12-31T23:59:59.000Z'
  },
  reason: 'Customer loyalty discount for annual renewal'
};

// Fixed amount discount
const fixedDiscount: DiscountApplicationRequest = {
  discountType: 'fixed_amount', 
  discountValue: 5000,  // $50.00 off (in cents)
  reason: 'Compensation for service interruption'
};
```

### 3. Extend Billing Period

```http
Method: POST
URL: /subscriptions/{tenantId}/extend-billing
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  tenantId: string;  // Tenant ID
}
```

**Request Body:**

```typescript
interface BillingExtensionRequest {
  newPeriodEndDate: string;  // ISO date string (must be after current end date)
  reason: string;            // Reason for extension (required)
}
```

**Response:**

```typescript
interface ApiResponse<void> {
  success: boolean;
  data?: null;
  error?: string;
}
```

**Usage Example:**

```typescript
const billingExtension: BillingExtensionRequest = {
  newPeriodEndDate: '2024-03-31T23:59:59.000Z',
  reason: 'Goodwill gesture for delayed feature delivery'
};
```

### 4. Grant Ad-hoc Feature

```http
Method: POST
URL: /subscriptions/{tenantId}/grant-feature
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  tenantId: string;  // Tenant ID
}
```

**Request Body:**

```typescript
interface FeatureGrantRequest {
  featureName: string;                // Feature identifier
  expiresWithPlan: boolean;          // True = expires with current plan
  customExpirationDate?: string;     // ISO date string (if expiresWithPlan = false)
  reason: string;                    // Reason for granting feature
}
```

**Response:**

```typescript
interface ApiResponse<void> {
  success: boolean;
  data?: null;
  error?: string;
}
```

**Usage Examples:**

```typescript
// Feature expires with plan
const planBasedFeature: FeatureGrantRequest = {
  featureName: 'advanced_analytics',
  expiresWithPlan: true,
  reason: 'Customer demo for potential upgrade'
};

// Feature with custom expiration
const timedFeature: FeatureGrantRequest = {
  featureName: 'priority_support',
  expiresWithPlan: false,
  customExpirationDate: '2024-06-30T23:59:59.000Z',
  reason: 'Compensation for service issues'
};
```

### 5. Designate Test Account

```http
Method: POST
URL: /subscriptions/{tenantId}/designate-test
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  tenantId: string;  // Tenant ID
}
```

**Request Body:**

```typescript
interface TestAccountRequest {
  accountType: 'demo' | 'test';      // Type of test account
  unlimitedAccess: boolean;          // Grant unlimited feature access
  reason: string;                    // Reason for designation
}
```

**Response:**

```typescript
interface ApiResponse<void> {
  success: boolean;
  data?: null;
  error?: string;
}
```

**Usage Examples:**

```typescript
// Demo account for sales
const demoAccount: TestAccountRequest = {
  accountType: 'demo',
  unlimitedAccess: true,
  reason: 'Sales demo account for enterprise prospects'
};

// Internal testing
const testAccount: TestAccountRequest = {
  accountType: 'test',
  unlimitedAccess: false,
  reason: 'QA testing for new feature rollout'
};
```

### 6. Get Subscription Audit Log

```http
Method: GET
URL: /subscriptions/{tenantId}/audit-log
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  tenantId: string;  // Tenant ID
}
```

**Query Parameters:**

```typescript
{
  page?: number;      // Page number (default: 1)
  pageSize?: number;  // Items per page (default: 20)
}
```

**Response:**

```typescript
interface SubscriptionAuditLog {
  entries: AuditEntry[];
  pagination: {
    page: number;
    pageSize: number;
    totalCount: number;
  };
}

interface AuditEntry {
  id: string;
  adminEmail: string;     // Admin who performed action
  action: string;         // Action type
  targetType: string;     // Type of target (subscription, feature, etc.)
  targetId: string;       // ID of target
  tenantId: string;       // Tenant ID
  tenantName: string;     // Tenant business name
  details: Record<string, unknown>; // Action-specific details
  timestamp: string;      // ISO date string
  ipAddress: string;      // Admin IP address
  userAgent: string;      // Admin browser/client
}
```

## Service Methods

### Core Methods

#### `extendTrial(request: TrialExtensionRequest)`

```typescript
async extendTrial(request: TrialExtensionRequest): Promise<ApiResponse<void>>
```

**Purpose**: Extend trial period for a tenant

**Parameters**:

- `request`: Trial extension details

**Returns**: API response with success/error status

**Validation Rules**:

- New end date must be in the future
- Reason must be at least 10 characters
- Tenant must have an active trial

**Usage Example**:

```typescript
import { subscriptionService } from '@/services/subscriptionService';

try {
  const response = await subscriptionService.extendTrial({
    tenantId: 'tenant-123',
    newTrialEndDate: '2024-02-15T23:59:59.000Z',
    reason: 'Customer requested extension due to integration delays'
  });
  
  if (response.success) {
    console.log('Trial extended successfully');
  }
} catch (error) {
  console.error('Failed to extend trial:', error.message);
}
```

#### `applyDiscount(request: DiscountApplicationRequest)`

```typescript
async applyDiscount(request: DiscountApplicationRequest): Promise<ApiResponse<void>>
```

**Purpose**: Apply discount to a subscription

**Parameters**:

- `request`: Discount application details

**Returns**: API response with success/error status

**Validation Rules**:

- Percentage discounts: 1-100
- Fixed amount discounts: positive integer (cents)
- Start date cannot be in the past
- End date must be after start date

**Usage Example**:

```typescript
import { subscriptionService } from '@/services/subscriptionService';

try {
  const response = await subscriptionService.applyDiscount({
    tenantId: 'tenant-123',
    discountType: 'percentage',
    discountValue: 20,
    duration: {
      startDate: new Date().toISOString(),
      endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 30 days
    },
    reason: 'Customer retention discount'
  });
  
  if (response.success) {
    console.log('Discount applied successfully');
  }
} catch (error) {
  console.error('Failed to apply discount:', error.message);
}
```

#### `extendBillingPeriod(request: BillingExtensionRequest)`

```typescript
async extendBillingPeriod(request: BillingExtensionRequest): Promise<ApiResponse<void>>
```

**Purpose**: Extend billing period for a subscription

**Parameters**:

- `request`: Billing extension details

**Returns**: API response with success/error status

**Validation Rules**:

- New end date must be after current billing period end
- Reason is required

**Usage Example**:

```typescript
import { subscriptionService } from '@/services/subscriptionService';

try {
  const response = await subscriptionService.extendBillingPeriod({
    tenantId: 'tenant-123',
    newPeriodEndDate: '2024-03-31T23:59:59.000Z',
    reason: 'Goodwill gesture for service disruption'
  });
  
  if (response.success) {
    console.log('Billing period extended successfully');
  }
} catch (error) {
  console.error('Failed to extend billing period:', error.message);
}
```

#### `grantFeature(request: FeatureGrantRequest)`

```typescript
async grantFeature(request: FeatureGrantRequest): Promise<ApiResponse<void>>
```

**Purpose**: Grant ad-hoc feature to a tenant

**Parameters**:

- `request`: Feature grant details

**Returns**: API response with success/error status

**Validation Rules**:

- Feature must exist in system
- Custom expiration date must be in future (if provided)
- Cannot grant features already included in current tier

**Usage Example**:

```typescript
import { subscriptionService } from '@/services/subscriptionService';

try {
  const response = await subscriptionService.grantFeature({
    tenantId: 'tenant-123',
    featureName: 'advanced_reporting',
    expiresWithPlan: false,
    customExpirationDate: '2024-06-30T23:59:59.000Z',
    reason: 'Special access for enterprise evaluation'
  });
  
  if (response.success) {
    console.log('Feature granted successfully');
  }
} catch (error) {
  console.error('Failed to grant feature:', error.message);
}
```

#### `designateTestAccount(request: TestAccountRequest)`

```typescript
async designateTestAccount(request: TestAccountRequest): Promise<ApiResponse<void>>
```

**Purpose**: Designate tenant as test account

**Parameters**:

- `request`: Test account designation details

**Returns**: API response with success/error status

**Business Rules**:

- Test accounts bypass billing
- Demo accounts get special UI treatment
- Unlimited access grants all features

**Usage Example**:

```typescript
import { subscriptionService } from '@/services/subscriptionService';

try {
  const response = await subscriptionService.designateTestAccount({
    tenantId: 'tenant-123',
    accountType: 'demo',
    unlimitedAccess: true,
    reason: 'Sales demo account for Q1 prospects'
  });
  
  if (response.success) {
    console.log('Account designated as test account');
  }
} catch (error) {
  console.error('Failed to designate test account:', error.message);
}
```

#### `getAuditLog(tenantId: string, page?: number, pageSize?: number)`

```typescript
async getAuditLog(tenantId: string, page = 1, pageSize = 20): Promise<SubscriptionAuditLog>
```

**Purpose**: Get audit log for subscription changes

**Parameters**:

- `tenantId`: Tenant ID
- `page`: Page number (optional, default: 1)
- `pageSize`: Items per page (optional, default: 20)

**Returns**: Paginated audit log entries

**Usage Example**:

```typescript
import { subscriptionService } from '@/services/subscriptionService';

try {
  const auditLog = await subscriptionService.getAuditLog('tenant-123', 1, 50);
  
  console.log(`Found ${auditLog.entries.length} audit entries`);
  auditLog.entries.forEach(entry => {
    console.log(`${entry.timestamp}: ${entry.action} by ${entry.adminEmail}`);
  });
} catch (error) {
  console.error('Failed to get audit log:', error.message);
}
```

## React Query Hooks

### Mutation Hooks

#### `useExtendTrial()`

```typescript
function useExtendTrial()
```

**Purpose**: Extend trial period with optimistic updates

**Returns**: TanStack Query mutation

**Cache Invalidation**: Invalidates subscriber details

**Usage Example**:

```typescript
import { useExtendTrial } from '@/hooks/useSubscriptions';
import { useToast } from '@/contexts/ToastContext';

function ExtendTrialDialog({ tenantId, onClose }: { tenantId: string; onClose: () => void }) {
  const [newEndDate, setNewEndDate] = useState('');
  const [reason, setReason] = useState('');
  
  const extendTrial = useExtendTrial();
  const toast = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    extendTrial.mutate({
      tenantId,
      newTrialEndDate: newEndDate,
      reason
    }, {
      onSuccess: () => {
        toast.showSuccess('Trial period extended successfully');
        onClose();
      },
      onError: (error) => {
        toast.showError(`Failed to extend trial: ${error.message}`);
      }
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Extend Trial Period</h2>
      
      <div>
        <label>New End Date:</label>
        <input
          type="datetime-local"
          value={newEndDate}
          onChange={(e) => setNewEndDate(e.target.value)}
          required
        />
      </div>
      
      <div>
        <label>Reason:</label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          minLength={10}
          required
        />
      </div>
      
      <button
        type="submit"
        disabled={extendTrial.isPending}
      >
        {extendTrial.isPending ? 'Extending...' : 'Extend Trial'}
      </button>
      
      <button type="button" onClick={onClose}>
        Cancel
      </button>
    </form>
  );
}
```

#### `useApplyDiscount()`

```typescript
function useApplyDiscount()
```

**Purpose**: Apply discount to subscription

**Returns**: TanStack Query mutation

**Cache Invalidation**: Invalidates subscriber details and billing info

**Usage Example**:

```typescript
import { useApplyDiscount } from '@/hooks/useSubscriptions';

function ApplyDiscountForm({ tenantId }: { tenantId: string }) {
  const [discountType, setDiscountType] = useState<'percentage' | 'fixed_amount'>('percentage');
  const [discountValue, setDiscountValue] = useState(0);
  const [duration, setDuration] = useState<'permanent' | 'temporary'>('temporary');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  
  const applyDiscount = useApplyDiscount();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const request = {
      tenantId,
      discountType,
      discountValue,
      reason
    };
    
    if (duration === 'temporary') {
      request.duration = {
        startDate: new Date().toISOString(),
        endDate: endDate
      };
    }
    
    applyDiscount.mutate(request);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Apply Discount</h2>
      
      <div>
        <label>Discount Type:</label>
        <select
          value={discountType}
          onChange={(e) => setDiscountType(e.target.value as 'percentage' | 'fixed_amount')}
        >
          <option value="percentage">Percentage</option>
          <option value="fixed_amount">Fixed Amount</option>
        </select>
      </div>
      
      <div>
        <label>
          {discountType === 'percentage' ? 'Percentage (%)' : 'Amount ($)'}:
        </label>
        <input
          type="number"
          value={discountValue}
          onChange={(e) => setDiscountValue(Number(e.target.value))}
          min={discountType === 'percentage' ? 1 : 0}
          max={discountType === 'percentage' ? 100 : undefined}
          step={discountType === 'percentage' ? 1 : 0.01}
          required
        />
      </div>
      
      <div>
        <label>Duration:</label>
        <select
          value={duration}
          onChange={(e) => setDuration(e.target.value as 'permanent' | 'temporary')}
        >
          <option value="temporary">Temporary</option>
          <option value="permanent">Permanent</option>
        </select>
      </div>
      
      {duration === 'temporary' && (
        <div>
          <label>End Date:</label>
          <input
            type="datetime-local"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            required
          />
        </div>
      )}
      
      <div>
        <label>Reason:</label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          required
        />
      </div>
      
      <button
        type="submit"
        disabled={applyDiscount.isPending}
      >
        {applyDiscount.isPending ? 'Applying...' : 'Apply Discount'}
      </button>
    </form>
  );
}
```

#### `useGrantFeature()`

```typescript
function useGrantFeature()
```

**Purpose**: Grant ad-hoc feature to tenant

**Returns**: TanStack Query mutation

**Cache Invalidation**: Invalidates subscriber details and feature grants

**Usage Example**:

```typescript
import { useGrantFeature } from '@/hooks/useSubscriptions';

function GrantFeatureDialog({ tenantId, availableFeatures }: {
  tenantId: string;
  availableFeatures: string[];
}) {
  const [selectedFeature, setSelectedFeature] = useState('');
  const [expiresWithPlan, setExpiresWithPlan] = useState(true);
  const [customExpiration, setCustomExpiration] = useState('');
  const [reason, setReason] = useState('');
  
  const grantFeature = useGrantFeature();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const request = {
      tenantId,
      featureName: selectedFeature,
      expiresWithPlan,
      reason
    };
    
    if (!expiresWithPlan && customExpiration) {
      request.customExpirationDate = customExpiration;
    }
    
    grantFeature.mutate(request);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Grant Feature Access</h2>
      
      <div>
        <label>Feature:</label>
        <select
          value={selectedFeature}
          onChange={(e) => setSelectedFeature(e.target.value)}
          required
        >
          <option value="">Select a feature</option>
          {availableFeatures.map(feature => (
            <option key={feature} value={feature}>{feature}</option>
          ))}
        </select>
      </div>
      
      <div>
        <label>
          <input
            type="radio"
            name="expiration"
            checked={expiresWithPlan}
            onChange={() => setExpiresWithPlan(true)}
          />
          Expires with current plan
        </label>
        
        <label>
          <input
            type="radio"
            name="expiration"
            checked={!expiresWithPlan}
            onChange={() => setExpiresWithPlan(false)}
          />
          Custom expiration date
        </label>
      </div>
      
      {!expiresWithPlan && (
        <div>
          <label>Expiration Date:</label>
          <input
            type="datetime-local"
            value={customExpiration}
            onChange={(e) => setCustomExpiration(e.target.value)}
            required
          />
        </div>
      )}
      
      <div>
        <label>Reason:</label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          required
        />
      </div>
      
      <button
        type="submit"
        disabled={grantFeature.isPending}
      >
        {grantFeature.isPending ? 'Granting...' : 'Grant Feature'}
      </button>
    </form>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum SubscriptionErrorType {
  TENANT_NOT_FOUND = 'TENANT_NOT_FOUND',
  INVALID_TRIAL_STATE = 'INVALID_TRIAL_STATE',
  INVALID_DATE_RANGE = 'INVALID_DATE_RANGE',
  FEATURE_NOT_FOUND = 'FEATURE_NOT_FOUND',
  FEATURE_ALREADY_GRANTED = 'FEATURE_ALREADY_GRANTED',
  DISCOUNT_VALIDATION_FAILED = 'DISCOUNT_VALIDATION_FAILED',
  BILLING_PERIOD_INVALID = 'BILLING_PERIOD_INVALID'
}
```

### Error Response Format

```typescript
interface SubscriptionServiceError {
  type: SubscriptionErrorType;
  message: string;
  statusCode: number;
  details?: {
    tenantId?: string;
    currentState?: string;
    validationErrors?: string[];
  };
}
```

### Error Handling Patterns

```typescript
import { subscriptionService } from '@/services/subscriptionService';
import { SubscriptionErrorType } from '@/types';

try {
  await subscriptionService.extendTrial({
    tenantId: 'tenant-123',
    newTrialEndDate: '2024-02-15T23:59:59.000Z',
    reason: 'Customer request'
  });
} catch (error) {
  switch (error.type) {
    case SubscriptionErrorType.TENANT_NOT_FOUND:
      showError('Subscriber not found');
      break;
    case SubscriptionErrorType.INVALID_TRIAL_STATE:
      showError('This subscription is not in trial state');
      break;
    case SubscriptionErrorType.INVALID_DATE_RANGE:
      showError('Invalid trial end date. Must be in the future.');
      break;
    default:
      showError('Failed to extend trial. Please try again.');
  }
}
```

## Business Rules & Validation

### Trial Extension Rules

1. **Trial State**: Subscription must be in trial status
2. **Date Validation**: New end date must be in future
3. **Maximum Extension**: Cannot extend beyond 90 days from original start
4. **Reason Required**: Must provide explanation for audit trail

### Discount Application Rules

1. **Percentage Discounts**: 1-100% range
2. **Fixed Amount**: Must be positive, cannot exceed subscription cost
3. **Duration**: Start date cannot be in past, end date must be after start
4. **Stacking**: Only one active discount per subscription

### Feature Grant Rules

1. **Feature Existence**: Feature must exist in system
2. **Tier Checking**: Cannot grant features already in current tier
3. **Expiration Logic**: Custom expiration requires future date
4. **Audit Trail**: All grants logged with admin and reason

### Test Account Rules

1. **Demo Accounts**: Get special UI indicators, unlimited features
2. **Test Accounts**: For internal QA, may have limited features
3. **Billing Bypass**: Test accounts excluded from billing processes
4. **Cleanup**: Test accounts should be cleaned up regularly

## Integration Examples

### Complete Subscription Management Panel

```typescript
import React, { useState } from 'react';
import {
  useExtendTrial,
  useApplyDiscount,
  useGrantFeature,
  useDesignateTestAccount
} from '@/hooks/useSubscriptions';

interface SubscriptionActionsProps {
  tenantId: string;
  subscriptionStatus: string;
  isTrialActive: boolean;
  currentTier: string;
}

function SubscriptionActions({
  tenantId,
  subscriptionStatus,
  isTrialActive,
  currentTier
}: SubscriptionActionsProps) {
  const [activeDialog, setActiveDialog] = useState<string | null>(null);
  
  const extendTrial = useExtendTrial();
  const applyDiscount = useApplyDiscount();
  const grantFeature = useGrantFeature();
  const designateTest = useDesignateTestAccount();

  const availableActions = [
    {
      id: 'extend-trial',
      label: 'Extend Trial',
      enabled: isTrialActive,
      icon: '⏰'
    },
    {
      id: 'apply-discount',
      label: 'Apply Discount',
      enabled: subscriptionStatus === 'active',
      icon: '💰'
    },
    {
      id: 'grant-feature',
      label: 'Grant Feature',
      enabled: true,
      icon: '🎁'
    },
    {
      id: 'extend-billing',
      label: 'Extend Billing',
      enabled: subscriptionStatus === 'active',
      icon: '📅'
    },
    {
      id: 'test-account',
      label: 'Test Account',
      enabled: true,
      icon: '🧪'
    }
  ];

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'extend-trial-quick':
        // Quick 7-day extension
        extendTrial.mutate({
          tenantId,
          newTrialEndDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          reason: 'Quick 7-day extension via admin panel'
        });
        break;
      case 'apply-discount-quick':
        // Quick 10% discount for 30 days
        applyDiscount.mutate({
          tenantId,
          discountType: 'percentage',
          discountValue: 10,
          duration: {
            startDate: new Date().toISOString(),
            endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
          },
          reason: 'Quick 10% discount for customer retention'
        });
        break;
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3>Subscription Actions</h3>
      
      {/* Quick Actions */}
      <div style={{ marginBottom: '20px' }}>
        <h4>Quick Actions</h4>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {isTrialActive && (
            <button
              onClick={() => handleQuickAction('extend-trial-quick')}
              disabled={extendTrial.isPending}
              style={{ padding: '8px 12px', fontSize: '12px' }}
            >
              +7 Days Trial
            </button>
          )}
          
          {subscriptionStatus === 'active' && (
            <button
              onClick={() => handleQuickAction('apply-discount-quick')}
              disabled={applyDiscount.isPending}
              style={{ padding: '8px 12px', fontSize: '12px' }}
            >
              10% Off (30d)
            </button>
          )}
        </div>
      </div>

      {/* Main Actions */}
      <div>
        <h4>Detailed Actions</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
          {availableActions.map(action => (
            <button
              key={action.id}
              onClick={() => setActiveDialog(action.id)}
              disabled={!action.enabled}
              style={{
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: action.enabled ? 'white' : '#f5f5f5',
                cursor: action.enabled ? 'pointer' : 'not-allowed',
                opacity: action.enabled ? 1 : 0.6
              }}
            >
              <div style={{ fontSize: '20px', marginBottom: '8px' }}>{action.icon}</div>
              <div>{action.label}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Status Indicators */}
      <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
        <div>Status: {subscriptionStatus}</div>
        <div>Tier: {currentTier}</div>
        {isTrialActive && <div>🟡 Trial Active</div>}
      </div>

      {/* Loading Indicators */}
      {(extendTrial.isPending || applyDiscount.isPending || grantFeature.isPending || designateTest.isPending) && (
        <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f0f8ff', borderRadius: '4px' }}>
          Processing action...
        </div>
      )}

      {/* Dialogs would be rendered here based on activeDialog state */}
      {activeDialog && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{ 
            backgroundColor: 'white', 
            padding: '20px', 
            borderRadius: '8px',
            maxWidth: '500px',
            width: '90%'
          }}>
            <div>Dialog for {activeDialog}</div>
            <button onClick={() => setActiveDialog(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
```

## Related Files

- `src/services/subscriptionService.ts` - Main service implementation
- `src/hooks/useSubscriptions.ts` - React Query hooks
- `src/types/index.ts` - Type definitions
- `src/components/features/subscriptions/` - Subscription operation components
- `src/pages/SubscriberDetailsPage.tsx` - Where subscription actions are used