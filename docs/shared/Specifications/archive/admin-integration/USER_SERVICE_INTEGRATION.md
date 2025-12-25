# User Management Service Integration Guide

## Service Overview

- **Service Name**: User Management Service
- **Base URL**: `{config.apiBaseUrl}/admin/users`
- **Primary File**: `src/services/userService.ts`
- **Hook File**: `src/hooks/useUsers.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Get Users List

```http
Method: GET
URL: /admin/users
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
interface UserListParams {
  page?: number;           // Page number (default: 1)
  pageSize?: number;       // Items per page (default: 50)
  search?: string;         // Search by name, email, or tenant
  tenantId?: string;       // Filter by specific tenant
  status?: UserStatus;     // Filter by user status
}

enum UserStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  LOCKED = 'locked',
  INACTIVE = 'inactive'
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<User>> {
  success: boolean;
  data: {
    items: User[];
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

interface User {
  id: string;
  email: string;
  name: string;
  tenantId: string;
  tenantName: string;
  status: UserStatus;
  lastLoginAt: string | null;
  createdAt: string;
  updatedAt: string;
  loginAttempts: number;
  isLocked: boolean;
  lockedUntil: string | null;
}
```

### 2. Get User Details

```http
Method: GET
URL: /admin/users/{userId}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  userId: string;  // User ID
}
```

**Response:**

```typescript
interface UserDetailsResponse extends User {
  activityHistory: UserActivityHistory;
}

interface UserActivityHistory {
  loginHistory: LoginHistoryEntry[];
  featureUsage: FeatureUsageEntry[];
  subscriptionChanges: SubscriptionChangeEntry[];
}

interface LoginHistoryEntry {
  timestamp: string;        // ISO date string
  ipAddress: string;        // Client IP address
  userAgent: string;        // Browser/client info
  success: boolean;         // Login success status
}

interface FeatureUsageEntry {
  feature: string;          // Feature name
  usageCount: number;       // Number of times used
  lastUsedAt: string;       // ISO date string
}

interface SubscriptionChangeEntry {
  timestamp: string;        // ISO date string
  changeType: string;       // Type of change
  details: string;          // Change description
  performedBy: string;      // Admin who made change
}
```

### 3. Unlock User Account

```http
Method: POST
URL: /admin/users/{userId}/unlock
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  userId: string;  // User ID to unlock
}
```

**Request Body:**

```typescript
interface UnlockAccountRequest {
  reason: string;           // Reason for unlocking (required)
  notifyUser?: boolean;     // Send notification to user (default: false)
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

### 4. Suspend User Account

```http
Method: POST
URL: /admin/users/{userId}/suspend
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  userId: string;  // User ID to suspend
}
```

**Request Body:**

```typescript
interface SuspendAccountRequest {
  reason: string;           // Reason for suspension (required)
  notifyUser?: boolean;     // Send notification to user (default: false)
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

### 5. Reactivate User Account

```http
Method: POST
URL: /admin/users/{userId}/reactivate
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  userId: string;  // User ID to reactivate
}
```

**Request Body:**

```typescript
interface ReactivateAccountRequest {
  reason: string;           // Reason for reactivation (required)
  notifyUser?: boolean;     // Send notification to user (default: false)
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

#### `getUsers(params?: UserListParams)`

```typescript
async getUsers(params: UserListParams = {}): Promise<PaginatedResponse<User>>
```

**Purpose**: Fetch paginated list of users with optional filters

**Parameters**:
- `params`: Optional filtering and pagination parameters

**Returns**: Paginated user list

**Error Handling**: Automatic retry with exponential backoff

**Usage Example**:

```typescript
import { userService } from '@/services/userService';

// Get all users (first page)
const users = await userService.getUsers();

// Get users with filters
const filteredUsers = await userService.getUsers({
  page: 2,
  pageSize: 25,
  search: 'john@example.com',
  status: UserStatus.ACTIVE,
  tenantId: 'tenant-123'
});
```

#### `getUserDetails(userId: string)`

```typescript
async getUserDetails(userId: string): Promise<UserDetailsResponse>
```

**Purpose**: Get detailed information for a specific user including activity history

**Parameters**:
- `userId`: User ID

**Returns**: User details with activity history

**Error Handling**: Throws error if user not found or access denied

**Usage Example**:

```typescript
import { userService } from '@/services/userService';

const userDetails = await userService.getUserDetails('user-123');
console.log('Login history:', userDetails.activityHistory.loginHistory);
```

#### `unlockAccount(params: UnlockAccountParams)`

```typescript
async unlockAccount(params: UnlockAccountParams): Promise<void>
```

**Purpose**: Unlock a user account (reset failed login attempts)

**Parameters**:

```typescript
interface UnlockAccountParams {
  userId: string;
  reason: string;
  notifyUser?: boolean;
}
```

**Returns**: void

**Error Handling**: Throws error if user not found or operation fails

**Usage Example**:

```typescript
import { userService } from '@/services/userService';

await userService.unlockAccount({
  userId: 'user-123',
  reason: 'Account locked due to multiple failed login attempts. Verified with user via phone.',
  notifyUser: true
});
```

#### `suspendAccount(params: SuspendAccountParams)`

```typescript
async suspendAccount(params: SuspendAccountParams): Promise<void>
```

**Purpose**: Suspend a user account

**Parameters**:

```typescript
interface SuspendAccountParams {
  userId: string;
  reason: string;
  notifyUser?: boolean;
}
```

**Returns**: void

**Error Handling**: Throws error if user not found or operation fails

**Usage Example**:

```typescript
import { userService } from '@/services/userService';

await userService.suspendAccount({
  userId: 'user-123',
  reason: 'Violation of terms of service. Reported for spam activity.',
  notifyUser: true
});
```

#### `reactivateAccount(params: ReactivateAccountParams)`

```typescript
async reactivateAccount(params: ReactivateAccountParams): Promise<void>
```

**Purpose**: Reactivate a suspended user account

**Parameters**:

```typescript
interface ReactivateAccountParams {
  userId: string;
  reason: string;
  notifyUser?: boolean;
}
```

**Returns**: void

**Error Handling**: Throws error if user not found or operation fails

**Usage Example**:

```typescript
import { userService } from '@/services/userService';

await userService.reactivateAccount({
  userId: 'user-123',
  reason: 'Issue resolved. User has agreed to follow terms of service.',
  notifyUser: true
});
```

## React Query Hooks

### Query Hooks

#### `useUsers(params?: UserListParams)`

```typescript
function useUsers(params: UserListParams = {})
```

**Purpose**: Fetch users with caching and automatic refetching

**Parameters**: Same as `userService.getUsers()`

**Returns**: TanStack Query result with user data

**Cache Key**: `['users', params]`

**Stale Time**: 5 minutes

**Usage Example**:

```typescript
import { useUsers } from '@/hooks/useUsers';

function UserList() {
  const {
    data: users,
    isLoading,
    error,
    refetch
  } = useUsers({
    page: 1,
    pageSize: 50,
    status: UserStatus.ACTIVE
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {users?.items.map(user => (
        <div key={user.id}>{user.name} - {user.email}</div>
      ))}
    </div>
  );
}
```

#### `useUserDetails(userId: string)`

```typescript
function useUserDetails(userId: string)
```

**Purpose**: Fetch detailed user information with activity history

**Parameters**:
- `userId`: User ID

**Returns**: TanStack Query result with user details

**Cache Key**: `['users', userId, 'details']`

**Stale Time**: 2 minutes

**Enabled**: Only when userId is provided

**Usage Example**:

```typescript
import { useUserDetails } from '@/hooks/useUsers';

function UserDetailsPage({ userId }: { userId: string }) {
  const {
    data: userDetails,
    isLoading,
    error
  } = useUserDetails(userId);

  if (isLoading) return <div>Loading user details...</div>;
  if (error) return <div>Error loading user</div>;

  return (
    <div>
      <h1>{userDetails?.name}</h1>
      <p>Status: {userDetails?.status}</p>
      <h2>Recent Logins</h2>
      {userDetails?.activityHistory.loginHistory.map((login, index) => (
        <div key={index}>
          {login.timestamp} - {login.success ? 'Success' : 'Failed'}
        </div>
      ))}
    </div>
  );
}
```

### Mutation Hooks

#### `useUnlockAccount()`

```typescript
function useUnlockAccount()
```

**Purpose**: Unlock user account with optimistic updates

**Returns**: TanStack Query mutation

**Cache Invalidation**: Invalidates user list and user details

**Usage Example**:

```typescript
import { useUnlockAccount } from '@/hooks/useUsers';
import { useToast } from '@/contexts/ToastContext';

function UnlockButton({ userId }: { userId: string }) {
  const unlockAccount = useUnlockAccount();
  const toast = useToast();

  const handleUnlock = () => {
    unlockAccount.mutate({
      userId,
      reason: 'Account unlocked by admin request',
      notifyUser: true
    }, {
      onSuccess: () => {
        toast.showSuccess('Account unlocked successfully');
      },
      onError: (error) => {
        toast.showError(`Failed to unlock account: ${error.message}`);
      }
    });
  };

  return (
    <button
      onClick={handleUnlock}
      disabled={unlockAccount.isPending}
    >
      {unlockAccount.isPending ? 'Unlocking...' : 'Unlock Account'}
    </button>
  );
}
```

#### `useSuspendAccount()`

```typescript
function useSuspendAccount()
```

**Purpose**: Suspend user account with confirmation

**Returns**: TanStack Query mutation

**Cache Invalidation**: Invalidates user list and user details

**Usage Example**:

```typescript
import { useSuspendAccount } from '@/hooks/useUsers';

function SuspendButton({ userId }: { userId: string }) {
  const suspendAccount = useSuspendAccount();

  const handleSuspend = () => {
    const reason = prompt('Enter reason for suspension:');
    if (!reason) return;

    suspendAccount.mutate({
      userId,
      reason,
      notifyUser: true
    });
  };

  return (
    <button onClick={handleSuspend}>
      Suspend Account
    </button>
  );
}
```

#### `useReactivateAccount()`

```typescript
function useReactivateAccount()
```

**Purpose**: Reactivate suspended user account

**Returns**: TanStack Query mutation

**Cache Invalidation**: Invalidates user list and user details

**Usage Example**:

```typescript
import { useReactivateAccount } from '@/hooks/useUsers';

function ReactivateButton({ userId }: { userId: string }) {
  const reactivateAccount = useReactivateAccount();

  const handleReactivate = () => {
    reactivateAccount.mutate({
      userId,
      reason: 'Account reactivated after issue resolution',
      notifyUser: true
    });
  };

  return (
    <button onClick={handleReactivate}>
      Reactivate Account
    </button>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum UserErrorType {
  USER_NOT_FOUND = 'USER_NOT_FOUND',
  ACCESS_DENIED = 'ACCESS_DENIED',
  INVALID_STATUS_TRANSITION = 'INVALID_STATUS_TRANSITION',
  ACCOUNT_ALREADY_ACTIVE = 'ACCOUNT_ALREADY_ACTIVE',
  ACCOUNT_ALREADY_SUSPENDED = 'ACCOUNT_ALREADY_SUSPENDED'
}
```

### Error Response Format

```typescript
interface UserServiceError {
  type: UserErrorType;
  message: string;
  statusCode: number;
  details?: {
    userId?: string;
    currentStatus?: UserStatus;
    requiredRole?: string;
  };
}
```

### Error Handling Patterns

```typescript
import { userService } from '@/services/userService';
import { UserErrorType } from '@/types';

try {
  await userService.suspendAccount({
    userId: 'user-123',
    reason: 'Policy violation'
  });
} catch (error) {
  if (error.type === UserErrorType.USER_NOT_FOUND) {
    showError('User not found');
  } else if (error.type === UserErrorType.ACCOUNT_ALREADY_SUSPENDED) {
    showError('Account is already suspended');
  } else if (error.statusCode === 403) {
    showError('You do not have permission to suspend this user');
  } else {
    showError('Failed to suspend account. Please try again.');
  }
}
```

## Business Rules & Constraints

### User Status Transitions

```typescript
const allowedTransitions = {
  [UserStatus.ACTIVE]: [UserStatus.SUSPENDED, UserStatus.LOCKED],
  [UserStatus.SUSPENDED]: [UserStatus.ACTIVE],
  [UserStatus.LOCKED]: [UserStatus.ACTIVE],
  [UserStatus.INACTIVE]: [UserStatus.ACTIVE]
};
```

### Validation Rules

1. **Reason Required**: All account actions require a reason (minimum 10 characters)
2. **User Exists**: User must exist in the system
3. **Valid Transitions**: Status changes must follow allowed transition rules
4. **Admin Permissions**: Admin must have user management permissions
5. **Tenant Access**: Admin can only manage users in accessible tenants

### Rate Limiting

- **User List**: 100 requests per minute per admin
- **User Details**: 200 requests per minute per admin
- **Account Actions**: 50 actions per minute per admin

## Integration Examples

### Complete User Management Component

```typescript
import React, { useState } from 'react';
import { useUsers, useUserDetails, useSuspendAccount } from '@/hooks/useUsers';
import { UserStatus } from '@/types';

interface UserManagementProps {
  tenantId?: string;
}

function UserManagement({ tenantId }: UserManagementProps) {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 50,
    status: UserStatus.ACTIVE,
    tenantId
  });

  const {
    data: users,
    isLoading: usersLoading,
    error: usersError
  } = useUsers(filters);

  const {
    data: userDetails,
    isLoading: detailsLoading
  } = useUserDetails(selectedUserId!);

  const suspendAccount = useSuspendAccount();

  const handleSuspend = (userId: string) => {
    const reason = prompt('Enter reason for suspension:');
    if (reason) {
      suspendAccount.mutate({
        userId,
        reason,
        notifyUser: true
      });
    }
  };

  if (usersLoading) return <div>Loading users...</div>;
  if (usersError) return <div>Error: {usersError.message}</div>;

  return (
    <div>
      <h1>User Management</h1>
      
      {/* Filters */}
      <div>
        <select
          value={filters.status}
          onChange={(e) => setFilters(prev => ({
            ...prev,
            status: e.target.value as UserStatus
          }))}
        >
          <option value={UserStatus.ACTIVE}>Active</option>
          <option value={UserStatus.SUSPENDED}>Suspended</option>
          <option value={UserStatus.LOCKED}>Locked</option>
        </select>
      </div>

      {/* User List */}
      <div>
        {users?.items.map(user => (
          <div key={user.id}>
            <h3>{user.name}</h3>
            <p>{user.email} - {user.status}</p>
            <button onClick={() => setSelectedUserId(user.id)}>
              View Details
            </button>
            {user.status === UserStatus.ACTIVE && (
              <button onClick={() => handleSuspend(user.id)}>
                Suspend
              </button>
            )}
          </div>
        ))}
      </div>

      {/* User Details */}
      {selectedUserId && (
        <div>
          <h2>User Details</h2>
          {detailsLoading ? (
            <div>Loading details...</div>
          ) : userDetails ? (
            <div>
              <p>Last Login: {userDetails.lastLoginAt || 'Never'}</p>
              <p>Login Attempts: {userDetails.loginAttempts}</p>
              <h3>Recent Activity</h3>
              {userDetails.activityHistory.loginHistory
                .slice(0, 5)
                .map((login, index) => (
                  <div key={index}>
                    {login.timestamp} - {login.success ? 'Success' : 'Failed'}
                  </div>
                ))}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
```

## Related Files

- `src/services/userService.ts` - Main service implementation
- `src/hooks/useUsers.ts` - React Query hooks
- `src/types/index.ts` - Type definitions
- `src/components/features/users/` - User management components
- `src/pages/UsersPage.tsx` - Main users page
- `src/pages/UserDetailsPage.tsx` - User details page