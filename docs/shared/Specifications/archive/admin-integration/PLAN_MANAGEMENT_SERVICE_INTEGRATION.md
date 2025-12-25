# Plan Management Service Integration Guide

## Service Overview

- **Service Name**: Plan Management Service
- **Base URL**: `{config.apiBaseUrl}/admin/plans`
- **Primary File**: `src/services/planService.ts`
- **Hook File**: `src/hooks/usePlans.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Get Plans List

```http
Method: GET
URL: /admin/plans
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
interface PlanListParams {
  page?: number;                          // Page number (default: 1)
  pageSize?: number;                      // Items per page (default: 50)
  search?: string;                        // Search by plan name or description
  status?: 'active' | 'inactive' | 'all'; // Filter by status (default: 'all')
  planType?: 'basic' | 'pro' | 'enterprise' | 'all'; // Filter by type
  includeUsage?: boolean;                 // Include usage statistics (default: false)
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<Plan>> {
  success: boolean;
  data: {
    items: Plan[];
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

interface Plan {
  id: string;                            // Unique plan ID
  name: string;                          // Plan name (e.g., "Basic Plan")
  description: string;                   // Plan description
  planType: 'basic' | 'pro' | 'enterprise'; // Plan tier
  monthlyPrice: number;                  // Monthly price in cents
  yearlyPrice: number;                   // Yearly price in cents (usually discounted)
  yearlyDiscount: number;                // Yearly discount percentage
  features: PlanFeature[];               // Plan features and limits
  maxUsers: number;                      // Maximum users allowed
  maxProjects: number;                   // Maximum projects allowed
  maxStorage: number;                    // Storage limit in MB
  supportLevel: 'basic' | 'priority' | 'premium'; // Support tier
  isActive: boolean;                     // Whether plan is available for new subscriptions
  isDefault: boolean;                    // Default plan for new users
  trialDays: number;                     // Free trial duration in days
  createdAt: string;                     // ISO date string
  updatedAt: string;                     // ISO date string
  usageStats?: PlanUsageStats;           // Usage statistics (if requested)
}

interface PlanFeature {
  id: string;                            // Feature ID
  name: string;                          // Feature name
  description: string;                   // Feature description
  included: boolean;                     // Whether feature is included
  limit?: number;                        // Feature limit (null = unlimited)
  category: 'core' | 'advanced' | 'premium'; // Feature category
}

interface PlanUsageStats {
  activeSubscriptions: number;           // Current active subscriptions
  totalSubscriptions: number;            // Total subscriptions (all time)
  monthlyRevenue: number;                // Monthly recurring revenue
  yearlyRevenue: number;                 // Yearly recurring revenue
  averageLifetimeValue: number;          // Average customer lifetime value
}
```

### 2. Get Plan Details

```http
Method: GET
URL: /admin/plans/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Plan ID
}
```

**Query Parameters:**

```typescript
{
  includeUsage?: boolean;  // Include usage statistics (default: false)
}
```

**Response:**

```typescript
interface ApiResponse<Plan> {
  success: boolean;
  data: Plan;
  error?: string;
}
```

### 3. Get Plan Usage Statistics

```http
Method: GET
URL: /admin/plans/{id}/usage
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Plan ID
}
```

**Query Parameters:**

```typescript
{
  period?: 'month' | 'quarter' | 'year';  // Time period for stats (default: 'month')
  startDate?: string;                      // Start date (ISO string)
  endDate?: string;                        // End date (ISO string)
}
```

**Response:**

```typescript
interface ApiResponse<DetailedPlanUsage> {
  success: boolean;
  data: DetailedPlanUsage;
  error?: string;
}

interface DetailedPlanUsage {
  planId: string;
  planName: string;
  period: {
    start: string;                       // ISO date string
    end: string;                         // ISO date string
  };
  subscriptions: {
    active: number;                      // Currently active
    new: number;                         // New in period
    cancelled: number;                   // Cancelled in period
    churned: number;                     // Churned in period
  };
  revenue: {
    monthly: number;                     // Monthly recurring revenue
    yearly: number;                      // Yearly revenue
    total: number;                       // Total revenue in period
  };
  growth: {
    subscriptionGrowthRate: number;      // Subscription growth rate (%)
    revenueGrowthRate: number;           // Revenue growth rate (%)
  };
  subscribers: SubscriberBreakdown[];    // Subscriber breakdown by tenant
}

interface SubscriberBreakdown {
  tenantId: string;
  tenantName: string;
  subscriptionType: 'monthly' | 'yearly';
  startDate: string;
  status: 'active' | 'cancelled' | 'pending';
  revenue: number;
}
```

### 4. Create Plan

```http
Method: POST
URL: /admin/plans
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface CreatePlanData {
  name: string;                          // Plan name
  description: string;                   // Plan description
  planType: 'basic' | 'pro' | 'enterprise'; // Plan tier
  monthlyPrice: number;                  // Monthly price in cents
  yearlyPrice: number;                   // Yearly price in cents
  features: CreatePlanFeature[];         // Plan features
  maxUsers: number;                      // Maximum users
  maxProjects: number;                   // Maximum projects
  maxStorage: number;                    // Storage limit in MB
  supportLevel: 'basic' | 'priority' | 'premium'; // Support level
  isActive: boolean;                     // Active status
  isDefault: boolean;                    // Default plan
  trialDays: number;                     // Trial period in days
}

interface CreatePlanFeature {
  featureId: string;                     // Reference to system feature
  included: boolean;                     // Whether included
  limit?: number;                        // Feature limit (null = unlimited)
}
```

**Response:**

```typescript
interface ApiResponse<Plan> {
  success: boolean;
  data: Plan;
  error?: string;
}
```

### 5. Update Plan

```http
Method: PATCH
URL: /admin/plans/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Plan ID
}
```

**Request Body:**

```typescript
interface UpdatePlanData extends Partial<CreatePlanData> {
  // All fields from CreatePlanData are optional for updates
}
```

**Response:**

```typescript
interface ApiResponse<Plan> {
  success: boolean;
  data: Plan;
  error?: string;
}
```

### 6. Enable/Disable Plan

```http
Method: POST
URL: /admin/plans/{id}/enable
URL: /admin/plans/{id}/disable
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Plan ID
}
```

**Response:**

```typescript
interface ApiResponse<Plan> {
  success: boolean;
  data: Plan;
  error?: string;
}
```

### 7. Set Default Plan

```http
Method: POST
URL: /admin/plans/{id}/set-default
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Plan ID
}
```

**Response:**

```typescript
interface ApiResponse<Plan> {
  success: boolean;
  data: Plan;
  error?: string;
}
```

### 8. Delete Plan

```http
Method: DELETE
URL: /admin/plans/{id}
Authentication: Bearer {access_token}
```

**Path Parameters:**

```typescript
{
  id: string;  // Plan ID
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

## Service Methods

### Core Methods

#### `getPlans(params?: PlanListParams)`

```typescript
async getPlans(params: PlanListParams = {}): Promise<PaginatedResponse<Plan>>
```

**Purpose**: Fetch paginated list of plans with optional filters

**Parameters**:

- `params`: Optional filtering and pagination parameters

**Returns**: Paginated plan list

**Usage Example**:

```typescript
import { planService } from '@/services/planService';

// Get all active plans
const activePlans = await planService.getPlans({
  status: 'active',
  includeUsage: true
});

// Search for specific plans
const searchResults = await planService.getPlans({
  search: 'Enterprise',
  planType: 'enterprise'
});
```

#### `getPlan(id: string, includeUsage?: boolean)`

```typescript
async getPlan(id: string, includeUsage: boolean = false): Promise<Plan>
```

**Purpose**: Get plan details by ID

**Parameters**:

- `id`: Plan ID
- `includeUsage`: Whether to include usage statistics

**Returns**: Complete plan details

**Usage Example**:

```typescript
import { planService } from '@/services/planService';

const plan = await planService.getPlan('plan-123', true);
console.log(`Plan: ${plan.name}, Active Subs: ${plan.usageStats?.activeSubscriptions}`);
```

#### `createPlan(data: CreatePlanData)`

```typescript
async createPlan(data: CreatePlanData): Promise<Plan>
```

**Purpose**: Create a new subscription plan

**Parameters**:

- `data`: Plan creation data

**Returns**: Created plan

**Validation Rules**:

- Plan name must be unique
- Monthly price must be positive
- Yearly price typically less than 12x monthly (discount)
- At least one feature must be included

**Usage Example**:

```typescript
import { planService } from '@/services/planService';

const newPlan = await planService.createPlan({
  name: 'Professional Plan',
  description: 'Advanced features for growing teams',
  planType: 'pro',
  monthlyPrice: 4900, // $49.00
  yearlyPrice: 49000, // $490.00 (2 months free)
  features: [
    { featureId: 'unlimited-projects', included: true },
    { featureId: 'advanced-analytics', included: true },
    { featureId: 'priority-support', included: true },
    { featureId: 'custom-integrations', included: true, limit: 10 }
  ],
  maxUsers: 25,
  maxProjects: -1, // Unlimited
  maxStorage: 100000, // 100GB
  supportLevel: 'priority',
  isActive: true,
  isDefault: false,
  trialDays: 14
});
```

#### `updatePlan(id: string, data: UpdatePlanData)`

```typescript
async updatePlan(id: string, data: UpdatePlanData): Promise<Plan>
```

**Purpose**: Update existing plan

**Parameters**:

- `id`: Plan ID
- `data`: Fields to update

**Returns**: Updated plan

**Business Rules**:

- Cannot change planType if plan has active subscriptions
- Price increases require notification to existing subscribers
- Feature removals may affect existing subscribers

**Usage Example**:

```typescript
import { planService } from '@/services/planService';

const updatedPlan = await planService.updatePlan('plan-123', {
  description: 'Updated plan description',
  monthlyPrice: 5900, // Price increase
  maxUsers: 50, // Increased user limit
  features: [
    // Updated feature set
    { featureId: 'unlimited-projects', included: true },
    { featureId: 'advanced-analytics', included: true },
    { featureId: 'ai-insights', included: true } // New feature
  ]
});
```

## React Query Hooks

### Query Hooks

#### `usePlans(params?: PlanListParams)`

```typescript
function usePlans(params: PlanListParams = {})
```

**Purpose**: Fetch plans with caching and automatic refetching

**Cache Key**: `['plans', params]`

**Stale Time**: 10 minutes

**Usage Example**:

```typescript
import { usePlans } from '@/hooks/usePlans';

function PlansList() {
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 20,
    status: 'active' as const,
    includeUsage: true
  });

  const {
    data: plans,
    isLoading,
    error
  } = usePlans(filters);

  if (isLoading) return <div>Loading plans...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Subscription Plans ({plans?.pagination.totalCount})</h1>
      
      {/* Status Filter */}
      <div style={{ marginBottom: '20px' }}>
        <select
          value={filters.status}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            status: e.target.value as 'active' | 'inactive' | 'all' 
          }))}
        >
          <option value="all">All Plans</option>
          <option value="active">Active Only</option>
          <option value="inactive">Inactive Only</option>
        </select>
      </div>

      {/* Plans Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        {plans?.items.map(plan => (
          <div key={plan.id} style={{ 
            border: '1px solid #ddd', 
            padding: '20px', 
            borderRadius: '8px',
            backgroundColor: plan.isActive ? 'white' : '#f5f5f5'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
              <div>
                <h3 style={{ margin: '0 0 5px 0' }}>{plan.name}</h3>
                <span style={{
                  background: plan.planType === 'basic' ? '#e3f2fd' : 
                             plan.planType === 'pro' ? '#f3e5f5' : '#e8f5e8',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  textTransform: 'uppercase'
                }}>
                  {plan.planType}
                </span>
              </div>
              
              <div style={{ display: 'flex', gap: '5px' }}>
                {plan.isDefault && (
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    backgroundColor: '#ff9800',
                    color: 'white'
                  }}>
                    DEFAULT
                  </span>
                )}
                <span style={{
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '10px',
                  backgroundColor: plan.isActive ? '#4caf50' : '#757575',
                  color: 'white'
                }}>
                  {plan.isActive ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>
            </div>
            
            <p style={{ margin: '0 0 15px 0', color: '#666', fontSize: '14px' }}>
              {plan.description}
            </p>
            
            {/* Pricing */}
            <div style={{ marginBottom: '15px' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                ${(plan.monthlyPrice / 100).toFixed(2)}
                <span style={{ fontSize: '14px', fontWeight: 'normal', color: '#666' }}>
                  /month
                </span>
              </div>
              
              {plan.yearlyPrice && (
                <div style={{ fontSize: '14px', color: '#666' }}>
                  ${(plan.yearlyPrice / 100).toFixed(2)}/year 
                  <span style={{ color: '#4caf50', marginLeft: '5px' }}>
                    ({plan.yearlyDiscount}% off)
                  </span>
                </div>
              )}
            </div>
            
            {/* Limits */}
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '15px' }}>
              <div>Users: {plan.maxUsers === -1 ? 'Unlimited' : plan.maxUsers}</div>
              <div>Projects: {plan.maxProjects === -1 ? 'Unlimited' : plan.maxProjects}</div>
              <div>Storage: {plan.maxStorage === -1 ? 'Unlimited' : `${Math.round(plan.maxStorage / 1024)}GB`}</div>
              <div>Support: {plan.supportLevel}</div>
              {plan.trialDays > 0 && <div>Trial: {plan.trialDays} days</div>}
            </div>
            
            {/* Usage Stats */}
            {plan.usageStats && (
              <div style={{ 
                borderTop: '1px solid #eee', 
                paddingTop: '10px', 
                fontSize: '12px' 
              }}>
                <div>Active Subscriptions: {plan.usageStats.activeSubscriptions}</div>
                <div>Monthly Revenue: ${(plan.usageStats.monthlyRevenue / 100).toFixed(2)}</div>
              </div>
            )}
            
            {/* Features Preview */}
            <div style={{ marginTop: '10px' }}>
              <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>
                Key Features ({plan.features.length}):
              </div>
              <div style={{ fontSize: '11px', color: '#666' }}>
                {plan.features.slice(0, 3).map(feature => feature.name).join(', ')}
                {plan.features.length > 3 && '...'}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          disabled={!plans?.pagination.hasPrevious}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
        >
          Previous
        </button>
        <span style={{ margin: '0 15px' }}>
          Page {plans?.pagination.page} of {plans?.pagination.totalPages}
        </span>
        <button
          disabled={!plans?.pagination.hasNext}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

#### `usePlan(id: string, includeUsage?: boolean)`

```typescript
function usePlan(id: string, includeUsage: boolean = false)
```

**Purpose**: Fetch single plan details

**Cache Key**: `['plans', id, { includeUsage }]`

**Stale Time**: 5 minutes

**Usage Example**:

```typescript
import { usePlan } from '@/hooks/usePlans';

function PlanDetails({ planId }: { planId: string }) {
  const {
    data: plan,
    isLoading,
    error
  } = usePlan(planId, true);

  if (isLoading) return <div>Loading plan details...</div>;
  if (error) return <div>Error loading plan</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
        <div>
          <h1>{plan?.name}</h1>
          <p style={{ color: '#666' }}>{plan?.description}</p>
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
            ${(plan?.monthlyPrice / 100).toFixed(2)}
            <span style={{ fontSize: '16px', fontWeight: 'normal' }}>/mo</span>
          </div>
          
          {plan?.yearlyPrice && (
            <div style={{ fontSize: '14px', color: '#666' }}>
              or ${(plan.yearlyPrice / 100).toFixed(2)}/year
            </div>
          )}
        </div>
      </div>
      
      {/* Plan Details */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginBottom: '30px' }}>
        <div>
          <h3>Plan Limits</h3>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li>👥 Users: {plan?.maxUsers === -1 ? 'Unlimited' : plan?.maxUsers}</li>
            <li>📁 Projects: {plan?.maxProjects === -1 ? 'Unlimited' : plan?.maxProjects}</li>
            <li>💾 Storage: {plan?.maxStorage === -1 ? 'Unlimited' : `${Math.round(plan?.maxStorage / 1024)}GB`}</li>
            <li>🎧 Support: {plan?.supportLevel}</li>
            {plan?.trialDays > 0 && <li>🆓 Trial: {plan.trialDays} days</li>}
          </ul>
        </div>
        
        {plan?.usageStats && (
          <div>
            <h3>Usage Statistics</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li>📊 Active Subscriptions: {plan.usageStats.activeSubscriptions}</li>
              <li>💰 Monthly Revenue: ${(plan.usageStats.monthlyRevenue / 100).toFixed(2)}</li>
              <li>💵 Yearly Revenue: ${(plan.usageStats.yearlyRevenue / 100).toFixed(2)}</li>
              <li>📈 Avg LTV: ${(plan.usageStats.averageLifetimeValue / 100).toFixed(2)}</li>
            </ul>
          </div>
        )}
      </div>
      
      {/* Features */}
      <div>
        <h3>Features</h3>
        <div style={{ display: 'grid', gap: '10px' }}>
          {plan?.features.map(feature => (
            <div key={feature.id} style={{ 
              padding: '10px', 
              border: '1px solid #ddd', 
              borderRadius: '4px',
              backgroundColor: feature.included ? '#f8f9fa' : '#fff3cd'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong>{feature.name}</strong>
                  {feature.limit && (
                    <span style={{ color: '#666', marginLeft: '10px' }}>
                      (Limit: {feature.limit})
                    </span>
                  )}
                </div>
                
                <span style={{
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  backgroundColor: feature.included ? '#4caf50' : '#ff9800',
                  color: 'white'
                }}>
                  {feature.included ? 'Included' : 'Limited'}
                </span>
              </div>
              
              <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#666' }}>
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### Mutation Hooks

#### `useCreatePlan()`

```typescript
function useCreatePlan()
```

**Purpose**: Create new plan with cache invalidation

**Cache Invalidation**: Invalidates plans list

**Usage Example**:

```typescript
import { useCreatePlan } from '@/hooks/usePlans';
import { useToast } from '@/contexts/ToastContext';

function CreatePlanForm() {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    planType: 'basic' as const,
    monthlyPrice: 0,
    yearlyPrice: 0,
    maxUsers: 1,
    maxProjects: 1,
    maxStorage: 1024, // 1GB default
    supportLevel: 'basic' as const,
    isActive: true,
    isDefault: false,
    trialDays: 0,
    features: [] as CreatePlanFeature[]
  });

  const createPlan = useCreatePlan();
  const toast = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Convert prices to cents
    const data = {
      ...formData,
      monthlyPrice: Math.round(formData.monthlyPrice * 100),
      yearlyPrice: Math.round(formData.yearlyPrice * 100)
    };
    
    createPlan.mutate(data, {
      onSuccess: (newPlan) => {
        toast.showSuccess(`Plan "${newPlan.name}" created successfully`);
        // Reset form or navigate away
      },
      onError: (error) => {
        toast.showError(`Failed to create plan: ${error.message}`);
      }
    });
  };

  const calculateYearlyDiscount = () => {
    if (formData.monthlyPrice > 0 && formData.yearlyPrice > 0) {
      const monthlyTotal = formData.monthlyPrice * 12;
      return Math.round(((monthlyTotal - formData.yearlyPrice) / monthlyTotal) * 100);
    }
    return 0;
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '600px' }}>
      <h2>Create New Plan</h2>
      
      {/* Basic Info */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Basic Information</h3>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Plan Name:</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            required
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Description:</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            required
            rows={3}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Plan Type:</label>
          <select
            value={formData.planType}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              planType: e.target.value as 'basic' | 'pro' | 'enterprise'
            }))}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          >
            <option value="basic">Basic</option>
            <option value="pro">Professional</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
      </div>
      
      {/* Pricing */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Pricing</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
          <div>
            <label>Monthly Price ($):</label>
            <input
              type="number"
              value={formData.monthlyPrice}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                monthlyPrice: Number(e.target.value)
              }))}
              min={0}
              step={0.01}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            />
          </div>
          
          <div>
            <label>Yearly Price ($):</label>
            <input
              type="number"
              value={formData.yearlyPrice}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                yearlyPrice: Number(e.target.value)
              }))}
              min={0}
              step={0.01}
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            />
            {formData.yearlyPrice > 0 && (
              <div style={{ fontSize: '12px', color: '#4caf50', marginTop: '2px' }}>
                {calculateYearlyDiscount()}% discount vs monthly
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Limits */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Plan Limits</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div>
            <label>Max Users:</label>
            <input
              type="number"
              value={formData.maxUsers}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                maxUsers: Number(e.target.value)
              }))}
              min={1}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            />
          </div>
          
          <div>
            <label>Max Projects:</label>
            <input
              type="number"
              value={formData.maxProjects}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                maxProjects: Number(e.target.value)
              }))}
              min={1}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            />
          </div>
          
          <div>
            <label>Storage (MB):</label>
            <input
              type="number"
              value={formData.maxStorage}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                maxStorage: Number(e.target.value)
              }))}
              min={1}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
              {Math.round(formData.maxStorage / 1024)}GB
            </div>
          </div>
          
          <div>
            <label>Support Level:</label>
            <select
              value={formData.supportLevel}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                supportLevel: e.target.value as 'basic' | 'priority' | 'premium'
              }))}
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            >
              <option value="basic">Basic</option>
              <option value="priority">Priority</option>
              <option value="premium">Premium</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Options */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Options</h3>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Trial Period (days):</label>
          <input
            type="number"
            value={formData.trialDays}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              trialDays: Number(e.target.value)
            }))}
            min={0}
            max={90}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        
        <div style={{ display: 'flex', gap: '20px' }}>
          <label>
            <input
              type="checkbox"
              checked={formData.isActive}
              onChange={(e) => setFormData(prev => ({ ...prev, isActive: e.target.checked }))}
            />
            <span style={{ marginLeft: '5px' }}>Active immediately</span>
          </label>
          
          <label>
            <input
              type="checkbox"
              checked={formData.isDefault}
              onChange={(e) => setFormData(prev => ({ ...prev, isDefault: e.target.checked }))}
            />
            <span style={{ marginLeft: '5px' }}>Default plan</span>
          </label>
        </div>
      </div>
      
      <button
        type="submit"
        disabled={createPlan.isPending}
        style={{
          padding: '12px 24px',
          backgroundColor: '#2196f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          fontSize: '16px'
        }}
      >
        {createPlan.isPending ? 'Creating Plan...' : 'Create Plan'}
      </button>
    </form>
  );
}
```

#### `useSetDefaultPlan()`

```typescript
function useSetDefaultPlan()
```

**Purpose**: Set a plan as the default

**Cache Invalidation**: Invalidates plans list

**Usage Example**:

```typescript
import { useSetDefaultPlan } from '@/hooks/usePlans';

function SetDefaultButton({ plan }: { plan: Plan }) {
  const setDefault = useSetDefaultPlan();

  const handleSetDefault = () => {
    if (confirm(`Set "${plan.name}" as the default plan?`)) {
      setDefault.mutate(plan.id, {
        onSuccess: () => {
          console.log('Default plan updated');
        }
      });
    }
  };

  return (
    <button
      onClick={handleSetDefault}
      disabled={setDefault.isPending || plan.isDefault}
      style={{
        padding: '6px 12px',
        backgroundColor: plan.isDefault ? '#4caf50' : '#2196f3',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        fontSize: '12px'
      }}
    >
      {setDefault.isPending 
        ? 'Setting...' 
        : plan.isDefault 
          ? 'Default Plan' 
          : 'Set as Default'
      }
    </button>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum PlanErrorType {
  PLAN_NOT_FOUND = 'PLAN_NOT_FOUND',
  PLAN_NAME_EXISTS = 'PLAN_NAME_EXISTS',
  PLAN_HAS_ACTIVE_SUBSCRIPTIONS = 'PLAN_HAS_ACTIVE_SUBSCRIPTIONS',
  INVALID_PRICING = 'INVALID_PRICING',
  FEATURE_NOT_FOUND = 'FEATURE_NOT_FOUND',
  CANNOT_DELETE_DEFAULT_PLAN = 'CANNOT_DELETE_DEFAULT_PLAN',
  CANNOT_DISABLE_DEFAULT_PLAN = 'CANNOT_DISABLE_DEFAULT_PLAN'
}
```

### Validation Error Details

```typescript
interface PlanValidationError {
  field: string;
  message: string;
  code: string;
}

// Example validation errors
const validationErrors = [
  {
    field: 'name',
    message: 'Plan name must be unique',
    code: 'PLAN_NAME_EXISTS'
  },
  {
    field: 'monthlyPrice',
    message: 'Monthly price must be positive',
    code: 'INVALID_MONTHLY_PRICE'
  },
  {
    field: 'yearlyPrice',
    message: 'Yearly price should be less than 12x monthly price',
    code: 'INVALID_YEARLY_DISCOUNT'
  }
];
```

## Business Rules & Constraints

### Plan Creation Rules

1. **Naming**: Plan names must be unique across all plans
2. **Pricing**: Monthly price must be positive, yearly price typically discounted
3. **Features**: At least one feature must be included
4. **Limits**: All limits must be positive integers or -1 for unlimited

### Plan Modification Rules

1. **Active Subscriptions**: Cannot change plan type if plan has active subscriptions
2. **Price Changes**: Price increases require notification period
3. **Feature Removal**: Cannot remove features that existing subscribers depend on
4. **Default Plan**: Cannot delete or disable the default plan

### Usage Statistics Rules

1. **Revenue Calculation**: Based on active subscriptions and pricing
2. **Growth Rates**: Calculated compared to previous period
3. **Lifetime Value**: Average revenue per subscriber over their lifetime

## Integration Examples

### Complete Plan Management Dashboard

```typescript
import React, { useState } from 'react';
import {
  usePlans,
  usePlan,
  useCreatePlan,
  useUpdatePlan,
  useTogglePlan,
  useSetDefaultPlan,
  useDeletePlan
} from '@/hooks/usePlans';

function PlanManagementDashboard() {
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  const {
    data: plans,
    isLoading: plansLoading
  } = usePlans({ includeUsage: true });

  const {
    data: selectedPlan,
    isLoading: planLoading
  } = usePlan(selectedPlanId!, true);

  const togglePlan = useTogglePlan();
  const setDefaultPlan = useSetDefaultPlan();
  const deletePlan = useDeletePlan();

  const handleTogglePlan = (plan: Plan) => {
    togglePlan.mutate({
      id: plan.id,
      action: plan.isActive ? 'disable' : 'enable'
    });
  };

  const handleSetDefault = (planId: string) => {
    setDefaultPlan.mutate(planId);
  };

  const handleDeletePlan = (planId: string, planName: string) => {
    if (confirm(`Are you sure you want to delete "${planName}"?`)) {
      deletePlan.mutate(planId, {
        onSuccess: () => {
          if (selectedPlanId === planId) {
            setSelectedPlanId(null);
          }
        }
      });
    }
  };

  if (plansLoading) return <div>Loading plans...</div>;

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Plans List */}
      <div style={{ width: '60%', padding: '20px', borderRight: '1px solid #ccc', overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1>Subscription Plans ({plans?.pagination.totalCount})</h1>
          <button
            onClick={() => setShowCreateForm(true)}
            style={{ 
              padding: '10px 20px', 
              backgroundColor: '#2196f3', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px' 
            }}
          >
            Create New Plan
          </button>
        </div>

        {/* Plans Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px', marginBottom: '30px' }}>
          {plans?.items.map(plan => (
            <div
              key={plan.id}
              onClick={() => setSelectedPlanId(plan.id)}
              style={{
                border: selectedPlanId === plan.id ? '2px solid #2196f3' : '1px solid #ddd',
                padding: '15px',
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: plan.isActive ? 'white' : '#f5f5f5'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                <div>
                  <h3 style={{ margin: '0 0 5px 0' }}>{plan.name}</h3>
                  <span style={{
                    background: plan.planType === 'basic' ? '#e3f2fd' : 
                               plan.planType === 'pro' ? '#f3e5f5' : '#e8f5e8',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    textTransform: 'uppercase',
                    fontWeight: 'bold'
                  }}>
                    {plan.planType}
                  </span>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {plan.isDefault && (
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '9px',
                      backgroundColor: '#ff9800',
                      color: 'white',
                      textAlign: 'center'
                    }}>
                      DEFAULT
                    </span>
                  )}
                  
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '9px',
                    backgroundColor: plan.isActive ? '#4caf50' : '#757575',
                    color: 'white',
                    textAlign: 'center'
                  }}>
                    {plan.isActive ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>
              </div>
              
              {/* Pricing */}
              <div style={{ marginBottom: '10px' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                  ${(plan.monthlyPrice / 100).toFixed(2)}
                  <span style={{ fontSize: '12px', fontWeight: 'normal', color: '#666' }}>
                    /mo
                  </span>
                </div>
                
                {plan.yearlyPrice && (
                  <div style={{ fontSize: '11px', color: '#666' }}>
                    ${(plan.yearlyPrice / 100).toFixed(2)}/yr 
                    <span style={{ color: '#4caf50', marginLeft: '5px' }}>
                      ({plan.yearlyDiscount}% off)
                    </span>
                  </div>
                )}
              </div>
              
              {/* Key Stats */}
              {plan.usageStats && (
                <div style={{ fontSize: '11px', color: '#666', marginBottom: '10px' }}>
                  <div>📊 {plan.usageStats.activeSubscriptions} active subs</div>
                  <div>💰 ${(plan.usageStats.monthlyRevenue / 100).toFixed(0)}/mo revenue</div>
                </div>
              )}
              
              {/* Quick Limits */}
              <div style={{ fontSize: '10px', color: '#666', marginBottom: '10px' }}>
                👥 {plan.maxUsers === -1 ? '∞' : plan.maxUsers} users • 
                📁 {plan.maxProjects === -1 ? '∞' : plan.maxProjects} projects • 
                🎧 {plan.supportLevel}
              </div>
              
              {/* Actions */}
              <div style={{ display: 'flex', gap: '5px', marginTop: '10px' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTogglePlan(plan);
                  }}
                  style={{
                    padding: '4px 8px',
                    fontSize: '10px',
                    border: 'none',
                    borderRadius: '3px',
                    backgroundColor: plan.isActive ? '#f44336' : '#4caf50',
                    color: 'white'
                  }}
                >
                  {plan.isActive ? 'Disable' : 'Enable'}
                </button>
                
                {!plan.isDefault && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSetDefault(plan.id);
                    }}
                    style={{
                      padding: '4px 8px',
                      fontSize: '10px',
                      border: '1px solid #2196f3',
                      borderRadius: '3px',
                      backgroundColor: 'white',
                      color: '#2196f3'
                    }}
                  >
                    Set Default
                  </button>
                )}
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeletePlan(plan.id, plan.name);
                  }}
                  style={{
                    padding: '4px 8px',
                    fontSize: '10px',
                    border: '1px solid #f44336',
                    borderRadius: '3px',
                    backgroundColor: 'white',
                    color: '#f44336'
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Plan Details */}
      <div style={{ width: '40%', padding: '20px', overflow: 'auto' }}>
        {selectedPlanId ? (
          planLoading ? (
            <div>Loading plan details...</div>
          ) : selectedPlan ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
                <div>
                  <h2>{selectedPlan.name}</h2>
                  <p style={{ color: '#666', margin: '5px 0' }}>{selectedPlan.description}</p>
                </div>
                
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                    ${(selectedPlan.monthlyPrice / 100).toFixed(2)}
                    <span style={{ fontSize: '14px', fontWeight: 'normal' }}>/mo</span>
                  </div>
                  
                  {selectedPlan.yearlyPrice && (
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      ${(selectedPlan.yearlyPrice / 100).toFixed(2)}/yr ({selectedPlan.yearlyDiscount}% off)
                    </div>
                  )}
                </div>
              </div>
              
              {/* Usage Statistics */}
              {selectedPlan.usageStats && (
                <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                  <h3 style={{ margin: '0 0 10px 0' }}>Usage Statistics</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '14px' }}>
                    <div>📊 Active Subscriptions: {selectedPlan.usageStats.activeSubscriptions}</div>
                    <div>📈 Total Subscriptions: {selectedPlan.usageStats.totalSubscriptions}</div>
                    <div>💰 Monthly Revenue: ${(selectedPlan.usageStats.monthlyRevenue / 100).toFixed(2)}</div>
                    <div>💵 Yearly Revenue: ${(selectedPlan.usageStats.yearlyRevenue / 100).toFixed(2)}</div>
                    <div style={{ gridColumn: 'span 2' }}>
                      📈 Avg LTV: ${(selectedPlan.usageStats.averageLifetimeValue / 100).toFixed(2)}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Plan Limits */}
              <div style={{ marginBottom: '20px' }}>
                <h3>Plan Limits</h3>
                <div style={{ display: 'grid', gap: '8px', fontSize: '14px' }}>
                  <div>👥 Users: {selectedPlan.maxUsers === -1 ? 'Unlimited' : selectedPlan.maxUsers}</div>
                  <div>📁 Projects: {selectedPlan.maxProjects === -1 ? 'Unlimited' : selectedPlan.maxProjects}</div>
                  <div>💾 Storage: {selectedPlan.maxStorage === -1 ? 'Unlimited' : `${Math.round(selectedPlan.maxStorage / 1024)}GB`}</div>
                  <div>🎧 Support: {selectedPlan.supportLevel}</div>
                  {selectedPlan.trialDays > 0 && <div>🆓 Trial: {selectedPlan.trialDays} days</div>}
                </div>
              </div>
              
              {/* Features */}
              <div style={{ marginBottom: '20px' }}>
                <h3>Features ({selectedPlan.features.length})</h3>
                <div style={{ display: 'grid', gap: '8px' }}>
                  {selectedPlan.features.map(feature => (
                    <div key={feature.id} style={{ 
                      padding: '8px', 
                      border: '1px solid #ddd', 
                      borderRadius: '4px',
                      fontSize: '13px',
                      backgroundColor: feature.included ? '#f8f9fa' : '#fff3cd'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <strong>{feature.name}</strong>
                          {feature.limit && (
                            <span style={{ color: '#666', marginLeft: '8px' }}>
                              (Limit: {feature.limit === -1 ? 'Unlimited' : feature.limit})
                            </span>
                          )}
                        </div>
                        
                        <span style={{
                          padding: '2px 6px',
                          borderRadius: '10px',
                          fontSize: '10px',
                          backgroundColor: feature.included ? '#4caf50' : '#ff9800',
                          color: 'white'
                        }}>
                          {feature.included ? 'Included' : 'Limited'}
                        </span>
                      </div>
                      
                      <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                        {feature.description}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Metadata */}
              <div style={{ fontSize: '12px', color: '#666' }}>
                <h3>Metadata</h3>
                <div>Created: {new Date(selectedPlan.createdAt).toLocaleString()}</div>
                <div>Last updated: {new Date(selectedPlan.updatedAt).toLocaleString()}</div>
              </div>
            </div>
          ) : (
            <div>Failed to load plan details</div>
          )
        ) : (
          <div style={{ textAlign: 'center', marginTop: '50px', color: '#666' }}>
            Select a plan to view details
          </div>
        )}
      </div>

      {/* Create Form Modal */}
      {showCreateForm && (
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
            maxWidth: '600px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            <h2>Create New Plan</h2>
            {/* Create form component would go here */}
            <button onClick={() => setShowCreateForm(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

## Related Files

- `src/services/planService.ts` - Main service implementation
- `src/hooks/usePlans.ts` - React Query hooks
- `src/types/index.ts` - Type definitions
- `src/components/features/plans/` - Plan management components
- `src/pages/PlansPage.tsx` - Main plans page
- `src/pages/PlanFormPage.tsx` - Create/edit form page