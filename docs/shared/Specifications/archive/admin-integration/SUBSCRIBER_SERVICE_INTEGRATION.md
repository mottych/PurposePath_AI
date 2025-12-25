# Subscriber Management Service Integration Guide

## Service Overview

- **Service Name**: Subscriber Management Service
- **Base URL**: `{config.apiBaseUrl}/admin/subscribers`
- **Primary File**: `src/services/subscriberService.ts`
- **Hook File**: `src/hooks/useSubscribers.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Get Subscribers List

```http
Method: GET
URL: /admin/subscribers
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
interface SubscriberListParams {
  page?: number;                    // Page number (default: 1)
  pageSize?: number;               // Items per page (default: 50)
  search?: string;                 // Search by business name, contact name, or email
  tier?: string;                   // Filter by subscription tier ID
  status?: SubscriptionStatus;     // Filter by subscription status
  renewalFrequency?: BillingFrequency; // Filter by billing frequency
}

enum SubscriptionStatus {
  ACTIVE = 'active',
  TRIAL = 'trial',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled',
  SUSPENDED = 'suspended',
  PENDING = 'pending'
}

enum BillingFrequency {
  MONTHLY = 'monthly',
  YEARLY = 'yearly'
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<Subscriber>> {
  success: boolean;
  data: {
    items: Subscriber[];
    pagination: {
      page: number;
      pageSize: number;
      totalCount: number;
      totalPages: number;
      hasNext: boolean;
      hasPrevious: boolean;
    };
  };
  error?: string;
}

interface Subscriber {
  tenantId: string;                // Unique tenant identifier
  businessName: string;            // Business/organization name
  contactName: string;             // Primary contact name
  contactEmail: string;            // Primary contact email
  subscriptionStatus: SubscriptionStatus; // Current subscription status
  currentTier: {
    id: string;
    name: string;
    displayName: string;
  };
  billingInfo: {
    frequency: BillingFrequency;
    nextBillingDate: string;       // ISO date string
    amount: number;                // Amount in cents
    currency: string;              // Currency code (USD)
  };
  trialInfo?: {
    isTrialActive: boolean;
    trialStartDate: string;        // ISO date string
    trialEndDate: string;          // ISO date string
    trialDaysRemaining: number;
  };
  usage: {
    currentPeriodStart: string;    // ISO date string
    currentPeriodEnd: string;      // ISO date string
    goalsUsed: number;
    goalsLimit: number | null;     // null = unlimited
    kpisUsed: number;
    kpisLimit: number | null;
    actionsUsed: number;
    actionsLimit: number | null;
  };
  createdAt: string;               // ISO date string
  updatedAt: string;               // ISO date string
  lastActivityAt: string | null;   // ISO date string
}
```

### 2. Get Subscriber Details

```http
Method: GET
URL: /admin/subscribers/{tenantId}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  tenantId: string;  // Tenant ID
}
```

**Response:**

```typescript
interface SubscriptionDetails extends Subscriber {
  users: SubscriberUser[];
  subscriptionHistory: SubscriptionHistoryEntry[];
  paymentHistory: PaymentHistoryEntry[];
  featureGrants: FeatureGrant[];
  auditLog: AuditEntry[];
  supportTickets: SupportTicket[];
}

interface SubscriberUser {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'admin' | 'user';
  status: 'active' | 'inactive' | 'suspended';
  lastLoginAt: string | null;
  createdAt: string;
}

interface SubscriptionHistoryEntry {
  id: string;
  eventType: 'created' | 'upgraded' | 'downgraded' | 'renewed' | 'cancelled' | 'suspended' | 'reactivated';
  fromTier?: string;
  toTier?: string;
  effectiveDate: string;
  reason?: string;
  performedBy: string;
  timestamp: string;
}

interface PaymentHistoryEntry {
  id: string;
  invoiceId: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'failed' | 'refunded';
  paymentMethod: string;
  paidAt: string | null;
  dueDate: string;
  description: string;
}

interface FeatureGrant {
  feature: string;
  grantedAt: string;
  grantedBy: string;
  expiresAt: string | null;
  reason: string;
  isActive: boolean;
}

