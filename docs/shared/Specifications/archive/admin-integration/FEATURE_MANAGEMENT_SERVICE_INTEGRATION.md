# Feature Management Service Integration Guide

## Service Overview

- **Service Name**: Feature Management Service
- **Base URL**: `{config.apiBaseUrl}/admin/features`
- **Primary File**: `src/services/featureService.ts`
- **Hook File**: `src/hooks/useFeatures.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Get Features List

```http
Method: GET
URL: /admin/features
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
interface FeatureListParams {
  page?: number;                          // Page number (default: 1)
  pageSize?: number;                      // Items per page (default: 50)
  search?: string;                        // Search by name or description
  category?: string;                      // Filter by category
  status?: 'enabled' | 'disabled' | 'all'; // Filter by status (default: 'all')
  scope?: 'global' | 'tenant' | 'user' | 'all'; // Filter by scope
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<Feature>> {
  success: boolean;
  data: {
    items: Feature[];
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

interface Feature {
  id: string;                            // Unique feature ID
  name: string;                          // Feature name
  key: string;                           // Feature key (for code reference)
  description: string;                   // Feature description
  category: string;                      // Feature category
  type: 'boolean' | 'string' | 'number' | 'json'; // Feature value type
  scope: 'global' | 'tenant' | 'user';   // Feature scope
  defaultValue: any;                     // Default value for feature
  currentValue: any;                     // Current global value
  isEnabled: boolean;                    // Whether feature is enabled
  rolloutPercentage: number;             // Gradual rollout percentage (0-100)
  conditions: FeatureCondition[];        // Conditional rules
  dependencies: string[];                // Feature dependencies (other feature IDs)
  tags: string[];                        // Feature tags
  metadata: FeatureMetadata;             // Additional metadata
  createdAt: string;                     // ISO date string
  updatedAt: string;                     // ISO date string
  createdBy: string;                     // Admin who created
  lastModifiedBy: string;                // Admin who last modified
}

interface FeatureCondition {
  id: string;                            // Condition ID
  name: string;                          // Condition name
  type: 'user_attribute' | 'tenant_attribute' | 'date_range' | 'percentage'; // Condition type
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'in' | 'not_in'; // Comparison operator
  attribute?: string;                    // Attribute name for attribute-based conditions
  value: any;                           // Condition value
  isActive: boolean;                     // Whether condition is active
}

interface FeatureMetadata {
  version: string;                       // Feature version
  documentation?: string;                // Documentation URL
  owner?: string;                        // Feature owner/team
  supportLevel: 'experimental' | 'beta' | 'stable' | 'deprecated'; // Support level
  deprecationDate?: string;              // Deprecation date if applicable
  migrationGuide?: string;               // Migration guide URL
  usageStats?: FeatureUsageStats;        // Usage statistics
}

interface FeatureUsageStats {
  totalEvaluations: number;              // Total evaluations
  enabledEvaluations: number;            // Evaluations that returned true
  lastEvaluated: string;                 // Last evaluation timestamp
  topTenants: string[];                  // Top tenants using this feature
  topUsers: string[];                    // Top users using this feature
}
```

### 2. Get Feature Details

```http
Method: GET
URL: /admin/features/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Feature ID
}
```

**Response:**

```typescript
interface ApiResponse<Feature> {
  success: boolean;
  data: Feature;
  error?: string;
}
```

### 3. Create Feature

```http
Method: POST
URL: /admin/features
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface CreateFeatureData {
  name: string;                          // Feature name
  key: string;                           // Feature key (unique, kebab-case)
  description: string;                   // Feature description
  category: string;                      // Feature category
  type: 'boolean' | 'string' | 'number' | 'json'; // Feature value type
  scope: 'global' | 'tenant' | 'user';   // Feature scope
  defaultValue: any;                     // Default value
  isEnabled: boolean;                    // Initial enabled state
  rolloutPercentage: number;             // Initial rollout percentage
  conditions: CreateFeatureCondition[];  // Initial conditions
  dependencies: string[];                // Feature dependencies
  tags: string[];                        // Feature tags
  metadata: {
    owner?: string;
    supportLevel: 'experimental' | 'beta' | 'stable';
    documentation?: string;
  };
}

interface CreateFeatureCondition {
  name: string;
  type: 'user_attribute' | 'tenant_attribute' | 'date_range' | 'percentage';
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'in' | 'not_in';
  attribute?: string;
  value: any;
  isActive: boolean;
}
```

**Response:**

```typescript
interface ApiResponse<Feature> {
  success: boolean;
  data: Feature;
  error?: string;
}
```

### 4. Update Feature

```http
Method: PATCH
URL: /admin/features/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Feature ID
}
```

**Request Body:**

```typescript
interface UpdateFeatureData extends Partial<CreateFeatureData> {
  // All fields from CreateFeatureData are optional for updates
}
```

**Response:**

```typescript
interface ApiResponse<Feature> {
  success: boolean;
  data: Feature;
  error?: string;
}
```

### 5. Toggle Feature

```http
Method: POST
URL: /admin/features/{id}/toggle
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Feature ID
}
```

**Request Body:**

```typescript
interface ToggleFeatureData {
  enabled: boolean;                      // New enabled state
  rolloutPercentage?: number;            // Optional rollout percentage
  reason?: string;                       // Reason for toggle
}
```

**Response:**

```typescript
interface ApiResponse<Feature> {
  success: boolean;
  data: Feature;
  error?: string;
}
```

### 6. Evaluate Feature

```http
Method: POST
URL: /admin/features/{id}/evaluate
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Feature ID
}
```

**Request Body:**

```typescript
interface EvaluateFeatureData {
  context: {
    tenantId?: string;                   // Tenant context
    userId?: string;                     // User context
    userAttributes?: Record<string, any>; // User attributes
    tenantAttributes?: Record<string, any>; // Tenant attributes
  };
}
```

**Response:**

```typescript
interface ApiResponse<FeatureEvaluation> {
  success: boolean;
  data: {
    featureId: string;
    featureKey: string;
    enabled: boolean;                    // Evaluation result
    value: any;                         // Feature value
    reason: string;                     // Reason for result
    conditions: ConditionEvaluation[];  // Condition evaluation details
    metadata: {
      evaluatedAt: string;
      rolloutPercentage: number;
      scopeUsed: string;
    };
  };
  error?: string;
}

