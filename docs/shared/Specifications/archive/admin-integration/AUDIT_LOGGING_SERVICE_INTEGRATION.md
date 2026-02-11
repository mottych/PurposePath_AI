# Audit Logging Service Integration Guide

## Service Overview

- **Service Name**: Audit Logging Service
- **Base URL**: `{config.apiBaseUrl}/admin/audit-logs`
- **Primary File**: `src/services/auditLogService.ts`
- **Hook File**: `src/hooks/useAuditLogs.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Get Audit Logs List

```http
Method: GET
URL: /admin/audit-logs
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
interface AuditLogListParams {
  page?: number;                          // Page number (default: 1)
  pageSize?: number;                      // Items per page (default: 50)
  search?: string;                        // Search by action, resource, or details
  dateFrom?: string;                      // Start date filter (ISO string)
  dateTo?: string;                        // End date filter (ISO string)
  actionType?: string;                    // Filter by action type
  resourceType?: string;                  // Filter by resource type
  userId?: string;                        // Filter by user ID
  adminId?: string;                       // Filter by admin ID
  severity?: 'low' | 'medium' | 'high' | 'critical'; // Filter by severity
  status?: 'success' | 'failed' | 'pending'; // Filter by status
  sortBy?: 'timestamp' | 'action' | 'resource' | 'severity'; // Sort field
  sortOrder?: 'asc' | 'desc';             // Sort order (default: desc)
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<AuditLog>> {
  success: boolean;
  data: {
    items: AuditLog[];
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

interface AuditLog {
  id: string;                            // Unique audit log ID
  timestamp: string;                     // ISO date string
  action: string;                        // Action performed
  actionType: AuditActionType;           // Categorized action type
  resourceType: string;                  // Type of resource affected
  resourceId: string;                    // ID of affected resource
  resourceName?: string;                 // Name/title of affected resource
  adminId: string;                       // Admin who performed action
  adminName: string;                     // Admin's display name
  adminEmail: string;                    // Admin's email
  userId?: string;                       // Affected user ID (if applicable)
  userName?: string;                     // Affected user name
  userEmail?: string;                    // Affected user email
  tenantId?: string;                     // Affected tenant ID (if applicable)
  tenantName?: string;                   // Affected tenant name
  severity: 'low' | 'medium' | 'high' | 'critical'; // Action severity
  status: 'success' | 'failed' | 'pending'; // Action status
  details: AuditLogDetails;              // Detailed information
  metadata: AuditLogMetadata;            // Additional metadata
  ipAddress: string;                     // Admin's IP address
  userAgent: string;                     // Admin's user agent
  sessionId: string;                     // Admin's session ID
  correlationId?: string;                // Correlation ID for related actions
}

enum AuditActionType {
  CREATE = 'CREATE',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
  VIEW = 'VIEW',
  LOGIN = 'LOGIN',
  LOGOUT = 'LOGOUT',
  EXPORT = 'EXPORT',
  IMPORT = 'IMPORT',
  APPROVE = 'APPROVE',
  REJECT = 'REJECT',
  SUSPEND = 'SUSPEND',
  RESTORE = 'RESTORE',
  GRANT_ACCESS = 'GRANT_ACCESS',
  REVOKE_ACCESS = 'REVOKE_ACCESS',
  FEATURE_TOGGLE = 'FEATURE_TOGGLE',
  SYSTEM_CONFIG = 'SYSTEM_CONFIG'
}

interface AuditLogDetails {
  description: string;                   // Human-readable description
  changes?: FieldChange[];               // Field changes for updates
  oldValues?: Record<string, any>;       // Previous values
  newValues?: Record<string, any>;       // New values
  affectedFields?: string[];             // List of affected fields
  reason?: string;                       // Reason for action
  additionalContext?: Record<string, any>; // Additional context data
  errorMessage?: string;                 // Error message if action failed
  requestData?: any;                     // Original request data
  responseData?: any;                    // Response data
}

interface FieldChange {
  field: string;                         // Field name
  oldValue: any;                         // Previous value
  newValue: any;                         // New value
  dataType: string;                      // Data type of field
}

interface AuditLogMetadata {
  source: 'admin_panel' | 'api' | 'system' | 'bulk_operation'; // Action source
  version: string;                       // Application version
  apiVersion?: string;                   // API version used
  batchId?: string;                      // Batch ID for bulk operations
  duration?: number;                     // Action duration in milliseconds
  retryCount?: number;                   // Number of retry attempts
  flags?: string[];                      // Special flags or tags
}
```

### 2. Get Audit Log Details

```http
Method: GET
URL: /admin/audit-logs/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Audit log ID
}
```

**Response:**

```typescript
interface ApiResponse<AuditLog> {
  success: boolean;
  data: AuditLog;
  error?: string;
}
```

### 3. Export Audit Logs

```http
Method: POST
URL: /admin/audit-logs/export
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface ExportAuditLogsData {
  filters: AuditLogListParams;           // Export filters
  format: 'csv' | 'json' | 'xlsx';       // Export format
  includeFields?: string[];              // Specific fields to include
  excludeFields?: string[];              // Fields to exclude
  includeDetails?: boolean;              // Include detailed information
  reason?: string;                       // Reason for export
}
```

**Response:**

```typescript
interface ApiResponse<ExportResult> {
  success: boolean;
  data: {
    exportId: string;                    // Export job ID
    status: 'pending' | 'processing' | 'completed' | 'failed'; // Export status
    downloadUrl?: string;                // Download URL when completed
    fileName: string;                    // Generated file name
    recordCount: number;                 // Number of records exported
    estimatedSize: string;               // Estimated file size
    expiresAt: string;                   // Download URL expiration
    createdAt: string;                   // Export creation time
  };
  error?: string;
}
```

### 4. Get Export Status

```http
Method: GET
URL: /admin/audit-logs/export/{exportId}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  exportId: string;  // Export job ID
}
```

**Response:**

```typescript
interface ApiResponse<ExportResult> {
  success: boolean;
  data: ExportResult;
  error?: string;
}
```

### 5. Get Audit Statistics

```http
Method: GET
URL: /admin/audit-logs/statistics
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
{
  period?: 'day' | 'week' | 'month' | 'quarter' | 'year'; // Time period (default: 'month')
  dateFrom?: string;                     // Custom start date
  dateTo?: string;                       // Custom end date
  groupBy?: 'action' | 'resource' | 'admin' | 'severity'; // Grouping field
}
```

**Response:**

```typescript
interface ApiResponse<AuditStatistics> {
  success: boolean;
  data: {
    period: {
      start: string;
      end: string;
    };
    summary: {
      totalLogs: number;
      successfulActions: number;
      failedActions: number;
      uniqueAdmins: number;
      uniqueUsers: number;
      uniqueResources: number;
    };
    actionBreakdown: ActionStatistic[];
    resourceBreakdown: ResourceStatistic[];
    adminActivity: AdminActivity[];
    severityDistribution: SeverityDistribution;
    timeline: TimelineDataPoint[];
    trends: {
      actionsPerDay: number;
      failureRate: number;
      trendDirection: 'up' | 'down' | 'stable';
      comparisonPeriod: string;
    };
  };
  error?: string;
}

interface ActionStatistic {
  actionType: AuditActionType;
  count: number;
  percentage: number;
  successRate: number;
}

interface ResourceStatistic {
  resourceType: string;
  count: number;
  percentage: number;
  mostCommonActions: string[];
}

interface AdminActivity {
  adminId: string;
  adminName: string;
  adminEmail: string;
  actionCount: number;
  lastActivity: string;
  mostCommonActions: string[];
}

interface SeverityDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

interface TimelineDataPoint {
  date: string;
  totalActions: number;
  successfulActions: number;
  failedActions: number;
  uniqueAdmins: number;
}
```

### 6. Get Related Logs

```http
Method: GET
URL: /admin/audit-logs/{id}/related
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Base audit log ID
}
```

**Query Parameters:**

```typescript
{
  relationshipType?: 'correlation' | 'resource' | 'admin' | 'session'; // Relationship type
  timeWindow?: number;                   // Time window in minutes (default: 60)
  limit?: number;                        // Maximum related logs (default: 20)
}
```

**Response:**

```typescript
interface ApiResponse<RelatedLogsResult> {
  success: boolean;
  data: {
    baseLog: AuditLog;                   // Original audit log
    relatedLogs: RelatedAuditLog[];      // Related logs
    relationshipSummary: {
      correlationMatches: number;        // Logs with same correlation ID
      resourceMatches: number;           // Logs for same resource
      adminMatches: number;              // Logs by same admin
      sessionMatches: number;            // Logs in same session
    };
  };
  error?: string;
}

