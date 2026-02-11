# Discount Code Service Integration Guide

## Service Overview

- **Service Name**: Discount Code Service
- **Base URL**: `{config.apiBaseUrl}/admin/discount-codes`
- **Primary File**: `src/services/discountCodeService.ts`
- **Hook File**: `src/hooks/useDiscountCodes.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Get Discount Codes List

```http
Method: GET
URL: /admin/discount-codes
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
interface DiscountCodeListParams {
  page?: number;                          // Page number (default: 1)
  pageSize?: number;                      // Items per page (default: 50)
  search?: string;                        // Search by code name or description
  status?: 'active' | 'inactive' | 'all'; // Filter by status (default: 'all')
  discountType?: 'percentage' | 'fixed_amount' | 'all'; // Filter by type
  applicability?: 'new_tenants' | 'renewals' | 'all';   // Filter by applicability
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<DiscountCode>> {
  success: boolean;
  data: {
    items: DiscountCode[];
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

interface DiscountCode {
  id: string;                            // Unique discount code ID
  codeName: string;                      // Discount code (e.g., "SAVE20")
  description: string;                   // Human-readable description
  discountType: 'percentage' | 'fixed_amount'; // Type of discount
  discountValue: number;                 // Percentage (1-100) or amount in cents
  applicability: 'new_tenants' | 'renewals' | 'all'; // When code can be used
  applicableTiers: string[];             // Tier IDs where code applies
  isSystemWide: boolean;                 // Applies to all tiers if true
  tenantRestrictions: string[];          // Specific tenant IDs (if restricted)
  expiresAt: string | null;              // ISO date string or null (no expiration)
  usageLimit: number | null;             // Max uses or null (unlimited)
  usageCount: number;                    // Current usage count
  isActive: boolean;                     // Whether code is active
  createdAt: string;                     // ISO date string
  updatedAt: string;                     // ISO date string
  createdBy: string;                     // Admin who created the code
}
```

### 2. Get Discount Code Details

```http
Method: GET
URL: /admin/discount-codes/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Discount code ID
}
```

**Response:**

```typescript
interface ApiResponse<DiscountCode> {
  success: boolean;
  data: DiscountCode;
  error?: string;
}
```

### 3. Get Discount Code Usage History

```http
Method: GET
URL: /admin/discount-codes/{id}/usage
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Discount code ID
}
```

**Query Parameters:**

```typescript
{
  page?: number;      // Page number (default: 1)
  pageSize?: number;  // Items per page (default: 50)
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<DiscountCodeUsage>> {
  success: boolean;
  data: {
    items: DiscountCodeUsage[];
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

interface DiscountCodeUsage {
  id: string;
  tenantId: string;
  tenantName: string;
  usedAt: string;                        // ISO date string
  usedBy: string;                        // User who applied the code
  discountApplied: number;               // Actual discount amount (in cents)
  originalAmount: number;                // Original amount before discount
  finalAmount: number;                   // Final amount after discount
  subscriptionType: 'new' | 'renewal';  // Type of subscription
  invoiceId?: string;                    // Associated invoice ID
}
```

### 4. Create Discount Code

```http
Method: POST
URL: /admin/discount-codes
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface CreateDiscountCodeData {
  codeName: string;                      // Unique code name (uppercase, alphanumeric + hyphens)
  description: string;                   // Description of the discount
  discountType: 'percentage' | 'fixed_amount'; // Type of discount
  discountValue: number;                 // Percentage (1-100) or amount in cents
  applicability: 'new_tenants' | 'renewals' | 'all'; // When code can be used
  applicableTiers: string[];             // Tier IDs (empty = all tiers)
  isSystemWide: boolean;                 // Applies to all tiers
  tenantRestrictions: string[];          // Specific tenant restrictions
  expiresAt: string | null;              // Expiration date or null
  usageLimit: number | null;             // Usage limit or null (unlimited)
  isActive: boolean;                     // Whether code starts active
}
```

**Response:**

```typescript
interface ApiResponse<DiscountCode> {
  success: boolean;
  data: DiscountCode;
  error?: string;
}
```

### 5. Update Discount Code

```http
Method: PATCH
URL: /admin/discount-codes/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Discount code ID
}
```

**Request Body:**

```typescript
interface UpdateDiscountCodeData extends Partial<CreateDiscountCodeData> {
  // All fields from CreateDiscountCodeData are optional for updates
}
```

**Response:**

```typescript
interface ApiResponse<DiscountCode> {
  success: boolean;
  data: DiscountCode;
  error?: string;
}
```

### 6. Enable/Disable Discount Code

```http
Method: POST
URL: /admin/discount-codes/{id}/enable
URL: /admin/discount-codes/{id}/disable
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Discount code ID
}
```

**Response:**

```typescript
interface ApiResponse<DiscountCode> {
  success: boolean;
  data: DiscountCode;
  error?: string;
}
```

### 7. Delete Discount Code

```http
Method: DELETE
URL: /admin/discount-codes/{id}
Authentication: Bearer {access_token}
```

**Path Parameters:**

```typescript
{
  id: string;  // Discount code ID
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

### 8. Validate Discount Code

```http
Method: POST
URL: /admin/discount-codes/validate
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface ValidateDiscountCodeParams {
  codeName: string;      // Code to validate
  tenantId?: string;     // Optional tenant context
}
```

**Response:**

```typescript
interface ApiResponse<DiscountCodeValidationResult> {
  success: boolean;
  data: {
    valid: boolean;
    reason?: string;       // Reason if invalid
    code?: DiscountCode;   // Full code details if valid
  };
  error?: string;
}
```

## Service Methods

### Core Methods

#### `getDiscountCodes(params?: DiscountCodeListParams)`

```typescript
async getDiscountCodes(params: DiscountCodeListParams = {}): Promise<PaginatedResponse<DiscountCode>>
```

**Purpose**: Fetch paginated list of discount codes with optional filters

**Parameters**:

- `params`: Optional filtering and pagination parameters

**Returns**: Paginated discount code list

**Usage Example**:

```typescript
import { discountCodeService } from '@/services/discountCodeService';

// Get all active discount codes
const activeCodes = await discountCodeService.getDiscountCodes({
  status: 'active',
  pageSize: 25
});

// Search for specific codes
const searchResults = await discountCodeService.getDiscountCodes({
  search: 'SAVE',
  discountType: 'percentage'
});
```

#### `getDiscountCode(id: string)`

```typescript
async getDiscountCode(id: string): Promise<DiscountCode>
```

**Purpose**: Get discount code details by ID

**Parameters**:

- `id`: Discount code ID

**Returns**: Complete discount code details

**Usage Example**:

```typescript
import { discountCodeService } from '@/services/discountCodeService';

const code = await discountCodeService.getDiscountCode('code-123');
console.log(`Code: ${code.codeName}, Value: ${code.discountValue}%`);
```

#### `createDiscountCode(data: CreateDiscountCodeData)`

```typescript
async createDiscountCode(data: CreateDiscountCodeData): Promise<DiscountCode>
```

**Purpose**: Create a new discount code

**Parameters**:

- `data`: Discount code creation data

**Returns**: Created discount code

**Validation Rules**:

- Code name must be unique and uppercase
- Percentage discounts: 1-100
- Fixed amount discounts: positive integers (cents)
- At least one applicable tier (unless system-wide)

**Usage Example**:

```typescript
import { discountCodeService } from '@/services/discountCodeService';

const newCode = await discountCodeService.createDiscountCode({
  codeName: 'SUMMER2024',
  description: 'Summer 2024 promotion - 25% off all plans',
  discountType: 'percentage',
  discountValue: 25,
  applicability: 'new_tenants',
  applicableTiers: ['basic', 'pro'],
  isSystemWide: false,
  tenantRestrictions: [],
  expiresAt: '2024-08-31T23:59:59.000Z',
  usageLimit: 1000,
  isActive: true
});
```

#### `updateDiscountCode(id: string, data: UpdateDiscountCodeData)`

```typescript
async updateDiscountCode(id: string, data: UpdateDiscountCodeData): Promise<DiscountCode>
```

**Purpose**: Update existing discount code

**Parameters**:

- `id`: Discount code ID
- `data`: Fields to update

**Returns**: Updated discount code

**Business Rules**:

- Cannot change code name after creation
- Cannot reduce usage limit below current usage
- Cannot change discount value if code has been used

**Usage Example**:

```typescript
import { discountCodeService } from '@/services/discountCodeService';

const updatedCode = await discountCodeService.updateDiscountCode('code-123', {
  description: 'Updated description',
  expiresAt: '2024-12-31T23:59:59.000Z',
  usageLimit: 2000
});
```

#### `validateDiscountCode(params: ValidateDiscountCodeParams)`

```typescript
async validateDiscountCode(params: ValidateDiscountCodeParams): Promise<DiscountCodeValidationResult>
```

**Purpose**: Validate if a discount code can be used

**Parameters**:

- `params`: Validation parameters

**Returns**: Validation result with details

**Validation Checks**:

- Code exists and is active
- Not expired
- Usage limit not exceeded
- Tenant restrictions respected
- Tier compatibility

**Usage Example**:

```typescript
import { discountCodeService } from '@/services/discountCodeService';

const validation = await discountCodeService.validateDiscountCode({
  codeName: 'SAVE20',
  tenantId: 'tenant-123'
});

if (validation.valid) {
  console.log('Code is valid:', validation.code);
} else {
  console.log('Code invalid:', validation.reason);
}
```

## React Query Hooks

### Query Hooks

#### `useDiscountCodes(params?: DiscountCodeListParams)`

```typescript
function useDiscountCodes(params: DiscountCodeListParams = {})
```

**Purpose**: Fetch discount codes with caching and automatic refetching

**Cache Key**: `['discountCodes', params]`

**Stale Time**: 5 minutes

**Usage Example**:

```typescript
import { useDiscountCodes } from '@/hooks/useDiscountCodes';

function DiscountCodeList() {
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 50,
    status: 'all' as const,
    discountType: 'all' as const
  });

  const {
    data: codes,
    isLoading,
    error
  } = useDiscountCodes(filters);

  if (isLoading) return <div>Loading discount codes...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Discount Codes ({codes?.pagination.totalCount})</h1>
      
      {/* Filters */}
      <div style={{ marginBottom: '20px' }}>
        <select
          value={filters.status}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            status: e.target.value as 'active' | 'inactive' | 'all' 
          }))}
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        
        <select
          value={filters.discountType}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            discountType: e.target.value as 'percentage' | 'fixed_amount' | 'all'
          }))}
        >
          <option value="all">All Types</option>
          <option value="percentage">Percentage</option>
          <option value="fixed_amount">Fixed Amount</option>
        </select>
      </div>

      {/* Code Cards */}
      <div style={{ display: 'grid', gap: '15px' }}>
        {codes?.items.map(code => (
          <div key={code.id} style={{ 
            border: '1px solid #ddd', 
            padding: '15px', 
            borderRadius: '8px',
            backgroundColor: code.isActive ? 'white' : '#f5f5f5'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <h3 style={{ margin: '0 0 8px 0' }}>{code.codeName}</h3>
                <p style={{ margin: '0 0 8px 0', color: '#666' }}>{code.description}</p>
                
                <div style={{ fontSize: '14px' }}>
                  <span style={{ 
                    background: code.discountType === 'percentage' ? '#e3f2fd' : '#f3e5f5',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    marginRight: '8px'
                  }}>
                    {code.discountType === 'percentage' 
                      ? `${code.discountValue}% off`
                      : `$${(code.discountValue / 100).toFixed(2)} off`
                    }
                  </span>
                  
                  <span style={{ color: '#666' }}>
                    {code.applicability} • {code.usageCount}/{code.usageLimit || '∞'} uses
                  </span>
                </div>
                
                {code.expiresAt && (
                  <div style={{ fontSize: '12px', color: '#f57c00', marginTop: '4px' }}>
                    Expires: {new Date(code.expiresAt).toLocaleDateString()}
                  </div>
                )}
              </div>
              
              <div style={{ display: 'flex', gap: '8px' }}>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  backgroundColor: code.isActive ? '#4caf50' : '#757575',
                  color: 'white'
                }}>
                  {code.isActive ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          disabled={!codes?.pagination.hasPrevious}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
        >
          Previous
        </button>
        <span style={{ margin: '0 15px' }}>
          Page {codes?.pagination.page} of {codes?.pagination.totalPages}
        </span>
        <button
          disabled={!codes?.pagination.hasNext}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

#### `useDiscountCode(id: string)`

```typescript
function useDiscountCode(id: string)
```

**Purpose**: Fetch single discount code details

**Cache Key**: `['discountCodes', id]`

**Stale Time**: 2 minutes

**Usage Example**:

```typescript
import { useDiscountCode } from '@/hooks/useDiscountCodes';

function DiscountCodeDetails({ codeId }: { codeId: string }) {
  const {
    data: code,
    isLoading,
    error
  } = useDiscountCode(codeId);

  if (isLoading) return <div>Loading code details...</div>;
  if (error) return <div>Error loading code</div>;

  return (
    <div>
      <h1>{code?.codeName}</h1>
      <p>{code?.description}</p>
      
      <div>
        <h3>Details</h3>
        <p>Type: {code?.discountType}</p>
        <p>Value: {code?.discountValue}</p>
        <p>Applicability: {code?.applicability}</p>
        <p>Usage: {code?.usageCount} / {code?.usageLimit || 'Unlimited'}</p>
        <p>Status: {code?.isActive ? 'Active' : 'Inactive'}</p>
        
        {code?.expiresAt && (
          <p>Expires: {new Date(code.expiresAt).toLocaleString()}</p>
        )}
      </div>
      
      {code?.applicableTiers.length > 0 && (
        <div>
          <h3>Applicable Tiers</h3>
          <ul>
            {code.applicableTiers.map(tier => (
              <li key={tier}>{tier}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

### Mutation Hooks

#### `useCreateDiscountCode()`

```typescript
function useCreateDiscountCode()
```

**Purpose**: Create new discount code with cache invalidation

**Cache Invalidation**: Invalidates discount codes list

**Usage Example**:

```typescript
import { useCreateDiscountCode } from '@/hooks/useDiscountCodes';
import { useToast } from '@/contexts/ToastContext';

function CreateDiscountCodeForm() {
  const [formData, setFormData] = useState({
    codeName: '',
    description: '',
    discountType: 'percentage' as const,
    discountValue: 0,
    applicability: 'new_tenants' as const,
    applicableTiers: [] as string[],
    isSystemWide: false,
    tenantRestrictions: [] as string[],
    expiresAt: '',
    usageLimit: null as number | null,
    isActive: true
  });

  const createCode = useCreateDiscountCode();
  const toast = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const data = {
      ...formData,
      expiresAt: formData.expiresAt || null,
      codeName: formData.codeName.toUpperCase()
    };
    
    createCode.mutate(data, {
      onSuccess: (newCode) => {
        toast.showSuccess(`Discount code "${newCode.codeName}" created successfully`);
        // Reset form or navigate away
      },
      onError: (error) => {
        toast.showError(`Failed to create discount code: ${error.message}`);
      }
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Create Discount Code</h2>
      
      <div>
        <label>Code Name:</label>
        <input
          type="text"
          value={formData.codeName}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            codeName: e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, '')
          }))}
          pattern="[A-Z0-9-]+"
          title="Only uppercase letters, numbers, and hyphens allowed"
          required
        />
      </div>
      
      <div>
        <label>Description:</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          required
        />
      </div>
      
      <div>
        <label>Discount Type:</label>
        <select
          value={formData.discountType}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            discountType: e.target.value as 'percentage' | 'fixed_amount'
          }))}
        >
          <option value="percentage">Percentage</option>
          <option value="fixed_amount">Fixed Amount</option>
        </select>
      </div>
      
      <div>
        <label>
          {formData.discountType === 'percentage' ? 'Percentage (1-100):' : 'Amount ($):'}
        </label>
        <input
          type="number"
          value={formData.discountValue}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            discountValue: Number(e.target.value)
          }))}
          min={formData.discountType === 'percentage' ? 1 : 0}
          max={formData.discountType === 'percentage' ? 100 : undefined}
          step={formData.discountType === 'percentage' ? 1 : 0.01}
          required
        />
      </div>
      
      <div>
        <label>Applicability:</label>
        <select
          value={formData.applicability}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            applicability: e.target.value as 'new_tenants' | 'renewals' | 'all'
          }))}
        >
          <option value="new_tenants">New Tenants Only</option>
          <option value="renewals">Renewals Only</option>
          <option value="all">All Subscriptions</option>
        </select>
      </div>
      
      <div>
        <label>Expiration Date (optional):</label>
        <input
          type="datetime-local"
          value={formData.expiresAt}
          onChange={(e) => setFormData(prev => ({ ...prev, expiresAt: e.target.value }))}
        />
      </div>
      
      <div>
        <label>Usage Limit (optional):</label>
        <input
          type="number"
          value={formData.usageLimit || ''}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            usageLimit: e.target.value ? Number(e.target.value) : null
          }))}
          min={1}
          placeholder="Unlimited"
        />
      </div>
      
      <div>
        <label>
          <input
            type="checkbox"
            checked={formData.isActive}
            onChange={(e) => setFormData(prev => ({ ...prev, isActive: e.target.checked }))}
          />
          Active immediately
        </label>
      </div>
      
      <button
        type="submit"
        disabled={createCode.isPending}
      >
        {createCode.isPending ? 'Creating...' : 'Create Discount Code'}
      </button>
    </form>
  );
}
```

#### `useToggleDiscountCode()`

```typescript
function useToggleDiscountCode()
```

**Purpose**: Enable/disable discount codes

**Cache Invalidation**: Invalidates codes list and individual code

**Usage Example**:

```typescript
import { useToggleDiscountCode } from '@/hooks/useDiscountCodes';

function DiscountCodeToggle({ code }: { code: DiscountCode }) {
  const toggleCode = useToggleDiscountCode();

  const handleToggle = () => {
    const action = code.isActive ? 'disable' : 'enable';
    
    toggleCode.mutate({
      id: code.id,
      action
    }, {
      onSuccess: () => {
        console.log(`Code ${action}d successfully`);
      }
    });
  };

  return (
    <button
      onClick={handleToggle}
      disabled={toggleCode.isPending}
      style={{
        backgroundColor: code.isActive ? '#f44336' : '#4caf50',
        color: 'white',
        border: 'none',
        padding: '8px 16px',
        borderRadius: '4px'
      }}
    >
      {toggleCode.isPending 
        ? 'Processing...' 
        : code.isActive 
          ? 'Disable' 
          : 'Enable'
      }
    </button>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum DiscountCodeErrorType {
  CODE_NOT_FOUND = 'CODE_NOT_FOUND',
  CODE_NAME_EXISTS = 'CODE_NAME_EXISTS',
  INVALID_DISCOUNT_VALUE = 'INVALID_DISCOUNT_VALUE',
  CODE_EXPIRED = 'CODE_EXPIRED',
  USAGE_LIMIT_EXCEEDED = 'USAGE_LIMIT_EXCEEDED',
  TENANT_RESTRICTED = 'TENANT_RESTRICTED',
  TIER_NOT_APPLICABLE = 'TIER_NOT_APPLICABLE',
  CODE_INACTIVE = 'CODE_INACTIVE'
}
```

### Validation Error Details

```typescript
interface DiscountCodeValidationError {
  field: string;
  message: string;
  code: string;
}

// Example validation errors
const validationErrors = [
  {
    field: 'codeName',
    message: 'Code name must be unique',
    code: 'CODE_NAME_EXISTS'
  },
  {
    field: 'discountValue',
    message: 'Percentage must be between 1 and 100',
    code: 'INVALID_PERCENTAGE_RANGE'
  },
  {
    field: 'expiresAt',
    message: 'Expiration date must be in the future',
    code: 'INVALID_EXPIRATION_DATE'
  }
];
```

## Business Rules & Constraints

### Code Name Rules

1. **Format**: Uppercase letters, numbers, and hyphens only
2. **Length**: 3-20 characters
3. **Uniqueness**: Must be unique across all codes
4. **Immutable**: Cannot be changed after creation

### Discount Value Rules

1. **Percentage**: 1-100% range
2. **Fixed Amount**: Positive integers in cents
3. **Immutable**: Cannot be changed if code has been used

### Usage & Expiration Rules

1. **Usage Limit**: Optional, once reached code becomes invalid
2. **Expiration**: Optional, codes without expiration never expire
3. **Tenant Restrictions**: Optional, restricts to specific tenants
4. **Tier Restrictions**: Codes can be limited to specific subscription tiers

## Integration Examples

### Complete Discount Code Management

```typescript
import React, { useState } from 'react';
import {
  useDiscountCodes,
  useDiscountCode,
  useCreateDiscountCode,
  useUpdateDiscountCode,
  useToggleDiscountCode,
  useDeleteDiscountCode
} from '@/hooks/useDiscountCodes';

function DiscountCodeManagement() {
  const [selectedCodeId, setSelectedCodeId] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  const {
    data: codes,
    isLoading: codesLoading
  } = useDiscountCodes();

  const {
    data: selectedCode,
    isLoading: codeLoading
  } = useDiscountCode(selectedCodeId!);

  const createCode = useCreateDiscountCode();
  const toggleCode = useToggleDiscountCode();
  const deleteCode = useDeleteDiscountCode();

  const handleCreateCode = (data: CreateDiscountCodeData) => {
    createCode.mutate(data, {
      onSuccess: () => {
        setShowCreateForm(false);
      }
    });
  };

  const handleToggleCode = (code: DiscountCode) => {
    toggleCode.mutate({
      id: code.id,
      action: code.isActive ? 'disable' : 'enable'
    });
  };

  const handleDeleteCode = (codeId: string) => {
    if (confirm('Are you sure you want to delete this discount code?')) {
      deleteCode.mutate(codeId, {
        onSuccess: () => {
          if (selectedCodeId === codeId) {
            setSelectedCodeId(null);
          }
        }
      });
    }
  };

  if (codesLoading) return <div>Loading discount codes...</div>;

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Codes List */}
      <div style={{ width: '60%', padding: '20px', borderRight: '1px solid #ccc' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1>Discount Codes ({codes?.pagination.totalCount})</h1>
          <button
            onClick={() => setShowCreateForm(true)}
            style={{ padding: '10px 20px', backgroundColor: '#2196f3', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            Create New Code
          </button>
        </div>

        <div>
          {codes?.items.map(code => (
            <div
              key={code.id}
              onClick={() => setSelectedCodeId(code.id)}
              style={{
                border: '1px solid #ddd',
                padding: '15px',
                marginBottom: '10px',
                cursor: 'pointer',
                borderRadius: '8px',
                backgroundColor: selectedCodeId === code.id ? '#f0f8ff' : 'white'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: '0 0 8px 0' }}>{code.codeName}</h3>
                  <p style={{ margin: '0 0 8px 0', color: '#666', fontSize: '14px' }}>
                    {code.description}
                  </p>
                  
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <span style={{
                      background: code.discountType === 'percentage' ? '#e3f2fd' : '#f3e5f5',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '12px'
                    }}>
                      {code.discountType === 'percentage' 
                        ? `${code.discountValue}% off`
                        : `$${(code.discountValue / 100).toFixed(2)} off`
                      }
                    </span>
                    
                    <span style={{
                      background: '#f5f5f5',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '12px'
                    }}>
                      {code.applicability}
                    </span>
                    
                    <span style={{
                      background: code.isActive ? '#e8f5e8' : '#f5f5f5',
                      color: code.isActive ? '#2e7d32' : '#757575',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '12px'
                    }}>
                      {code.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                    Uses: {code.usageCount}/{code.usageLimit || '∞'}
                    {code.expiresAt && (
                      <span> • Expires: {new Date(code.expiresAt).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleCode(code);
                    }}
                    style={{
                      padding: '4px 8px',
                      fontSize: '12px',
                      border: 'none',
                      borderRadius: '4px',
                      backgroundColor: code.isActive ? '#f44336' : '#4caf50',
                      color: 'white'
                    }}
                  >
                    {code.isActive ? 'Disable' : 'Enable'}
                  </button>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteCode(code.id);
                    }}
                    style={{
                      padding: '4px 8px',
                      fontSize: '12px',
                      border: '1px solid #f44336',
                      borderRadius: '4px',
                      backgroundColor: 'white',
                      color: '#f44336'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Code Details */}
      <div style={{ width: '40%', padding: '20px' }}>
        {selectedCodeId ? (
          codeLoading ? (
            <div>Loading details...</div>
          ) : selectedCode ? (
            <div>
              <h2>{selectedCode.codeName}</h2>
              <p>{selectedCode.description}</p>
              
              <div style={{ marginBottom: '20px' }}>
                <h3>Discount Details</h3>
                <p>Type: {selectedCode.discountType}</p>
                <p>Value: {selectedCode.discountType === 'percentage' 
                  ? `${selectedCode.discountValue}%`
                  : `$${(selectedCode.discountValue / 100).toFixed(2)}`
                }</p>
                <p>Applicability: {selectedCode.applicability}</p>
              </div>
              
              <div style={{ marginBottom: '20px' }}>
                <h3>Usage & Expiration</h3>
                <p>Usage: {selectedCode.usageCount} / {selectedCode.usageLimit || 'Unlimited'}</p>
                <p>Status: {selectedCode.isActive ? 'Active' : 'Inactive'}</p>
                {selectedCode.expiresAt && (
                  <p>Expires: {new Date(selectedCode.expiresAt).toLocaleString()}</p>
                )}
              </div>
              
              {selectedCode.applicableTiers.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h3>Applicable Tiers</h3>
                  <ul>
                    {selectedCode.applicableTiers.map(tier => (
                      <li key={tier}>{tier}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div>
                <h3>Metadata</h3>
                <p>Created: {new Date(selectedCode.createdAt).toLocaleString()}</p>
                <p>Created by: {selectedCode.createdBy}</p>
                <p>Last updated: {new Date(selectedCode.updatedAt).toLocaleString()}</p>
              </div>
            </div>
          ) : (
            <div>Failed to load code details</div>
          )
        ) : (
          <div style={{ textAlign: 'center', marginTop: '50px', color: '#666' }}>
            Select a discount code to view details
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
            maxWidth: '500px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            <h2>Create Discount Code</h2>
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

- `src/services/discountCodeService.ts` - Main service implementation
- `src/hooks/useDiscountCodes.ts` - React Query hooks
- `src/types/index.ts` - Type definitions
- `src/components/features/discountCodes/` - Discount code components
- `src/pages/DiscountCodesPage.tsx` - Main discount codes page
- `src/pages/DiscountCodeFormPage.tsx` - Create/edit form page