interface ConditionEvaluation {
  conditionId: string;
  conditionName: string;
  matched: boolean;
  reason: string;
}
```

### 7. Get Feature Overrides

```http
Method: GET
URL: /admin/features/{id}/overrides
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Feature ID
}
```

**Query Parameters:**

```typescript
{
  page?: number;                         // Page number (default: 1)
  pageSize?: number;                     // Items per page (default: 50)
  scope?: 'tenant' | 'user';             // Override scope
  entityId?: string;                     // Specific entity ID
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<FeatureOverride>> {
  success: boolean;
  data: {
    items: FeatureOverride[];
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

interface FeatureOverride {
  id: string;                            // Override ID
  featureId: string;                     // Feature ID
  scope: 'tenant' | 'user';              // Override scope
  entityId: string;                      // Entity ID (tenant or user)
  entityName: string;                    // Entity name
  value: any;                           // Override value
  enabled: boolean;                      // Override enabled state
  reason?: string;                       // Reason for override
  expiresAt?: string;                    // Expiration date
  createdAt: string;                     // Creation date
  createdBy: string;                     // Admin who created
}
```

### 8. Create Feature Override

```http
Method: POST
URL: /admin/features/{id}/overrides
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Feature ID
}
```

**Request Body:**

```typescript
interface CreateFeatureOverrideData {
  scope: 'tenant' | 'user';              // Override scope
  entityId: string;                      // Entity ID
  value: any;                           // Override value
  enabled: boolean;                      // Override enabled state
  reason?: string;                       // Reason for override
  expiresAt?: string;                    // Optional expiration date
}
```

**Response:**

```typescript
interface ApiResponse<FeatureOverride> {
  success: boolean;
  data: FeatureOverride;
  error?: string;
}
```

### 9. Delete Feature Override

```http
Method: DELETE
URL: /admin/features/{featureId}/overrides/{overrideId}
Authentication: Bearer {access_token}
```

**Path Parameters:**

```typescript
{
  featureId: string;   // Feature ID
  overrideId: string;  // Override ID
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

### 10. Get Feature Analytics

```http
Method: GET
URL: /admin/features/{id}/analytics
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Feature ID
}
```

**Query Parameters:**

```typescript
{
  period?: 'day' | 'week' | 'month';     // Time period (default: 'week')
  startDate?: string;                    // Start date (ISO string)
  endDate?: string;                      // End date (ISO string)
}
```

**Response:**

```typescript
interface ApiResponse<FeatureAnalytics> {
  success: boolean;
  data: {
    featureId: string;
    featureKey: string;
    period: {
      start: string;
      end: string;
    };
    metrics: {
      totalEvaluations: number;
      enabledEvaluations: number;
      enabledPercentage: number;
      uniqueTenants: number;
      uniqueUsers: number;
    };
    timeline: AnalyticsDataPoint[];
    topEntities: {
      tenants: EntityUsage[];
      users: EntityUsage[];
    };
    overrideStats: {
      totalOverrides: number;
      tenantOverrides: number;
      userOverrides: number;
    };
  };
  error?: string;
}

interface AnalyticsDataPoint {
  date: string;
  evaluations: number;
  enabled: number;
  percentage: number;
}

interface EntityUsage {
  entityId: string;
  entityName: string;
  evaluations: number;
  enabledCount: number;
  percentage: number;
}
```

## Service Methods

### Core Methods

#### `getFeatures(params?: FeatureListParams)`

```typescript
async getFeatures(params: FeatureListParams = {}): Promise<PaginatedResponse<Feature>>
```

**Purpose**: Fetch paginated list of features with optional filters

**Parameters**:

- `params`: Optional filtering and pagination parameters

**Returns**: Paginated feature list

**Usage Example**:

```typescript
import { featureService } from '@/services/featureService';

// Get all enabled features
const enabledFeatures = await featureService.getFeatures({
  status: 'enabled',
  pageSize: 25
});

// Search for AI features
const aiFeatures = await featureService.getFeatures({
  search: 'AI',
  category: 'ai-features'
});
```

#### `getFeature(id: string)`

```typescript
async getFeature(id: string): Promise<Feature>
```

**Purpose**: Get feature details by ID

**Parameters**:

- `id`: Feature ID

**Returns**: Complete feature details

**Usage Example**:

```typescript
import { featureService } from '@/services/featureService';

const feature = await featureService.getFeature('feature-123');
console.log(`Feature: ${feature.name}, Enabled: ${feature.isEnabled}`);
```

#### `createFeature(data: CreateFeatureData)`

```typescript
async createFeature(data: CreateFeatureData): Promise<Feature>
```

**Purpose**: Create a new feature flag

**Parameters**:

- `data`: Feature creation data

**Returns**: Created feature

**Validation Rules**:

- Feature key must be unique and kebab-case
- Default value must match specified type
- Dependencies must refer to existing features
- Rollout percentage must be 0-100

**Usage Example**:

```typescript
import { featureService } from '@/services/featureService';

const newFeature = await featureService.createFeature({
  name: 'AI Code Completion',
  key: 'ai-code-completion',
  description: 'Enable AI-powered code completion features',
  category: 'ai-features',
  type: 'boolean',
  scope: 'tenant',
  defaultValue: false,
  isEnabled: true,
  rolloutPercentage: 25, // 25% gradual rollout
  conditions: [
    {
      name: 'Premium Tenants Only',
      type: 'tenant_attribute',
      operator: 'equals',
      attribute: 'planType',
      value: 'premium',
      isActive: true
    }
  ],
  dependencies: ['ai-features-enabled'],
  tags: ['ai', 'productivity', 'beta'],
  metadata: {
    owner: 'ai-team',
    supportLevel: 'beta',
    documentation: 'https://docs.purposepath.com/features/ai-completion'
  }
});
```

#### `toggleFeature(id: string, data: ToggleFeatureData)`

```typescript
async toggleFeature(id: string, data: ToggleFeatureData): Promise<Feature>
```

**Purpose**: Toggle feature enabled state

**Parameters**:

- `id`: Feature ID
- `data`: Toggle parameters

**Returns**: Updated feature

**Business Rules**:

- Disabling a feature with dependencies requires confirmation
- Rollout percentage changes are logged
- Toggle actions are audited

**Usage Example**:

```typescript
import { featureService } from '@/services/featureService';

// Enable feature with gradual rollout
const feature = await featureService.toggleFeature('feature-123', {
  enabled: true,
  rolloutPercentage: 50,
  reason: 'Increasing rollout after successful beta testing'
});
```

#### `evaluateFeature(id: string, context: EvaluateFeatureData)`

```typescript
async evaluateFeature(id: string, context: EvaluateFeatureData): Promise<FeatureEvaluation>
```

**Purpose**: Evaluate feature for specific context

**Parameters**:

- `id`: Feature ID
- `context`: Evaluation context

**Returns**: Feature evaluation result

**Usage Example**:

```typescript
import { featureService } from '@/services/featureService';

const evaluation = await featureService.evaluateFeature('ai-features', {
  context: {
    tenantId: 'tenant-123',
    userId: 'user-456',
    tenantAttributes: { planType: 'premium' },
    userAttributes: { role: 'admin' }
  }
});

console.log(`Feature enabled: ${evaluation.enabled}`);
console.log(`Reason: ${evaluation.reason}`);
```

#### `createOverride(featureId: string, data: CreateFeatureOverrideData)`

```typescript
async createOverride(featureId: string, data: CreateFeatureOverrideData): Promise<FeatureOverride>
```

**Purpose**: Create feature override for specific entity

**Parameters**:

- `featureId`: Feature ID
- `data`: Override creation data

**Returns**: Created override

**Usage Example**:

```typescript
import { featureService } from '@/services/featureService';

// Override feature for specific tenant
const override = await featureService.createOverride('ai-features', {
  scope: 'tenant',
  entityId: 'tenant-123',
  value: true,
  enabled: true,
  reason: 'VIP customer - early access to AI features',
  expiresAt: '2024-12-31T23:59:59.000Z'
});
```

## React Query Hooks

### Query Hooks

#### `useFeatures(params?: FeatureListParams)`

```typescript
function useFeatures(params: FeatureListParams = {})
```

**Purpose**: Fetch features with caching and automatic refetching

**Cache Key**: `['features', params]`

**Stale Time**: 2 minutes

**Usage Example**:

```typescript
import { useFeatures } from '@/hooks/useFeatures';

function FeatureManagement() {
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 20,
    status: 'all' as const,
    category: '',
    scope: 'all' as const
  });

  const {
    data: features,
    isLoading,
    error
  } = useFeatures(filters);

  if (isLoading) return <div>Loading features...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Feature Management ({features?.pagination.totalCount})</h1>
      
      {/* Filters */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '15px' }}>
        <select
          value={filters.status}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            status: e.target.value as 'enabled' | 'disabled' | 'all',
            page: 1 
          }))}
        >
          <option value="all">All Status</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
        </select>
        
        <select
          value={filters.scope}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            scope: e.target.value as 'global' | 'tenant' | 'user' | 'all',
            page: 1 
          }))}
        >
          <option value="all">All Scopes</option>
          <option value="global">Global</option>
          <option value="tenant">Tenant</option>
          <option value="user">User</option>
        </select>
        
        <input
          type="text"
          placeholder="Search features..."
          value={filters.search || ''}
          onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value, page: 1 }))}
          style={{ flex: 1, padding: '8px' }}
        />
      </div>

      {/* Features Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Feature</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Status</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Scope</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Rollout</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Support</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {features?.items.map(feature => (
              <tr key={feature.id}>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{feature.name}</div>
                    <div style={{ fontSize: '12px', color: '#666', fontFamily: 'monospace' }}>
                      {feature.key}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
                      {feature.description}
                    </div>
                    
                    {/* Tags */}
                    {feature.tags.length > 0 && (
                      <div style={{ marginTop: '6px' }}>
                        {feature.tags.slice(0, 3).map(tag => (
                          <span key={tag} style={{
                            padding: '2px 6px',
                            backgroundColor: '#e3f2fd',
                            color: '#1976d2',
                            borderRadius: '12px',
                            fontSize: '10px',
                            marginRight: '4px'
                          }}>
                            #{tag}
                          </span>
                        ))}
                        {feature.tags.length > 3 && (
                          <span style={{ fontSize: '10px', color: '#666' }}>
                            +{feature.tags.length - 3}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    backgroundColor: feature.isEnabled ? '#4caf50' : '#757575',
                    color: 'white'
                  }}>
                    {feature.isEnabled ? 'Enabled' : 'Disabled'}
                  </span>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    backgroundColor: 
                      feature.scope === 'global' ? '#2196f3' :
                      feature.scope === 'tenant' ? '#ff9800' : '#9c27b0',
                    color: 'white'
                  }}>
                    {feature.scope}
                  </span>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      width: '60px',
                      height: '8px',
                      backgroundColor: '#e0e0e0',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${feature.rolloutPercentage}%`,
                        height: '100%',
                        backgroundColor: feature.rolloutPercentage === 100 ? '#4caf50' : '#ff9800'
                      }} />
                    </div>
                    <span style={{ fontSize: '12px' }}>{feature.rolloutPercentage}%</span>
                  </div>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    backgroundColor: 
                      feature.metadata.supportLevel === 'experimental' ? '#f44336' :
                      feature.metadata.supportLevel === 'beta' ? '#ff9800' :
                      feature.metadata.supportLevel === 'stable' ? '#4caf50' : '#757575',
                    color: 'white'
                  }}>
                    {feature.metadata.supportLevel}
                  </span>
                  
                  {feature.dependencies.length > 0 && (
                    <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>
                      {feature.dependencies.length} dependencies
                    </div>
                  )}
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button style={{
                      padding: '4px 8px',
                      fontSize: '10px',
                      backgroundColor: feature.isEnabled ? '#f44336' : '#4caf50',
                      color: 'white',
                      border: 'none',
                      borderRadius: '3px'
                    }}>
                      {feature.isEnabled ? 'Disable' : 'Enable'}
                    </button>
                    
                    <button style={{
                      padding: '4px 8px',
                      fontSize: '10px',
                      backgroundColor: '#2196f3',
                      color: 'white',
                      border: 'none',
                      borderRadius: '3px'
                    }}>
                      Edit
                    </button>
                    
                    <button style={{
                      padding: '4px 8px',
                      fontSize: '10px',
                      backgroundColor: '#ff9800',
                      color: 'white',
                      border: 'none',
                      borderRadius: '3px'
                    }}>
                      Analytics
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          disabled={!features?.pagination.hasPrevious}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
        >
          Previous
        </button>
        <span style={{ margin: '0 15px' }}>
          Page {features?.pagination.page} of {features?.pagination.totalPages}
        </span>
        <button
          disabled={!features?.pagination.hasNext}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