interface RelatedAuditLog extends AuditLog {
  relationshipType: 'correlation' | 'resource' | 'admin' | 'session';
  relationshipStrength: number;         // 0-1 relationship strength
  timeDifference: number;               // Minutes from base log
}
```

### 7. Create Manual Audit Log

```http
Method: POST
URL: /admin/audit-logs
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface CreateAuditLogData {
  action: string;                        // Action description
  actionType: AuditActionType;           // Action type
  resourceType: string;                  // Resource type
  resourceId: string;                    // Resource ID
  resourceName?: string;                 // Resource name
  userId?: string;                       // Affected user ID
  tenantId?: string;                     // Affected tenant ID
  severity: 'low' | 'medium' | 'high' | 'critical'; // Severity level
  details: {
    description: string;                 // Detailed description
    reason?: string;                     // Reason for action
    additionalContext?: Record<string, any>; // Additional context
  };
  correlationId?: string;                // Correlation ID
}
```

**Response:**

```typescript
interface ApiResponse<AuditLog> {
  success: boolean;
  data: AuditLog;
  error?: string;
}
```

### 8. Bulk Delete Audit Logs

```http
Method: DELETE
URL: /admin/audit-logs/bulk
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface BulkDeleteAuditLogsData {
  criteria: {
    olderThan?: string;                  // Delete logs older than date
    actionTypes?: AuditActionType[];     // Delete specific action types
    severity?: ('low' | 'medium' | 'high' | 'critical')[]; // Delete specific severities
    resourceTypes?: string[];            // Delete specific resource types
  };
  dryRun?: boolean;                      // Perform dry run without deletion
  reason: string;                        // Reason for bulk deletion
}
```

**Response:**

```typescript
interface ApiResponse<BulkDeleteResult> {
  success: boolean;
  data: {
    deletedCount: number;                // Number of logs deleted
    affectedRecords: string[];           // IDs of affected records
    estimatedCount?: number;             // Estimated count for dry run
    executionTime: number;               // Execution time in milliseconds
    deletionReason: string;              // Reason for deletion
  };
  error?: string;
}
```

## Service Methods

### Core Methods

#### `getAuditLogs(params?: AuditLogListParams)`

```typescript
async getAuditLogs(params: AuditLogListParams = {}): Promise<PaginatedResponse<AuditLog>>
```

**Purpose**: Fetch paginated list of audit logs with optional filters

**Parameters**:

- `params`: Optional filtering and pagination parameters

**Returns**: Paginated audit logs list

**Usage Example**:

```typescript
import { auditLogService } from '@/services/auditLogService';