interface AuditEntry {
  id: string;
  adminEmail: string;
  action: string;
  targetType: string;
  targetId: string;
  details: Record<string, unknown>;
  timestamp: string;
  ipAddress: string;
  userAgent: string;
}

interface SupportTicket {
  id: string;
  subject: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  createdAt: string;
  lastUpdatedAt: string;
  assignedTo?: string;
}
```

## Service Methods

### Core Methods

#### `getSubscribers(params?: SubscriberListParams)`

```typescript
async getSubscribers(params: SubscriberListParams = {}): Promise<PaginatedResponse<Subscriber>>
```

**Purpose**: Fetch paginated list of subscribers with optional filters

**Parameters**:

- `params`: Optional filtering and pagination parameters

**Returns**: Paginated subscriber list

**Error Handling**: Automatic retry with exponential backoff

**Usage Example**:

```typescript
import { subscriberService } from '@/services/subscriberService';

// Get all subscribers (first page)
const subscribers = await subscriberService.getSubscribers();

// Get subscribers with filters
const filteredSubscribers = await subscriberService.getSubscribers({
  page: 2,
  pageSize: 25,
  search: 'Acme Corp',
  tier: 'pro-tier',
  status: SubscriptionStatus.ACTIVE,
  renewalFrequency: BillingFrequency.MONTHLY
});
```

#### `getSubscriberDetails(tenantId: string)`

```typescript
async getSubscriberDetails(tenantId: string): Promise<SubscriptionDetails>
```

**Purpose**: Get detailed information for a specific subscriber including users, history, and audit logs

**Parameters**:

- `tenantId`: Tenant ID

**Returns**: Complete subscription details

**Error Handling**: Throws error if subscriber not found or access denied

**Usage Example**:

```typescript
import { subscriberService } from '@/services/subscriberService';

const details = await subscriberService.getSubscriberDetails('tenant-123');
console.log('Business:', details.businessName);
console.log('Users:', details.users.length);
console.log('Current tier:', details.currentTier.displayName);
console.log('Next billing:', details.billingInfo.nextBillingDate);
```

## React Query Hooks

### Query Hooks

#### `useSubscribers(params?: SubscriberListParams)`

```typescript
function useSubscribers(params: SubscriberListParams = {})
```

**Purpose**: Fetch subscribers with caching and automatic refetching

**Parameters**: Same as `subscriberService.getSubscribers()`

**Returns**: TanStack Query result with subscriber data

**Cache Key**: `['subscribers', params]`

**Stale Time**: 5 minutes

**Usage Example**:

```typescript
import { useSubscribers } from '@/hooks/useSubscribers';
import { SubscriptionStatus, BillingFrequency } from '@/types';