#### `useFeature(id: string)`

```typescript
function useFeature(id: string)
```

**Purpose**: Fetch single feature details

**Cache Key**: `['features', id]`

**Stale Time**: 1 minute

**Usage Example**:

```typescript
import { useFeature } from '@/hooks/useFeatures';

function FeatureDetails({ featureId }: { featureId: string }) {
  const {
    data: feature,
    isLoading,
    error
  } = useFeature(featureId);

  if (isLoading) return <div>Loading feature details...</div>;
  if (error) return <div>Error loading feature</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
        <div>
          <h1>{feature?.name}</h1>
          <div style={{ fontSize: '14px', color: '#666', fontFamily: 'monospace', marginBottom: '8px' }}>
            {feature?.key}
          </div>
          <p style={{ color: '#666' }}>{feature?.description}</p>
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <span style={{
            padding: '8px 16px',
            borderRadius: '4px',
            fontSize: '14px',
            backgroundColor: feature?.isEnabled ? '#4caf50' : '#757575',
            color: 'white'
          }}>
            {feature?.isEnabled ? 'Enabled' : 'Disabled'}
          </span>
          
          <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
            {feature?.rolloutPercentage}% rollout
          </div>
        </div>
      </div>
      
      {/* Feature Configuration */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginBottom: '30px' }}>
        <div>
          <h3>Configuration</h3>
          <div style={{ display: 'grid', gap: '8px', fontSize: '14px' }}>
            <div><strong>Type:</strong> {feature?.type}</div>
            <div><strong>Scope:</strong> {feature?.scope}</div>
            <div><strong>Category:</strong> {feature?.category}</div>
            <div><strong>Default Value:</strong> <code>{JSON.stringify(feature?.defaultValue)}</code></div>
            <div><strong>Current Value:</strong> <code>{JSON.stringify(feature?.currentValue)}</code></div>
          </div>
        </div>
        
        <div>
          <h3>Metadata</h3>
          <div style={{ display: 'grid', gap: '8px', fontSize: '14px' }}>
            <div><strong>Support Level:</strong> {feature?.metadata.supportLevel}</div>
            <div><strong>Owner:</strong> {feature?.metadata.owner || 'N/A'}</div>
            <div><strong>Version:</strong> {feature?.metadata.version}</div>
            {feature?.metadata.documentation && (
              <div>
                <strong>Documentation:</strong> 
                <a href={feature.metadata.documentation} target="_blank" rel="noopener noreferrer">
                  View Docs
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Dependencies */}
      {feature?.dependencies.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h3>Dependencies ({feature.dependencies.length})</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {feature.dependencies.map(depId => (
              <span key={depId} style={{
                padding: '4px 8px',
                backgroundColor: '#f5f5f5',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '12px',
                fontFamily: 'monospace'
              }}>
                {depId}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Conditions */}
      {feature?.conditions.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h3>Conditions ({feature.conditions.length})</h3>
          <div style={{ display: 'grid', gap: '10px' }}>
            {feature.conditions.map(condition => (
              <div key={condition.id} style={{ 
                padding: '12px', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                backgroundColor: condition.isActive ? '#f8f9fa' : '#fff3cd'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <strong>{condition.name}</strong>
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    backgroundColor: condition.isActive ? '#4caf50' : '#ff9800',
                    color: 'white'
                  }}>
                    {condition.isActive ? 'Active' : 'Inactive'}
                  </span>
                </div>
                
                <div style={{ fontSize: '12px', color: '#666' }}>
                  <div>Type: {condition.type}</div>
                  <div>Operator: {condition.operator}</div>
                  {condition.attribute && <div>Attribute: {condition.attribute}</div>}
                  <div>Value: <code>{JSON.stringify(condition.value)}</code></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Usage Statistics */}
      {feature?.metadata.usageStats && (
        <div style={{ marginBottom: '30px' }}>
          <h3>Usage Statistics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
            <div style={{ padding: '12px', border: '1px solid #ddd', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2196f3' }}>
                {feature.metadata.usageStats.totalEvaluations}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Evaluations</div>
            </div>
            
            <div style={{ padding: '12px', border: '1px solid #ddd', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4caf50' }}>
                {feature.metadata.usageStats.enabledEvaluations}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Enabled Results</div>
            </div>
            
            <div style={{ padding: '12px', border: '1px solid #ddd', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff9800' }}>
                {Math.round((feature.metadata.usageStats.enabledEvaluations / feature.metadata.usageStats.totalEvaluations) * 100)}%
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Success Rate</div>
            </div>
          </div>
          
          <div style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
            Last evaluated: {new Date(feature.metadata.usageStats.lastEvaluated).toLocaleString()}
          </div>
        </div>
      )}
      
      {/* Tags */}
      {feature?.tags.length > 0 && (
        <div>
          <h3>Tags</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {feature.tags.map(tag => (
              <span key={tag} style={{
                padding: '4px 8px',
                backgroundColor: '#e3f2fd',
                color: '#1976d2',
                borderRadius: '12px',
                fontSize: '12px'
              }}>
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

### Mutation Hooks

#### `useToggleFeature()`

```typescript
function useToggleFeature()
```

**Purpose**: Toggle feature enabled state with cache invalidation

**Cache Invalidation**: Invalidates features list and individual feature

**Usage Example**:

```typescript
import { useToggleFeature } from '@/hooks/useFeatures';