// Get recent high-severity logs
const criticalLogs = await auditLogService.getAuditLogs({
  severity: 'critical',
  pageSize: 25,
  sortBy: 'timestamp',
  sortOrder: 'desc'
});

// Get logs for specific user
const userLogs = await auditLogService.getAuditLogs({
  userId: 'user-123',
  dateFrom: '2024-01-01T00:00:00.000Z',
  dateTo: '2024-01-31T23:59:59.999Z'
});
```

#### `getAuditLog(id: string)`

```typescript
async getAuditLog(id: string): Promise<AuditLog>
```

**Purpose**: Get audit log details by ID

**Parameters**:

- `id`: Audit log ID

**Returns**: Complete audit log details

**Usage Example**:

```typescript
import { auditLogService } from '@/services/auditLogService';

const auditLog = await auditLogService.getAuditLog('log-123');
console.log(`Action: ${auditLog.action} by ${auditLog.adminName}`);
```

#### `exportAuditLogs(data: ExportAuditLogsData)`

```typescript
async exportAuditLogs(data: ExportAuditLogsData): Promise<ExportResult>
```

**Purpose**: Export audit logs to file

**Parameters**:

- `data`: Export configuration

**Returns**: Export job details

**Usage Example**:

```typescript
import { auditLogService } from '@/services/auditLogService';