function SubscriberList() {
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 50,
    status: SubscriptionStatus.ACTIVE
  });

  const {
    data: subscribers,
    isLoading,
    error,
    refetch
  } = useSubscribers(filters);

  if (isLoading) return <div>Loading subscribers...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Subscribers ({subscribers?.pagination.totalCount})</h1>
      
      {/* Filters */}
      <div>
        <select
          value={filters.status}
          onChange={(e) => setFilters(prev => ({
            ...prev,
            status: e.target.value as SubscriptionStatus
          }))}
        >
          <option value={SubscriptionStatus.ACTIVE}>Active</option>
          <option value={SubscriptionStatus.TRIAL}>Trial</option>
          <option value={SubscriptionStatus.EXPIRED}>Expired</option>
          <option value={SubscriptionStatus.CANCELLED}>Cancelled</option>
        </select>
      </div>

      {/* Subscriber Cards */}
      <div>
        {subscribers?.items.map(subscriber => (
          <div key={subscriber.tenantId}>
            <h3>{subscriber.businessName}</h3>
            <p>{subscriber.contactName} - {subscriber.contactEmail}</p>
            <p>Tier: {subscriber.currentTier.displayName}</p>
            <p>Status: {subscriber.subscriptionStatus}</p>
            <p>Next Billing: {subscriber.billingInfo.nextBillingDate}</p>
            
            {subscriber.trialInfo?.isTrialActive && (
              <p>Trial: {subscriber.trialInfo.trialDaysRemaining} days remaining</p>
            )}
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div>
        <button
          disabled={!subscribers?.pagination.hasPrevious}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
        >
          Previous
        </button>
        <span>Page {subscribers?.pagination.page} of {subscribers?.pagination.totalPages}</span>
        <button
          disabled={!subscribers?.pagination.hasNext}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

#### `useSubscriberDetails(tenantId: string)`

```typescript
function useSubscriberDetails(tenantId: string)
```

**Purpose**: Fetch detailed subscriber information

**Parameters**:

- `tenantId`: Tenant ID

**Returns**: TanStack Query result with subscription details

**Cache Key**: `['subscribers', tenantId, 'details']`

**Stale Time**: 2 minutes

**Enabled**: Only when tenantId is provided

**Usage Example**:

```typescript
import { useSubscriberDetails } from '@/hooks/useSubscribers';

function SubscriberDetailsPage({ tenantId }: { tenantId: string }) {
  const {
    data: details,
    isLoading,
    error
  } = useSubscriberDetails(tenantId);

  if (isLoading) return <div>Loading subscriber details...</div>;
  if (error) return <div>Error loading subscriber</div>;

  return (
    <div>
      <h1>{details?.businessName}</h1>
      
      {/* Basic Info */}
      <div>
        <h2>Contact Information</h2>
        <p>Name: {details?.contactName}</p>
        <p>Email: {details?.contactEmail}</p>
      </div>

      {/* Subscription Info */}
      <div>
        <h2>Subscription</h2>
        <p>Tier: {details?.currentTier.displayName}</p>
        <p>Status: {details?.subscriptionStatus}</p>
        <p>Billing: {details?.billingInfo.frequency}</p>
        <p>Next Payment: {details?.billingInfo.nextBillingDate}</p>
        <p>Amount: ${(details?.billingInfo.amount || 0) / 100}</p>
      </div>

      {/* Trial Info */}
      {details?.trialInfo?.isTrialActive && (
        <div>
          <h2>Trial Information</h2>
          <p>Days Remaining: {details.trialInfo.trialDaysRemaining}</p>
          <p>End Date: {details.trialInfo.trialEndDate}</p>
        </div>
      )}

      {/* Usage Stats */}
      <div>
        <h2>Current Usage</h2>
        <p>Goals: {details?.usage.goalsUsed} / {details?.usage.goalsLimit || 'Unlimited'}</p>
        <p>KPIs: {details?.usage.kpisUsed} / {details?.usage.kpisLimit || 'Unlimited'}</p>
        <p>Actions: {details?.usage.actionsUsed} / {details?.usage.actionsLimit || 'Unlimited'}</p>
      </div>

      {/* Users */}
      <div>
        <h2>Users ({details?.users.length})</h2>
        {details?.users.map(user => (
          <div key={user.id}>
            <p>{user.name} ({user.email}) - {user.role}</p>
            <p>Status: {user.status}</p>
            <p>Last Login: {user.lastLoginAt || 'Never'}</p>
          </div>
        ))}
      </div>

      {/* Feature Grants */}
      {details?.featureGrants.length > 0 && (
        <div>
          <h2>Special Feature Grants</h2>
          {details.featureGrants.map((grant, index) => (
            <div key={index}>
              <p>Feature: {grant.feature}</p>
              <p>Granted: {grant.grantedAt} by {grant.grantedBy}</p>
              <p>Expires: {grant.expiresAt || 'Never'}</p>
              <p>Reason: {grant.reason}</p>
            </div>
          ))}
        </div>
      )}

      {/* Recent History */}
      <div>
        <h2>Recent Activity</h2>
        {details?.subscriptionHistory.slice(0, 5).map(entry => (
          <div key={entry.id}>
            <p>{entry.eventType} - {entry.timestamp}</p>
            {entry.reason && <p>Reason: {entry.reason}</p>}
          </div>
        ))}
      </div>

      {/* Payment History */}
      <div>
        <h2>Recent Payments</h2>
        {details?.paymentHistory.slice(0, 5).map(payment => (
          <div key={payment.id}>
            <p>Invoice: {payment.invoiceId}</p>
            <p>Amount: ${payment.amount / 100} {payment.currency}</p>
            <p>Status: {payment.status}</p>
            <p>Due: {payment.dueDate}</p>
            {payment.paidAt && <p>Paid: {payment.paidAt}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum SubscriberErrorType {
  SUBSCRIBER_NOT_FOUND = 'SUBSCRIBER_NOT_FOUND',
  ACCESS_DENIED = 'ACCESS_DENIED',
  INVALID_TENANT_ID = 'INVALID_TENANT_ID',
  SUBSCRIPTION_INACTIVE = 'SUBSCRIPTION_INACTIVE'
}
```

### Error Response Format

```typescript
interface SubscriberServiceError {
  type: SubscriberErrorType;
  message: string;
  statusCode: number;
  details?: {
    tenantId?: string;
    currentStatus?: SubscriptionStatus;
    requiredPermission?: string;
  };
}
```

### Error Handling Patterns

```typescript
import { subscriberService } from '@/services/subscriberService';
import { SubscriberErrorType } from '@/types';

try {
  const details = await subscriberService.getSubscriberDetails('tenant-123');
  // Process subscriber details
} catch (error) {
  if (error.type === SubscriberErrorType.SUBSCRIBER_NOT_FOUND) {
    showError('Subscriber not found');
  } else if (error.type === SubscriberErrorType.ACCESS_DENIED) {
    showError('You do not have permission to view this subscriber');
  } else if (error.statusCode === 404) {
    showError('Subscriber not found');
  } else {
    showError('Failed to load subscriber details. Please try again.');
  }
}
```

## Business Rules & Constraints

### Subscription Status Rules

```typescript
const statusDescriptions = {
  [SubscriptionStatus.ACTIVE]: 'Subscription is current and active',
  [SubscriptionStatus.TRIAL]: 'In trial period',
  [SubscriptionStatus.EXPIRED]: 'Subscription has expired',
  [SubscriptionStatus.CANCELLED]: 'Subscription was cancelled',
  [SubscriptionStatus.SUSPENDED]: 'Subscription is temporarily suspended',
  [SubscriptionStatus.PENDING]: 'Subscription setup is pending'
};
```

### Usage Limit Enforcement

1. **Goals**: Limited by tier, null = unlimited
2. **KPIs**: Limited by tier, null = unlimited  
3. **Actions**: Limited by tier, null = unlimited
4. **Users**: Limited by tier configuration
5. **Storage**: Limited by tier configuration

### Access Control

1. **Tenant Access**: Admins can only view subscribers in their accessible tenants
2. **Data Privacy**: Sensitive payment and user data requires special permissions
3. **Audit Trail**: All subscriber data access is logged

## Search & Filtering

### Search Functionality

The search parameter supports searching across:

- Business name (partial match, case-insensitive)
- Contact name (partial match, case-insensitive)
- Contact email (partial match, case-insensitive)
- Tenant ID (exact match)

### Advanced Filtering

```typescript
// Complex filtering example
const advancedFilters = {
  search: 'tech company',
  tier: 'enterprise',
  status: SubscriptionStatus.ACTIVE,
  renewalFrequency: BillingFrequency.YEARLY,
  page: 1,
  pageSize: 25
};

const subscribers = await subscriberService.getSubscribers(advancedFilters);
```

### Sorting Options

Default sorting is by:
1. Subscription status (active first)
2. Business name (alphabetical)
3. Created date (newest first)

## Performance Considerations

### Caching Strategy

- **Subscriber List**: 5-minute cache with background refetch
- **Subscriber Details**: 2-minute cache for frequently accessed data
- **Search Results**: 1-minute cache for search queries

### Pagination Best Practices

```typescript
// Recommended page sizes
const pageSizeOptions = [25, 50, 100, 200];

// Large datasets
const largeDatasetQuery = {
  pageSize: 25, // Smaller pages for faster loading
  page: 1
};

// Export scenarios
const exportQuery = {
  pageSize: 1000, // Larger pages for bulk operations
  page: 1
};
```

### Rate Limiting

- **Subscriber List**: 200 requests per minute per admin
- **Subscriber Details**: 500 requests per minute per admin
- **Search**: 100 requests per minute per admin

## Integration Examples

### Complete Subscriber Dashboard

```typescript
import React, { useState, useMemo } from 'react';
import { useSubscribers, useSubscriberDetails } from '@/hooks/useSubscribers';
import { SubscriptionStatus, BillingFrequency } from '@/types';

function SubscriberDashboard() {
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 50,
    search: '',
    status: '' as SubscriptionStatus | '',
    tier: '',
    renewalFrequency: '' as BillingFrequency | ''
  });

  const [selectedTenant, setSelectedTenant] = useState<string | null>(null);

  // Clean filters (remove empty values)
  const cleanFilters = useMemo(() => {
    const clean: any = { page: filters.page, pageSize: filters.pageSize };
    if (filters.search) clean.search = filters.search;
    if (filters.status) clean.status = filters.status;
    if (filters.tier) clean.tier = filters.tier;
    if (filters.renewalFrequency) clean.renewalFrequency = filters.renewalFrequency;
    return clean;
  }, [filters]);

  const {
    data: subscribers,
    isLoading: subscribersLoading,
    error: subscribersError
  } = useSubscribers(cleanFilters);

  const {
    data: selectedSubscriber,
    isLoading: detailsLoading
  } = useSubscriberDetails(selectedTenant!);

  const handleSearch = (search: string) => {
    setFilters(prev => ({ ...prev, search, page: 1 }));
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  if (subscribersLoading) return <div>Loading subscribers...</div>;
  if (subscribersError) return <div>Error: {subscribersError.message}</div>;

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Subscriber List */}
      <div style={{ width: '60%', padding: '20px', borderRight: '1px solid #ccc' }}>
        <h1>Subscribers ({subscribers?.pagination.totalCount})</h1>
        
        {/* Search and Filters */}
        <div style={{ marginBottom: '20px' }}>
          <input
            type="text"
            placeholder="Search subscribers..."
            value={filters.search}
            onChange={(e) => handleSearch(e.target.value)}
            style={{ marginRight: '10px', padding: '8px' }}
          />
          
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            style={{ marginRight: '10px', padding: '8px' }}
          >
            <option value="">All Statuses</option>
            <option value={SubscriptionStatus.ACTIVE}>Active</option>
            <option value={SubscriptionStatus.TRIAL}>Trial</option>
            <option value={SubscriptionStatus.EXPIRED}>Expired</option>
            <option value={SubscriptionStatus.CANCELLED}>Cancelled</option>
            <option value={SubscriptionStatus.SUSPENDED}>Suspended</option>
          </select>

          <select
            value={filters.renewalFrequency}
            onChange={(e) => handleFilterChange('renewalFrequency', e.target.value)}
            style={{ padding: '8px' }}
          >
            <option value="">All Frequencies</option>
            <option value={BillingFrequency.MONTHLY}>Monthly</option>
            <option value={BillingFrequency.YEARLY}>Yearly</option>
          </select>
        </div>

        {/* Subscriber Cards */}
        <div>
          {subscribers?.items.map(subscriber => (
            <div
              key={subscriber.tenantId}
              onClick={() => setSelectedTenant(subscriber.tenantId)}
              style={{
                border: '1px solid #ddd',
                padding: '15px',
                marginBottom: '10px',
                cursor: 'pointer',
                backgroundColor: selectedTenant === subscriber.tenantId ? '#f0f8ff' : 'white'
              }}
            >
              <h3>{subscriber.businessName}</h3>
              <p>{subscriber.contactName} - {subscriber.contactEmail}</p>
              <div style={{ display: 'flex', gap: '20px' }}>
                <span>Tier: {subscriber.currentTier.displayName}</span>
                <span>Status: {subscriber.subscriptionStatus}</span>
                <span>Billing: {subscriber.billingInfo.frequency}</span>
              </div>
              
              {subscriber.trialInfo?.isTrialActive && (
                <p style={{ color: 'orange' }}>
                  Trial: {subscriber.trialInfo.trialDaysRemaining} days remaining
                </p>
              )}

              <div style={{ fontSize: '12px', color: '#666' }}>
                Goals: {subscriber.usage.goalsUsed} / {subscriber.usage.goalsLimit || '∞'} | 
                KPIs: {subscriber.usage.kpisUsed} / {subscriber.usage.kpisLimit || '∞'} |
                Actions: {subscriber.usage.actionsUsed} / {subscriber.usage.actionsLimit || '∞'}
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        <div style={{ marginTop: '20px' }}>
          <button
            disabled={!subscribers?.pagination.hasPrevious}
            onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
          >
            Previous
          </button>
          <span style={{ margin: '0 15px' }}>
            Page {subscribers?.pagination.page} of {subscribers?.pagination.totalPages}
          </span>
          <button
            disabled={!subscribers?.pagination.hasNext}
            onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
          >
            Next
          </button>
        </div>
      </div>

      {/* Subscriber Details */}
      <div style={{ width: '40%', padding: '20px' }}>
        {selectedTenant ? (
          detailsLoading ? (
            <div>Loading details...</div>
          ) : selectedSubscriber ? (
            <div>
              <h2>{selectedSubscriber.businessName}</h2>
              
              {/* Quick Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '20px' }}>
                <div style={{ border: '1px solid #ddd', padding: '10px', textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{selectedSubscriber.users.length}</div>
                  <div>Users</div>
                </div>
                <div style={{ border: '1px solid #ddd', padding: '10px', textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                    ${(selectedSubscriber.billingInfo.amount / 100).toFixed(2)}
                  </div>
                  <div>{selectedSubscriber.billingInfo.frequency}</div>
                </div>
              </div>

              {/* Contact Info */}
              <div style={{ marginBottom: '20px' }}>
                <h3>Contact</h3>
                <p>{selectedSubscriber.contactName}</p>
                <p>{selectedSubscriber.contactEmail}</p>
              </div>

              {/* Subscription Info */}
              <div style={{ marginBottom: '20px' }}>
                <h3>Subscription</h3>
                <p>Tier: {selectedSubscriber.currentTier.displayName}</p>
                <p>Status: {selectedSubscriber.subscriptionStatus}</p>
                <p>Next Billing: {new Date(selectedSubscriber.billingInfo.nextBillingDate).toLocaleDateString()}</p>
              </div>

              {/* Usage */}
              <div style={{ marginBottom: '20px' }}>
                <h3>Usage</h3>
                <div>Goals: {selectedSubscriber.usage.goalsUsed} / {selectedSubscriber.usage.goalsLimit || 'Unlimited'}</div>
                <div>KPIs: {selectedSubscriber.usage.kpisUsed} / {selectedSubscriber.usage.kpisLimit || 'Unlimited'}</div>
                <div>Actions: {selectedSubscriber.usage.actionsUsed} / {selectedSubscriber.usage.actionsLimit || 'Unlimited'}</div>
              </div>

              {/* Recent Activity */}
              <div>
                <h3>Recent Activity</h3>
                {selectedSubscriber.subscriptionHistory.slice(0, 3).map(entry => (
                  <div key={entry.id} style={{ fontSize: '14px', marginBottom: '5px' }}>
                    {entry.eventType} - {new Date(entry.timestamp).toLocaleDateString()}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>Failed to load details</div>
          )
        ) : (
          <div style={{ textAlign: 'center', marginTop: '50px', color: '#666' }}>
            Select a subscriber to view details
          </div>
        )}
      </div>
    </div>
  );
}
```

## Related Files

- `src/services/subscriberService.ts` - Main service implementation
- `src/hooks/useSubscribers.ts` - React Query hooks  
- `src/types/index.ts` - Type definitions
- `src/components/features/subscribers/` - Subscriber management components
- `src/pages/SubscribersPage.tsx` - Main subscribers page
- `src/pages/SubscriberDetailsPage.tsx` - Subscriber details page