function FeatureToggle({ feature }: { feature: Feature }) {
  const toggleFeature = useToggleFeature();

  const handleToggle = () => {
    const newState = !feature.isEnabled;
    const action = newState ? 'enable' : 'disable';
    
    if (confirm(`Are you sure you want to ${action} "${feature.name}"?`)) {
      toggleFeature.mutate({
        id: feature.id,
        enabled: newState,
        reason: `Manual ${action} from admin panel`
      }, {
        onSuccess: () => {
          console.log(`Feature ${action}d successfully`);
        }
      });
    }
  };

  return (
    <button
      onClick={handleToggle}
      disabled={toggleFeature.isPending}
      style={{
        padding: '8px 16px',
        backgroundColor: feature.isEnabled ? '#f44336' : '#4caf50',
        color: 'white',
        border: 'none',
        borderRadius: '4px'
      }}
    >
      {toggleFeature.isPending 
        ? 'Processing...' 
        : feature.isEnabled 
          ? 'Disable' 
          : 'Enable'
      }
    </button>
  );
}
```

#### `useCreateFeature()`

```typescript
function useCreateFeature()
```

**Purpose**: Create new feature with cache invalidation

**Cache Invalidation**: Invalidates features list

**Usage Example**:

```typescript
import { useCreateFeature } from '@/hooks/useFeatures';
import { useToast } from '@/contexts/ToastContext';