const exportJob = await auditLogService.exportAuditLogs({
  filters: {
    dateFrom: '2024-01-01T00:00:00.000Z',
    dateTo: '2024-01-31T23:59:59.999Z',
    severity: 'high'
  },
  format: 'xlsx',
  includeDetails: true,
  reason: 'Monthly compliance report'
});

console.log(`Export job ${exportJob.exportId} created`);
```

#### `getAuditStatistics(params: StatisticsParams)`

```typescript
async getAuditStatistics(params: StatisticsParams): Promise<AuditStatistics>
```

**Purpose**: Get audit log statistics and analytics

**Parameters**:

- `params`: Statistics parameters

**Returns**: Comprehensive audit statistics

**Usage Example**:

```typescript
import { auditLogService } from '@/services/auditLogService';

const stats = await auditLogService.getAuditStatistics({
  period: 'month',
  groupBy: 'action'
});

console.log(`Total logs: ${stats.summary.totalLogs}`);
console.log(`Success rate: ${((stats.summary.successfulActions / stats.summary.totalLogs) * 100).toFixed(1)}%`);
```

#### `createManualAuditLog(data: CreateAuditLogData)`

```typescript
async createManualAuditLog(data: CreateAuditLogData): Promise<AuditLog>
```

**Purpose**: Create manual audit log entry

**Parameters**:

- `data`: Audit log creation data

**Returns**: Created audit log

**Usage Example**:

```typescript
import { auditLogService } from '@/services/auditLogService';

const auditLog = await auditLogService.createManualAuditLog({
  action: 'Manual Data Correction',
  actionType: AuditActionType.UPDATE,
  resourceType: 'user',
  resourceId: 'user-123',
  resourceName: 'John Doe',
  severity: 'medium',
  details: {
    description: 'Manually corrected user email address due to typo',
    reason: 'Customer support request #12345',
    additionalContext: {
      supportTicket: '12345',
      requestedBy: 'customer',
      approvedBy: 'manager'
    }
  }
});
```

## React Query Hooks

### Query Hooks

#### `useAuditLogs(params?: AuditLogListParams)`

```typescript
function useAuditLogs(params: AuditLogListParams = {})
```

**Purpose**: Fetch audit logs with caching and automatic refetching

**Cache Key**: `['auditLogs', params]`

**Stale Time**: 30 seconds

**Usage Example**:

```typescript
import { useAuditLogs } from '@/hooks/useAuditLogs';