function CreateFeatureForm() {
  const [formData, setFormData] = useState({
    name: '',
    key: '',
    description: '',
    category: '',
    type: 'boolean' as const,
    scope: 'tenant' as const,
    defaultValue: false,
    isEnabled: false,
    rolloutPercentage: 0,
    conditions: [],
    dependencies: [],
    tags: [],
    metadata: {
      supportLevel: 'experimental' as const,
      owner: '',
      documentation: ''
    }
  });

  const createFeature = useCreateFeature();
  const toast = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    createFeature.mutate(formData, {
      onSuccess: (newFeature) => {
        toast.showSuccess(`Feature "${newFeature.name}" created successfully`);
        // Reset form or navigate away
      },
      onError: (error) => {
        toast.showError(`Failed to create feature: ${error.message}`);
      }
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '600px' }}>
      <h2>Create Feature Flag</h2>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Feature Name:</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => {
            const name = e.target.value;
            const key = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            setFormData(prev => ({ ...prev, name, key }));
          }}
          required
          style={{ width: '100%', padding: '8px', marginTop: '5px' }}
        />
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Feature Key:</label>
        <input
          type="text"
          value={formData.key}
          onChange={(e) => setFormData(prev => ({ ...prev, key: e.target.value }))}
          required
          pattern="[a-z0-9-]+"
          title="Only lowercase letters, numbers, and hyphens"
          style={{ width: '100%', padding: '8px', marginTop: '5px', fontFamily: 'monospace' }}
        />
        <small style={{ color: '#666' }}>Used in code to reference this feature</small>
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
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
        <div>
          <label>Type:</label>
          <select
            value={formData.type}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              type: e.target.value as 'boolean' | 'string' | 'number' | 'json',
              defaultValue: e.target.value === 'boolean' ? false : 
                           e.target.value === 'number' ? 0 : ''
            }))}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          >
            <option value="boolean">Boolean</option>
            <option value="string">String</option>
            <option value="number">Number</option>
            <option value="json">JSON</option>
          </select>
        </div>
        
        <div>
          <label>Scope:</label>
          <select
            value={formData.scope}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              scope: e.target.value as 'global' | 'tenant' | 'user'
            }))}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          >
            <option value="global">Global</option>
            <option value="tenant">Tenant</option>
            <option value="user">User</option>
          </select>
        </div>
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Default Value:</label>
        {formData.type === 'boolean' ? (
          <select
            value={formData.defaultValue.toString()}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              defaultValue: e.target.value === 'true'
            }))}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          >
            <option value="false">False</option>
            <option value="true">True</option>
          </select>
        ) : (
          <input
            type={formData.type === 'number' ? 'number' : 'text'}
            value={formData.defaultValue}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              defaultValue: formData.type === 'number' ? Number(e.target.value) : e.target.value
            }))}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        )}
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Initial Rollout Percentage:</label>
        <input
          type="range"
          min="0"
          max="100"
          value={formData.rolloutPercentage}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            rolloutPercentage: Number(e.target.value)
          }))}
          style={{ width: '100%', marginTop: '5px' }}
        />
        <div style={{ textAlign: 'center', fontSize: '14px', marginTop: '5px' }}>
          {formData.rolloutPercentage}%
        </div>
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label>
          <input
            type="checkbox"
            checked={formData.isEnabled}
            onChange={(e) => setFormData(prev => ({ ...prev, isEnabled: e.target.checked }))}
          />
          <span style={{ marginLeft: '5px' }}>Enable immediately</span>
        </label>
      </div>
      
      <button
        type="submit"
        disabled={createFeature.isPending}
        style={{
          padding: '12px 24px',
          backgroundColor: '#2196f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          fontSize: '16px'
        }}
      >
        {createFeature.isPending ? 'Creating Feature...' : 'Create Feature Flag'}
      </button>
    </form>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum FeatureErrorType {
  FEATURE_NOT_FOUND = 'FEATURE_NOT_FOUND',
  FEATURE_KEY_EXISTS = 'FEATURE_KEY_EXISTS',
  INVALID_FEATURE_TYPE = 'INVALID_FEATURE_TYPE',
  CIRCULAR_DEPENDENCY = 'CIRCULAR_DEPENDENCY',
  DEPENDENCY_NOT_FOUND = 'DEPENDENCY_NOT_FOUND',
  INVALID_CONDITION = 'INVALID_CONDITION',
  OVERRIDE_CONFLICT = 'OVERRIDE_CONFLICT'
}
```

### Validation Error Details

```typescript
interface FeatureValidationError {
  field: string;
  message: string;
  code: string;
  details?: any;
}

// Example validation errors
const validationErrors = [
  {
    field: 'key',
    message: 'Feature key must be unique',
    code: 'FEATURE_KEY_EXISTS',
    details: { existingFeatureId: 'feature-123' }
  },
  {
    field: 'dependencies',
    message: 'Circular dependency detected',
    code: 'CIRCULAR_DEPENDENCY',
    details: { cycle: ['feature-a', 'feature-b', 'feature-a'] }
  }
];
```

## Business Rules & Constraints

### Feature Creation Rules

1. **Unique Keys**: Feature keys must be unique across all features
2. **Key Format**: Keys must be kebab-case (lowercase with hyphens)
3. **Type Validation**: Default values must match specified type
4. **Dependencies**: Dependencies must refer to existing features
5. **No Circular Dependencies**: Feature dependency chains cannot be circular

### Feature Management Rules

1. **Rollout Percentage**: Must be between 0-100
2. **Scope Inheritance**: User scope can override tenant scope, tenant can override global
3. **Condition Evaluation**: Conditions are evaluated in order with AND logic
4. **Override Priority**: Overrides take precedence over default evaluation

### Performance Rules

1. **Evaluation Caching**: Feature evaluations are cached for performance
2. **Condition Complexity**: Limit number of conditions per feature
3. **Dependency Depth**: Limit dependency chain depth
4. **Rollout Changes**: Gradual rollout changes to prevent system overload

## Integration Examples

### Complete Feature Flag Management System

```typescript
import React, { useState } from 'react';
import {
  useFeatures,
  useFeature,
  useCreateFeature,
  useToggleFeature,
  useFeatureOverrides,
  useCreateOverride
} from '@/hooks/useFeatures';