function AuditLogsDashboard() {
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 50,
    severity: undefined,
    actionType: undefined,
    dateFrom: undefined,
    dateTo: undefined,
    search: ''
  });

  const {
    data: auditLogs,
    isLoading,
    error
  } = useAuditLogs(filters);

  if (isLoading) return <div>Loading audit logs...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Audit Logs ({auditLogs?.pagination.totalCount})</h1>
      
      {/* Filters */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
        <select
          value={filters.severity || ''}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            severity: e.target.value || undefined,
            page: 1 
          }))}
        >
          <option value="">All Severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        
        <select
          value={filters.actionType || ''}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            actionType: e.target.value || undefined,
            page: 1 
          }))}
        >
          <option value="">All Actions</option>
          <option value="CREATE">Create</option>
          <option value="UPDATE">Update</option>
          <option value="DELETE">Delete</option>
          <option value="LOGIN">Login</option>
          <option value="LOGOUT">Logout</option>
        </select>
        
        <input
          type="date"
          value={filters.dateFrom?.split('T')[0] || ''}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            dateFrom: e.target.value ? `${e.target.value}T00:00:00.000Z` : undefined,
            page: 1 
          }))}
          placeholder="From Date"
        />
        
        <input
          type="date"
          value={filters.dateTo?.split('T')[0] || ''}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            dateTo: e.target.value ? `${e.target.value}T23:59:59.999Z` : undefined,
            page: 1 
          }))}
          placeholder="To Date"
        />
        
        <input
          type="text"
          placeholder="Search logs..."
          value={filters.search}
          onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value, page: 1 }))}
          style={{ flex: 1, minWidth: '200px', padding: '8px' }}
        />
      </div>

      {/* Audit Logs Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Timestamp</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Action</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Admin</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Resource</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Severity</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Status</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Details</th>
            </tr>
          </thead>
          <tbody>
            {auditLogs?.items.map(log => (
              <tr key={log.id} style={{ backgroundColor: log.status === 'failed' ? '#fff5f5' : 'white' }}>
                <td style={{ padding: '12px', border: '1px solid #ddd', fontSize: '12px' }}>
                  <div>{new Date(log.timestamp).toLocaleDateString()}</div>
                  <div style={{ color: '#666' }}>
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{log.action}</div>
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    backgroundColor: '#e3f2fd',
                    color: '#1976d2'
                  }}>
                    {log.actionType}
                  </span>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '12px' }}>{log.adminName}</div>
                  <div style={{ fontSize: '11px', color: '#666' }}>{log.adminEmail}</div>
                  <div style={{ fontSize: '10px', color: '#999', marginTop: '2px' }}>
                    IP: {log.ipAddress}
                  </div>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div style={{ fontSize: '12px' }}>
                    <strong>{log.resourceType}</strong>
                  </div>
                  {log.resourceName && (
                    <div style={{ fontSize: '11px', color: '#666', marginBottom: '2px' }}>
                      {log.resourceName}
                    </div>
                  )}
                  <div style={{ fontSize: '10px', color: '#999', fontFamily: 'monospace' }}>
                    {log.resourceId}
                  </div>
                  
                  {/* Affected User/Tenant */}
                  {log.userName && (
                    <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                      User: {log.userName}
                    </div>
                  )}
                  {log.tenantName && (
                    <div style={{ fontSize: '10px', color: '#666' }}>
                      Tenant: {log.tenantName}
                    </div>
                  )}
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: 
                      log.severity === 'critical' ? '#d32f2f' :
                      log.severity === 'high' ? '#f57c00' :
                      log.severity === 'medium' ? '#fbc02d' : '#388e3c',
                    color: 'white'
                  }}>
                    {log.severity.toUpperCase()}
                  </span>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    backgroundColor: 
                      log.status === 'success' ? '#4caf50' :
                      log.status === 'failed' ? '#f44336' : '#ff9800',
                    color: 'white'
                  }}>
                    {log.status.toUpperCase()}
                  </span>
                </td>
                
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div style={{ fontSize: '12px', maxWidth: '200px' }}>
                    {log.details.description}
                  </div>
                  
                  {log.details.reason && (
                    <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                      Reason: {log.details.reason}
                    </div>
                  )}
                  
                  {log.details.changes && log.details.changes.length > 0 && (
                    <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                      {log.details.changes.length} field(s) changed
                    </div>
                  )}
                  
                  {log.correlationId && (
                    <div style={{ 
                      fontSize: '9px', 
                      color: '#999', 
                      fontFamily: 'monospace',
                      marginTop: '4px'
                    }}>
                      ID: {log.correlationId.slice(0, 8)}...
                    </div>
                  )}
                  
                  <button style={{
                    marginTop: '6px',
                    padding: '2px 6px',
                    fontSize: '9px',
                    backgroundColor: '#2196f3',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    cursor: 'pointer'
                  }}>
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          disabled={!auditLogs?.pagination.hasPrevious}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
          style={{ marginRight: '10px' }}
        >
          Previous
        </button>
        <span style={{ margin: '0 15px' }}>
          Page {auditLogs?.pagination.page} of {auditLogs?.pagination.totalPages}
        </span>
        <button
          disabled={!auditLogs?.pagination.hasNext}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

#### `useAuditStatistics(params: StatisticsParams)`

```typescript
function useAuditStatistics(params: StatisticsParams)
```

**Purpose**: Fetch audit log statistics and analytics

**Cache Key**: `['auditStatistics', params]`

**Stale Time**: 5 minutes

**Usage Example**:

```typescript
import { useAuditStatistics } from '@/hooks/useAuditLogs';

function AuditAnalyticsDashboard() {
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('month');
  
  const {
    data: statistics,
    isLoading,
    error
  } = useAuditStatistics({ period });

  if (isLoading) return <div>Loading analytics...</div>;
  if (error) return <div>Error loading analytics</div>;

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h1>Audit Analytics Dashboard</h1>
        
        {/* Period Selector */}
        <div style={{ marginTop: '10px' }}>
          {['day', 'week', 'month'].map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p as any)}
              style={{
                padding: '8px 16px',
                marginRight: '5px',
                backgroundColor: period === p ? '#2196f3' : '#f5f5f5',
                color: period === p ? 'white' : '#333',
                border: 'none',
                borderRadius: '4px'
              }}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#2196f3', marginBottom: '8px' }}>
            {statistics?.summary.totalLogs.toLocaleString()}
          </div>
          <div style={{ color: '#666' }}>Total Actions</div>
        </div>
        
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#4caf50', marginBottom: '8px' }}>
            {statistics?.summary.successfulActions.toLocaleString()}
          </div>
          <div style={{ color: '#666' }}>Successful</div>
        </div>
        
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f44336', marginBottom: '8px' }}>
            {statistics?.summary.failedActions.toLocaleString()}
          </div>
          <div style={{ color: '#666' }}>Failed</div>
        </div>
        
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#ff9800', marginBottom: '8px' }}>
            {statistics && Math.round((statistics.summary.successfulActions / statistics.summary.totalLogs) * 100)}%
          </div>
          <div style={{ color: '#666' }}>Success Rate</div>
        </div>
        
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#9c27b0', marginBottom: '8px' }}>
            {statistics?.summary.uniqueAdmins}
          </div>
          <div style={{ color: '#666' }}>Active Admins</div>
        </div>
      </div>

      {/* Charts Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginBottom: '30px' }}>
        {/* Action Breakdown */}
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
          <h3>Action Breakdown</h3>
          <div style={{ display: 'grid', gap: '8px' }}>
            {statistics?.actionBreakdown.slice(0, 5).map(action => (
              <div key={action.actionType} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '14px' }}>{action.actionType}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ 
                    width: '100px', 
                    height: '8px', 
                    backgroundColor: '#e0e0e0', 
                    borderRadius: '4px', 
                    overflow: 'hidden' 
                  }}>
                    <div style={{ 
                      width: `${action.percentage}%`, 
                      height: '100%', 
                      backgroundColor: '#2196f3' 
                    }} />
                  </div>
                  <span style={{ fontSize: '12px', minWidth: '40px' }}>
                    {action.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Severity Distribution */}
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
          <h3>Severity Distribution</h3>
          <div style={{ display: 'grid', gap: '8px' }}>
            {[
              { level: 'Critical', count: statistics?.severityDistribution.critical, color: '#d32f2f' },
              { level: 'High', count: statistics?.severityDistribution.high, color: '#f57c00' },
              { level: 'Medium', count: statistics?.severityDistribution.medium, color: '#fbc02d' },
              { level: 'Low', count: statistics?.severityDistribution.low, color: '#388e3c' }
            ].map(severity => (
              <div key={severity.level} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ 
                    width: '12px', 
                    height: '12px', 
                    backgroundColor: severity.color, 
                    borderRadius: '2px' 
                  }} />
                  <span style={{ fontSize: '14px' }}>{severity.level}</span>
                </div>
                <span style={{ fontSize: '14px', fontWeight: 'bold' }}>
                  {severity.count?.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Active Admins */}
      <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', marginBottom: '30px' }}>
        <h3>Most Active Admins</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5' }}>
                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Admin</th>
                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Actions</th>
                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Last Activity</th>
                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Top Actions</th>
              </tr>
            </thead>
            <tbody>
              {statistics?.adminActivity.slice(0, 5).map(admin => (
                <tr key={admin.adminId}>
                  <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '12px' }}>{admin.adminName}</div>
                    <div style={{ fontSize: '10px', color: '#666' }}>{admin.adminEmail}</div>
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'center' }}>
                    <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
                      {admin.actionCount}
                    </span>
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd', fontSize: '12px' }}>
                    {new Date(admin.lastActivity).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {admin.mostCommonActions.slice(0, 3).map(action => (
                        <span key={action} style={{
                          padding: '2px 4px',
                          backgroundColor: '#e3f2fd',
                          color: '#1976d2',
                          borderRadius: '3px',
                          fontSize: '9px'
                        }}>
                          {action}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Timeline Chart */}
      <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h3>Activity Timeline</h3>
        <div style={{ height: '200px', display: 'flex', alignItems: 'end', gap: '4px', padding: '20px 0' }}>
          {statistics?.timeline.map((point, index) => {
            const maxActions = Math.max(...statistics.timeline.map(p => p.totalActions));
            const height = (point.totalActions / maxActions) * 160;
            
            return (
              <div key={index} style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center',
                flex: 1
              }}>
                <div style={{
                  width: '100%',
                  height: `${height}px`,
                  backgroundColor: '#2196f3',
                  borderRadius: '2px',
                  marginBottom: '5px',
                  title: `${point.totalActions} actions on ${point.date}`
                }} />
                <div style={{ fontSize: '9px', color: '#666', textAlign: 'center' }}>
                  {new Date(point.date).getDate()}
                </div>
              </div>
            );
          })}
        </div>
        
        <div style={{ fontSize: '12px', color: '#666', textAlign: 'center', marginTop: '10px' }}>
          Daily activity for {period}
        </div>
      </div>
    </div>
  );
}
```