function FeatureFlagManagement() {
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('features');
  
  const { data: features, isLoading } = useFeatures();
  const { data: selectedFeature } = useFeature(selectedFeatureId!);
  const { data: overrides } = useFeatureOverrides(selectedFeatureId!);

  if (isLoading) return <div>Loading features...</div>;

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '20px', borderBottom: '1px solid #ccc' }}>
        <h1>Feature Flag Management</h1>
        
        {/* Tab Navigation */}
        <div style={{ marginTop: '15px' }}>
          {['features', 'overrides', 'analytics'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '8px 16px',
                marginRight: '5px',
                border: 'none',
                borderRadius: '4px 4px 0 0',
                backgroundColor: activeTab === tab ? '#2196f3' : '#f5f5f5',
                color: activeTab === tab ? 'white' : '#333'
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>
      
      <div style={{ flex: 1, display: 'flex' }}>
        {/* Features List */}
        <div style={{ width: '40%', padding: '20px', borderRight: '1px solid #ccc', overflow: 'auto' }}>
          <div style={{ marginBottom: '20px' }}>
            <h2>Features ({features?.pagination.totalCount})</h2>
          </div>
          
          {features?.items.map(feature => (
            <div
              key={feature.id}
              onClick={() => setSelectedFeatureId(feature.id)}
              style={{
                border: selectedFeatureId === feature.id ? '2px solid #2196f3' : '1px solid #ddd',
                padding: '12px',
                marginBottom: '8px',
                borderRadius: '6px',
                cursor: 'pointer',
                backgroundColor: feature.isEnabled ? 'white' : '#f9f9f9'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <h4 style={{ margin: '0 0 4px 0' }}>{feature.name}</h4>
                  <div style={{ fontSize: '11px', fontFamily: 'monospace', color: '#666', marginBottom: '4px' }}>
                    {feature.key}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {feature.description}
                  </div>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '3px',
                    fontSize: '9px',
                    backgroundColor: feature.isEnabled ? '#4caf50' : '#757575',
                    color: 'white',
                    textAlign: 'center'
                  }}>
                    {feature.isEnabled ? 'ON' : 'OFF'}
                  </span>
                  
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '3px',
                    fontSize: '9px',
                    backgroundColor: '#2196f3',
                    color: 'white',
                    textAlign: 'center'
                  }}>
                    {feature.rolloutPercentage}%
                  </span>
                </div>
              </div>
              
              <div style={{ marginTop: '8px', fontSize: '10px', color: '#666' }}>
                {feature.scope} • {feature.type} • {feature.metadata.supportLevel}
                {feature.conditions.length > 0 && ` • ${feature.conditions.length} conditions`}
              </div>
            </div>
          ))}
        </div>
        
        {/* Details Panel */}
        <div style={{ flex: 1, padding: '20px', overflow: 'auto' }}>
          {selectedFeatureId && selectedFeature ? (
            <div>
              {activeTab === 'features' && (
                <FeatureDetailsPanel feature={selectedFeature} />
              )}
              
              {activeTab === 'overrides' && (
                <FeatureOverridesPanel featureId={selectedFeatureId} overrides={overrides} />
              )}
              
              {activeTab === 'analytics' && (
                <FeatureAnalyticsPanel featureId={selectedFeatureId} />
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', marginTop: '50px', color: '#666' }}>
              Select a feature to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Individual panels would be implemented as separate components
function FeatureDetailsPanel({ feature }) {
  return <div>Feature Details Panel Implementation</div>;
}

function FeatureOverridesPanel({ featureId, overrides }) {
  return <div>Feature Overrides Panel Implementation</div>;
}

function FeatureAnalyticsPanel({ featureId }) {
  return <div>Feature Analytics Panel Implementation</div>;
}
```

## Related Files

- `src/services/featureService.ts` - Main service implementation
- `src/hooks/useFeatures.ts` - React Query hooks
- `src/types/index.ts` - Type definitions
- `src/components/features/featureFlags/` - Feature flag components
- `src/pages/FeatureFlagsPage.tsx` - Main feature flags page
- `src/pages/FeatureEditorPage.tsx` - Feature editor page