### Mutation Hooks

#### `useExportAuditLogs()`

```typescript
function useExportAuditLogs()
```

**Purpose**: Export audit logs with progress tracking

**Usage Example**:

```typescript
import { useExportAuditLogs } from '@/hooks/useAuditLogs';
import { useToast } from '@/contexts/ToastContext';

function AuditLogExport() {
  const [exportConfig, setExportConfig] = useState({
    format: 'xlsx' as const,
    dateFrom: '',
    dateTo: '',
    includeDetails: true
  });

  const exportAuditLogs = useExportAuditLogs();
  const toast = useToast();

  const handleExport = () => {
    exportAuditLogs.mutate({
      filters: {
        dateFrom: exportConfig.dateFrom ? `${exportConfig.dateFrom}T00:00:00.000Z` : undefined,
        dateTo: exportConfig.dateTo ? `${exportConfig.dateTo}T23:59:59.999Z` : undefined
      },
      format: exportConfig.format,
      includeDetails: exportConfig.includeDetails,
      reason: 'Admin panel export for compliance review'
    }, {
      onSuccess: (result) => {
        toast.showSuccess(`Export started: ${result.fileName}`);
        // Could poll for completion status
      },
      onError: (error) => {
        toast.showError(`Export failed: ${error.message}`);
      }
    });
  };

  return (
    <div style={{ maxWidth: '500px', padding: '20px' }}>
      <h2>Export Audit Logs</h2>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Export Format:</label>
        <select
          value={exportConfig.format}
          onChange={(e) => setExportConfig(prev => ({ 
            ...prev, 
            format: e.target.value as 'csv' | 'json' | 'xlsx'
          }))}
          style={{ width: '100%', padding: '8px', marginTop: '5px' }}
        >
          <option value="xlsx">Excel (.xlsx)</option>
          <option value="csv">CSV (.csv)</option>
          <option value="json">JSON (.json)</option>
        </select>
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Date Range:</label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '5px' }}>
          <input
            type="date"
            value={exportConfig.dateFrom}
            onChange={(e) => setExportConfig(prev => ({ ...prev, dateFrom: e.target.value }))}
            placeholder="From Date"
            style={{ padding: '8px' }}
          />
          <input
            type="date"
            value={exportConfig.dateTo}
            onChange={(e) => setExportConfig(prev => ({ ...prev, dateTo: e.target.value }))}
            placeholder="To Date"
            style={{ padding: '8px' }}
          />
        </div>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <label>
          <input
            type="checkbox"
            checked={exportConfig.includeDetails}
            onChange={(e) => setExportConfig(prev => ({ 
              ...prev, 
              includeDetails: e.target.checked 
            }))}
          />
          <span style={{ marginLeft: '5px' }}>Include detailed information</span>
        </label>
      </div>
      
      <button
        onClick={handleExport}
        disabled={exportAuditLogs.isPending}
        style={{
          padding: '12px 24px',
          backgroundColor: '#2196f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          width: '100%',
          fontSize: '16px'
        }}
      >
        {exportAuditLogs.isPending ? 'Starting Export...' : 'Export Audit Logs'}
      </button>
      
      {exportAuditLogs.isSuccess && (
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: '#e8f5e8', 
          borderRadius: '4px' 
        }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>
            Export Started Successfully
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            File: {exportAuditLogs.data?.fileName}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            Records: {exportAuditLogs.data?.recordCount.toLocaleString()}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            Status: {exportAuditLogs.data?.status}
          </div>
        </div>
      )}
    </div>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum AuditLogErrorType {
  LOG_NOT_FOUND = 'LOG_NOT_FOUND',
  INVALID_DATE_RANGE = 'INVALID_DATE_RANGE',
  EXPORT_LIMIT_EXCEEDED = 'EXPORT_LIMIT_EXCEEDED',
  INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS',
  BULK_DELETE_FAILED = 'BULK_DELETE_FAILED'
}
```

### Error Details

```typescript
interface AuditLogError {
  type: AuditLogErrorType;
  message: string;
  details?: {
    maxExportRecords?: number;
    dateRange?: { min: string; max: string };
    affectedRecords?: string[];
  };
}
```

## Business Rules & Constraints

### Data Retention Rules

1. **Retention Period**: Audit logs retained for minimum 7 years
2. **Immutability**: Audit logs cannot be modified after creation
3. **Deletion Policy**: Only system-level bulk deletions allowed
4. **Archiving**: Old logs automatically archived for long-term storage

### Access Control Rules

1. **View Permissions**: Admins can only view logs for their scope
2. **Export Limitations**: Maximum 100K records per export
3. **Sensitive Data**: PII masked in certain log types
4. **Real-time Monitoring**: Critical actions logged immediately

### Performance Rules

1. **Query Optimization**: Indexes on timestamp, action type, admin ID
2. **Pagination**: Required for large result sets
3. **Search Limits**: Text search limited to specific fields
4. **Export Timeouts**: Large exports processed asynchronously

## Integration Examples

### Complete Audit Logging Dashboard

```typescript
import React, { useState } from 'react';
import {
  useAuditLogs,
  useAuditLog,
  useAuditStatistics,
  useExportAuditLogs,
  useRelatedLogs
} from '@/hooks/useAuditLogs';

function AuditLoggingDashboard() {
  const [activeView, setActiveView] = useState('logs');
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '20px', borderBottom: '1px solid #ccc', backgroundColor: '#f8f9fa' }}>
        <h1>Audit Logging Dashboard</h1>
        
        {/* Navigation */}
        <div style={{ marginTop: '15px' }}>
          {[
            { key: 'logs', label: 'Audit Logs' },
            { key: 'analytics', label: 'Analytics' },
            { key: 'exports', label: 'Exports' },
            { key: 'settings', label: 'Settings' }
          ].map(view => (
            <button
              key={view.key}
              onClick={() => setActiveView(view.key)}
              style={{
                padding: '8px 16px',
                marginRight: '8px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: activeView === view.key ? '#2196f3' : '#e0e0e0',
                color: activeView === view.key ? 'white' : '#333',
                cursor: 'pointer'
              }}
            >
              {view.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Content */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {activeView === 'logs' && (
          <AuditLogsView onSelectLog={setSelectedLogId} selectedLogId={selectedLogId} />
        )}
        
        {activeView === 'analytics' && (
          <AuditAnalyticsView />
        )}
        
        {activeView === 'exports' && (
          <AuditExportsView />
        )}
        
        {activeView === 'settings' && (
          <AuditSettingsView />
        )}
      </div>
    </div>
  );
}

// Individual view components would be implemented separately
function AuditLogsView({ onSelectLog, selectedLogId }) {
  return <div>Audit Logs View Implementation</div>;
}

function AuditAnalyticsView() {
  return <div>Analytics View Implementation</div>;
}

function AuditExportsView() {
  return <div>Exports View Implementation</div>;
}

function AuditSettingsView() {
  return <div>Settings View Implementation</div>;
}
```

## Related Files

- `src/services/auditLogService.ts` - Main service implementation
- `src/hooks/useAuditLogs.ts` - React Query hooks
- `src/types/index.ts` - Type definitions
- `src/components/audit/` - Audit log components
- `src/pages/AuditLogsPage.tsx` - Main audit logs page
- `src/utils/auditHelpers.ts` - Audit utility functions