# System Settings Service Integration Guide

## Service Overview

- **Service Name**: System Settings Service
- **Base URL**: `{config.apiBaseUrl}/admin/settings`
- **Primary File**: `src/services/settingsService.ts`
- **Hook File**: `src/hooks/useSettings.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Get System Settings

```http
Method: GET
URL: /admin/settings
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
interface SettingsListParams {
  category?: string;                      // Filter by category
  search?: string;                        // Search by key or description
  includeDefaults?: boolean;              // Include default values (default: true)
  environment?: 'development' | 'staging' | 'production'; // Environment filter
}
```

**Response:**

```typescript
interface ApiResponse<SystemSettings> {
  success: boolean;
  data: SystemSettings;
  error?: string;
}

interface SystemSettings {
  general: GeneralSettings;
  security: SecuritySettings;
  email: EmailSettings;
  payment: PaymentSettings;
  features: FeatureSettings;
  integrations: IntegrationSettings;
  ui: UISettings;
  api: APISettings;
  metadata: SettingsMetadata;
}

interface GeneralSettings {
  appName: string;                        // Application name
  companyName: string;                    // Company/organization name
  supportEmail: string;                   // Support contact email
  defaultTimezone: string;                // Default timezone
  defaultLanguage: string;                // Default language code
  maintenanceMode: boolean;               // Maintenance mode status
  maintenanceMessage: string;             // Maintenance mode message
  allowRegistration: boolean;             // Allow new user registration
  requireEmailVerification: boolean;      // Require email verification
  sessionTimeout: number;                 // Session timeout in minutes
}

interface SecuritySettings {
  passwordMinLength: number;              // Minimum password length
  passwordRequireUppercase: boolean;      // Require uppercase letters
  passwordRequireLowercase: boolean;      // Require lowercase letters
  passwordRequireNumbers: boolean;        // Require numbers
  passwordRequireSymbols: boolean;        // Require special characters
  maxLoginAttempts: number;               // Max failed login attempts
  lockoutDuration: number;                // Account lockout duration (minutes)
  sessionSecure: boolean;                 // Secure session cookies
  corsOrigins: string[];                  // Allowed CORS origins
  rateLimiting: {
    enabled: boolean;
    requestsPerMinute: number;
    requestsPerHour: number;
  };
}

interface EmailSettings {
  provider: 'smtp' | 'sendgrid' | 'aws-ses'; // Email provider
  fromName: string;                       // Default sender name
  fromEmail: string;                      // Default sender email
  replyToEmail: string;                   // Reply-to email
  smtp: {
    host: string;
    port: number;
    secure: boolean;
    username: string;
    // password is write-only, not returned
  };
  templates: {
    welcome: string;                      // Welcome email template ID
    passwordReset: string;                // Password reset template ID
    emailVerification: string;            // Email verification template ID
    subscription: string;                 // Subscription emails template ID
  };
}

interface PaymentSettings {
  provider: 'stripe' | 'paypal';          // Payment provider
  currency: string;                       // Default currency
  taxRate: number;                        // Default tax rate (percentage)
  allowTrials: boolean;                   // Allow free trials
  trialDuration: number;                  // Default trial duration (days)
  gracePeriod: number;                    // Payment grace period (days)
  webhook: {
    enabled: boolean;
    url: string;
    secret: string;                       // Write-only
  };
}

interface FeatureSettings {
  aiFeatures: boolean;                    // Enable AI features
  analyticsTracking: boolean;             // Enable analytics
  chatSupport: boolean;                   // Enable chat support
  apiAccess: boolean;                     // Enable API access
  customBranding: boolean;                // Allow custom branding
  ssoIntegration: boolean;                // Enable SSO integration
  auditLogging: boolean;                  // Enable audit logging
  backupRetention: number;                // Backup retention (days)
}

interface IntegrationSettings {
  googleAnalytics: {
    enabled: boolean;
    trackingId: string;
  };
  slack: {
    enabled: boolean;
    webhookUrl: string;                   // Write-only
    channel: string;
  };
  zapier: {
    enabled: boolean;
    apiKey: string;                       // Write-only
  };
  webhook: {
    enabled: boolean;
    endpoints: WebhookEndpoint[];
  };
}

interface WebhookEndpoint {
  id: string;
  name: string;
  url: string;
  events: string[];                       // Event types to send
  active: boolean;
  secret: string;                         // Write-only
}

interface UISettings {
  theme: 'light' | 'dark' | 'auto';       // Default theme
  primaryColor: string;                   // Primary brand color
  secondaryColor: string;                 // Secondary brand color
  logo: string;                           // Logo URL
  favicon: string;                        // Favicon URL
  customCSS: string;                      // Custom CSS
  showPoweredBy: boolean;                 // Show "powered by" branding
}

interface APISettings {
  version: string;                        // Current API version
  rateLimiting: {
    enabled: boolean;
    requestsPerMinute: number;
    requestsPerDay: number;
  };
  cors: {
    enabled: boolean;
    origins: string[];
    methods: string[];
    headers: string[];
  };
  documentation: {
    enabled: boolean;
    public: boolean;
    url: string;
  };
}

interface SettingsMetadata {
  lastUpdated: string;                    // ISO date string
  updatedBy: string;                      // Admin who last updated
  version: string;                        // Settings version
  environment: 'development' | 'staging' | 'production';
}
```

### 2. Update System Settings

```http
Method: PATCH
URL: /admin/settings
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface UpdateSettingsData {
  general?: Partial<GeneralSettings>;
  security?: Partial<SecuritySettings>;
  email?: Partial<EmailSettings>;
  payment?: Partial<PaymentSettings>;
  features?: Partial<FeatureSettings>;
  integrations?: Partial<IntegrationSettings>;
  ui?: Partial<UISettings>;
  api?: Partial<APISettings>;
}
```

**Response:**

```typescript
interface ApiResponse<SystemSettings> {
  success: boolean;
  data: SystemSettings;
  error?: string;
}
```

### 3. Reset Settings Category

```http
Method: POST
URL: /admin/settings/{category}/reset
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  category: 'general' | 'security' | 'email' | 'payment' | 'features' | 'integrations' | 'ui' | 'api';
}
```

**Response:**

```typescript
interface ApiResponse<SystemSettings> {
  success: boolean;
  data: SystemSettings;
  error?: string;
}
```

### 4. Test Email Configuration

```http
Method: POST
URL: /admin/settings/email/test
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface TestEmailParams {
  toEmail: string;                        // Test recipient email
  template?: string;                      // Optional template to test
}
```

**Response:**

```typescript
interface ApiResponse<EmailTestResult> {
  success: boolean;
  data: {
    sent: boolean;
    messageId?: string;
    error?: string;
    details: {
      provider: string;
      from: string;
      to: string;
      subject: string;
      sentAt: string;
    };
  };
  error?: string;
}
```

### 5. Test Payment Configuration

```http
Method: POST
URL: /admin/settings/payment/test
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Response:**

```typescript
interface ApiResponse<PaymentTestResult> {
  success: boolean;
  data: {
    connected: boolean;
    provider: string;
    account: {
      id: string;
      name: string;
      country: string;
      currency: string;
    };
    capabilities: string[];
    error?: string;
  };
  error?: string;
}
```

### 6. Get Settings History

```http
Method: GET
URL: /admin/settings/history
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
{
  page?: number;                          // Page number (default: 1)
  pageSize?: number;                      // Items per page (default: 50)
  category?: string;                      // Filter by category
  adminId?: string;                       // Filter by admin who made changes
  startDate?: string;                     // Start date (ISO string)
  endDate?: string;                       // End date (ISO string)
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<SettingsChange>> {
  success: boolean;
  data: {
    items: SettingsChange[];
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

interface SettingsChange {
  id: string;
  category: string;
  setting: string;                        // Setting key that was changed
  oldValue: any;                          // Previous value
  newValue: any;                          // New value
  changedBy: string;                      // Admin who made the change
  changedAt: string;                      // ISO date string
  reason?: string;                        // Optional reason for change
  ip: string;                             // IP address of change
  userAgent: string;                      // User agent of change
}
```

### 7. Export Settings

```http
Method: GET
URL: /admin/settings/export
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
{
  format?: 'json' | 'yaml';               // Export format (default: json)
  includeSecrets?: boolean;               // Include sensitive data (default: false)
  categories?: string[];                  // Categories to export (default: all)
}
```

**Response:**

```typescript
interface ApiResponse<SettingsExport> {
  success: boolean;
  data: {
    settings: SystemSettings | string;    // Settings object or serialized string
    metadata: {
      exportedAt: string;
      exportedBy: string;
      version: string;
      format: string;
      includeSecrets: boolean;
    };
  };
  error?: string;
}
```

### 8. Import Settings

```http
Method: POST
URL: /admin/settings/import
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface ImportSettingsData {
  settings: SystemSettings | string;     // Settings to import
  format?: 'json' | 'yaml';              // Import format (auto-detected if not provided)
  overwriteExisting?: boolean;            // Overwrite existing settings (default: false)
  validateOnly?: boolean;                 // Only validate, don't import (default: false)
}
```

**Response:**

```typescript
interface ApiResponse<SettingsImportResult> {
  success: boolean;
  data: {
    imported: boolean;
    changes: SettingsChange[];
    errors: string[];
    warnings: string[];
    summary: {
      categoriesUpdated: string[];
      settingsChanged: number;
      secretsSkipped: number;
    };
  };
  error?: string;
}
```

## Service Methods

### Core Methods

#### `getSettings(params?: SettingsListParams)`

```typescript
async getSettings(params: SettingsListParams = {}): Promise<SystemSettings>
```

**Purpose**: Fetch current system settings

**Parameters**:

- `params`: Optional filtering parameters

**Returns**: Complete system settings

**Usage Example**:

```typescript
import { settingsService } from '@/services/settingsService';

// Get all settings
const settings = await settingsService.getSettings();

// Get specific category with defaults
const emailSettings = await settingsService.getSettings({
  category: 'email',
  includeDefaults: true
});
```

#### `updateSettings(data: UpdateSettingsData)`

```typescript
async updateSettings(data: UpdateSettingsData): Promise<SystemSettings>
```

**Purpose**: Update system settings

**Parameters**:

- `data`: Settings updates by category

**Returns**: Updated system settings

**Validation Rules**:

- Email addresses must be valid format
- URLs must be valid format
- Colors must be valid hex codes
- Numeric values must be within acceptable ranges

**Usage Example**:

```typescript
import { settingsService } from '@/services/settingsService';

const updatedSettings = await settingsService.updateSettings({
  general: {
    appName: 'PurposePath Admin',
    supportEmail: 'support@purposepath.app',
    sessionTimeout: 480 // 8 hours
  },
  security: {
    passwordMinLength: 12,
    maxLoginAttempts: 5,
    lockoutDuration: 30
  },
  ui: {
    theme: 'dark',
    primaryColor: '#2196f3',
    showPoweredBy: false
  }
});
```

#### `resetCategory(category: string)`

```typescript
async resetCategory(category: string): Promise<SystemSettings>
```

**Purpose**: Reset a settings category to defaults

**Parameters**:

- `category`: Category to reset

**Returns**: Updated system settings

**Usage Example**:

```typescript
import { settingsService } from '@/services/settingsService';

// Reset security settings to defaults
const settings = await settingsService.resetCategory('security');
```

#### `testEmailConfiguration(params: TestEmailParams)`

```typescript
async testEmailConfiguration(params: TestEmailParams): Promise<EmailTestResult>
```

**Purpose**: Test email configuration by sending test email

**Parameters**:

- `params`: Test email parameters

**Returns**: Test result with details

**Usage Example**:

```typescript
import { settingsService } from '@/services/settingsService';

const testResult = await settingsService.testEmailConfiguration({
  toEmail: 'admin@example.com',
  template: 'welcome'
});

if (testResult.sent) {
  console.log('Email sent successfully:', testResult.messageId);
} else {
  console.error('Email failed:', testResult.error);
}
```

#### `testPaymentConfiguration()`

```typescript
async testPaymentConfiguration(): Promise<PaymentTestResult>
```

**Purpose**: Test payment provider connection

**Returns**: Connection test result

**Usage Example**:

```typescript
import { settingsService } from '@/services/settingsService';

const testResult = await settingsService.testPaymentConfiguration();

if (testResult.connected) {
  console.log('Payment provider connected:', testResult.account);
} else {
  console.error('Payment connection failed:', testResult.error);
}
```

#### `getSettingsHistory(params?: SettingsHistoryParams)`

```typescript
async getSettingsHistory(params: SettingsHistoryParams = {}): Promise<PaginatedResponse<SettingsChange>>
```

**Purpose**: Get settings change history

**Parameters**:

- `params`: Optional filtering and pagination parameters

**Returns**: Paginated settings change history

**Usage Example**:

```typescript
import { settingsService } from '@/services/settingsService';

// Get recent changes
const history = await settingsService.getSettingsHistory({
  pageSize: 20,
  category: 'security'
});

// Get changes by specific admin
const adminChanges = await settingsService.getSettingsHistory({
  adminId: 'admin-123',
  startDate: '2024-10-01T00:00:00.000Z'
});
```

## React Query Hooks

### Query Hooks

#### `useSettings(params?: SettingsListParams)`

```typescript
function useSettings(params: SettingsListParams = {})
```

**Purpose**: Fetch system settings with caching

**Cache Key**: `['settings', params]`

**Stale Time**: 5 minutes

**Usage Example**:

```typescript
import { useSettings } from '@/hooks/useSettings';

function SettingsDashboard() {
  const {
    data: settings,
    isLoading,
    error
  } = useSettings();

  if (isLoading) return <div>Loading settings...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>System Settings</h1>
      
      {/* General Settings */}
      <div style={{ marginBottom: '30px' }}>
        <h2>General Settings</h2>
        <div style={{ display: 'grid', gap: '15px' }}>
          <div>
            <strong>Application Name:</strong> {settings?.general.appName}
          </div>
          <div>
            <strong>Company Name:</strong> {settings?.general.companyName}
          </div>
          <div>
            <strong>Support Email:</strong> {settings?.general.supportEmail}
          </div>
          <div>
            <strong>Maintenance Mode:</strong> 
            <span style={{
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '12px',
              backgroundColor: settings?.general.maintenanceMode ? '#f44336' : '#4caf50',
              color: 'white',
              marginLeft: '8px'
            }}>
              {settings?.general.maintenanceMode ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>
      </div>
      
      {/* Security Settings */}
      <div style={{ marginBottom: '30px' }}>
        <h2>Security Settings</h2>
        <div style={{ display: 'grid', gap: '15px' }}>
          <div>
            <strong>Password Requirements:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
              <li>Minimum length: {settings?.security.passwordMinLength} characters</li>
              <li>Uppercase: {settings?.security.passwordRequireUppercase ? 'Required' : 'Optional'}</li>
              <li>Numbers: {settings?.security.passwordRequireNumbers ? 'Required' : 'Optional'}</li>
              <li>Symbols: {settings?.security.passwordRequireSymbols ? 'Required' : 'Optional'}</li>
            </ul>
          </div>
          <div>
            <strong>Login Security:</strong> {settings?.security.maxLoginAttempts} attempts, 
            {settings?.security.lockoutDuration} min lockout
          </div>
        </div>
      </div>
      
      {/* Features */}
      <div style={{ marginBottom: '30px' }}>
        <h2>Feature Flags</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
          {Object.entries(settings?.features || {}).map(([key, value]) => (
            <div key={key} style={{ 
              padding: '10px', 
              border: '1px solid #ddd', 
              borderRadius: '4px',
              backgroundColor: value ? '#e8f5e8' : '#fff3cd'
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
              </div>
              <span style={{
                padding: '2px 8px',
                borderRadius: '12px',
                fontSize: '12px',
                backgroundColor: value ? '#4caf50' : '#ff9800',
                color: 'white'
              }}>
                {value ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          ))}
        </div>
      </div>
      
      {/* UI Settings */}
      <div style={{ marginBottom: '30px' }}>
        <h2>UI Settings</h2>
        <div style={{ display: 'grid', gap: '15px' }}>
          <div>
            <strong>Theme:</strong> {settings?.ui.theme}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <strong>Primary Color:</strong>
            <div style={{
              width: '20px',
              height: '20px',
              backgroundColor: settings?.ui.primaryColor,
              border: '1px solid #ccc',
              borderRadius: '4px'
            }} />
            {settings?.ui.primaryColor}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <strong>Secondary Color:</strong>
            <div style={{
              width: '20px',
              height: '20px',
              backgroundColor: settings?.ui.secondaryColor,
              border: '1px solid #ccc',
              borderRadius: '4px'
            }} />
            {settings?.ui.secondaryColor}
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### `useSettingsHistory(params?: SettingsHistoryParams)`

```typescript
function useSettingsHistory(params: SettingsHistoryParams = {})
```

**Purpose**: Fetch settings change history

**Cache Key**: `['settingsHistory', params]`

**Stale Time**: 2 minutes

**Usage Example**:

```typescript
import { useSettingsHistory } from '@/hooks/useSettings';

function SettingsHistory() {
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 20,
    category: ''
  });

  const {
    data: history,
    isLoading,
    error
  } = useSettingsHistory(filters);

  if (isLoading) return <div>Loading history...</div>;
  if (error) return <div>Error loading history</div>;

  return (
    <div>
      <h2>Settings Change History</h2>
      
      {/* Filters */}
      <div style={{ marginBottom: '20px' }}>
        <select
          value={filters.category}
          onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
        >
          <option value="">All Categories</option>
          <option value="general">General</option>
          <option value="security">Security</option>
          <option value="email">Email</option>
          <option value="payment">Payment</option>
          <option value="features">Features</option>
          <option value="ui">UI</option>
        </select>
      </div>
      
      {/* History Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ddd' }}>Date</th>
              <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ddd' }}>Category</th>
              <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ddd' }}>Setting</th>
              <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ddd' }}>Changed By</th>
              <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ddd' }}>Change</th>
            </tr>
          </thead>
          <tbody>
            {history?.items.map(change => (
              <tr key={change.id}>
                <td style={{ padding: '10px', border: '1px solid #ddd', fontSize: '12px' }}>
                  {new Date(change.changedAt).toLocaleString()}
                </td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    backgroundColor: '#e3f2fd'
                  }}>
                    {change.category}
                  </span>
                </td>
                <td style={{ padding: '10px', border: '1px solid #ddd', fontFamily: 'monospace' }}>
                  {change.setting}
                </td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                  {change.changedBy}
                </td>
                <td style={{ padding: '10px', border: '1px solid #ddd', fontSize: '12px' }}>
                  <div style={{ marginBottom: '5px' }}>
                    <strong>From:</strong> <code>{JSON.stringify(change.oldValue)}</code>
                  </div>
                  <div>
                    <strong>To:</strong> <code>{JSON.stringify(change.newValue)}</code>
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
          disabled={!history?.pagination.hasPrevious}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
        >
          Previous
        </button>
        <span style={{ margin: '0 15px' }}>
          Page {history?.pagination.page} of {history?.pagination.totalPages}
        </span>
        <button
          disabled={!history?.pagination.hasNext}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

### Mutation Hooks

#### `useUpdateSettings()`

```typescript
function useUpdateSettings()
```

**Purpose**: Update system settings with cache invalidation

**Cache Invalidation**: Invalidates settings cache

**Usage Example**:

```typescript
import { useUpdateSettings } from '@/hooks/useSettings';
import { useToast } from '@/contexts/ToastContext';

function GeneralSettingsForm() {
  const { data: settings } = useSettings();
  const updateSettings = useUpdateSettings();
  const toast = useToast();
  
  const [formData, setFormData] = useState({
    appName: '',
    companyName: '',
    supportEmail: '',
    maintenanceMode: false,
    maintenanceMessage: ''
  });

  // Initialize form with current settings
  useEffect(() => {
    if (settings?.general) {
      setFormData({
        appName: settings.general.appName,
        companyName: settings.general.companyName,
        supportEmail: settings.general.supportEmail,
        maintenanceMode: settings.general.maintenanceMode,
        maintenanceMessage: settings.general.maintenanceMessage
      });
    }
  }, [settings]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    updateSettings.mutate({
      general: formData
    }, {
      onSuccess: () => {
        toast.showSuccess('General settings updated successfully');
      },
      onError: (error) => {
        toast.showError(`Failed to update settings: ${error.message}`);
      }
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '500px' }}>
      <h3>General Settings</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Application Name:</label>
        <input
          type="text"
          value={formData.appName}
          onChange={(e) => setFormData(prev => ({ ...prev, appName: e.target.value }))}
          required
          style={{ width: '100%', padding: '8px', marginTop: '5px' }}
        />
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Company Name:</label>
        <input
          type="text"
          value={formData.companyName}
          onChange={(e) => setFormData(prev => ({ ...prev, companyName: e.target.value }))}
          required
          style={{ width: '100%', padding: '8px', marginTop: '5px' }}
        />
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label>Support Email:</label>
        <input
          type="email"
          value={formData.supportEmail}
          onChange={(e) => setFormData(prev => ({ ...prev, supportEmail: e.target.value }))}
          required
          style={{ width: '100%', padding: '8px', marginTop: '5px' }}
        />
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label>
          <input
            type="checkbox"
            checked={formData.maintenanceMode}
            onChange={(e) => setFormData(prev => ({ ...prev, maintenanceMode: e.target.checked }))}
          />
          <span style={{ marginLeft: '5px' }}>Maintenance Mode</span>
        </label>
      </div>
      
      {formData.maintenanceMode && (
        <div style={{ marginBottom: '15px' }}>
          <label>Maintenance Message:</label>
          <textarea
            value={formData.maintenanceMessage}
            onChange={(e) => setFormData(prev => ({ ...prev, maintenanceMessage: e.target.value }))}
            rows={3}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            placeholder="We're currently performing maintenance. Please check back later."
          />
        </div>
      )}
      
      <button
        type="submit"
        disabled={updateSettings.isPending}
        style={{
          padding: '10px 20px',
          backgroundColor: '#2196f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px'
        }}
      >
        {updateSettings.isPending ? 'Updating...' : 'Update Settings'}
      </button>
    </form>
  );
}
```

#### `useTestEmailConfiguration()`

```typescript
function useTestEmailConfiguration()
```

**Purpose**: Test email configuration

**Usage Example**:

```typescript
import { useTestEmailConfiguration } from '@/hooks/useSettings';

function EmailTestButton() {
  const testEmail = useTestEmailConfiguration();
  
  const handleTest = () => {
    testEmail.mutate({
      toEmail: 'admin@example.com'
    }, {
      onSuccess: (result) => {
        if (result.sent) {
          alert(`Test email sent successfully! Message ID: ${result.messageId}`);
        } else {
          alert(`Email test failed: ${result.error}`);
        }
      },
      onError: (error) => {
        alert(`Test failed: ${error.message}`);
      }
    });
  };

  return (
    <button
      onClick={handleTest}
      disabled={testEmail.isPending}
      style={{
        padding: '8px 16px',
        backgroundColor: '#4caf50',
        color: 'white',
        border: 'none',
        borderRadius: '4px'
      }}
    >
      {testEmail.isPending ? 'Testing...' : 'Test Email Configuration'}
    </button>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum SettingsErrorType {
  SETTINGS_NOT_FOUND = 'SETTINGS_NOT_FOUND',
  INVALID_CONFIGURATION = 'INVALID_CONFIGURATION',
  EMAIL_TEST_FAILED = 'EMAIL_TEST_FAILED',
  PAYMENT_TEST_FAILED = 'PAYMENT_TEST_FAILED',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  CATEGORY_NOT_FOUND = 'CATEGORY_NOT_FOUND',
  IMPORT_FAILED = 'IMPORT_FAILED',
  EXPORT_FAILED = 'EXPORT_FAILED'
}
```

### Validation Error Details

```typescript
interface SettingsValidationError {
  category: string;
  field: string;
  message: string;
  code: string;
  value: any;
}

// Example validation errors
const validationErrors = [
  {
    category: 'general',
    field: 'supportEmail',
    message: 'Invalid email address format',
    code: 'INVALID_EMAIL_FORMAT',
    value: 'invalid-email'
  },
  {
    category: 'ui',
    field: 'primaryColor',
    message: 'Invalid hex color format',
    code: 'INVALID_COLOR_FORMAT',
    value: 'notacolor'
  }
];
```

## Business Rules & Constraints

### General Rules

1. **Email Validation**: All email fields must be valid email addresses
2. **URL Validation**: All URL fields must be valid HTTP/HTTPS URLs
3. **Color Validation**: UI colors must be valid hex color codes
4. **Numeric Ranges**: Timeout and limit values must be within acceptable ranges

### Security Rules

1. **Password Requirements**: Must be enforceable and reasonable
2. **Rate Limiting**: Must prevent abuse while allowing normal usage
3. **Session Security**: Secure cookies required in production
4. **CORS Origins**: Must be valid domains for security

### Feature Dependencies

1. **AI Features**: Require API access to be enabled
2. **Payment Features**: Require valid payment provider configuration
3. **Email Features**: Require valid email provider configuration
4. **SSO Integration**: Requires security features to be properly configured

## Integration Examples

### Complete Settings Management Interface

```typescript
import React, { useState } from 'react';
import {
  useSettings,
  useUpdateSettings,
  useTestEmailConfiguration,
  useTestPaymentConfiguration,
  useSettingsHistory
} from '@/hooks/useSettings';

function SettingsManagement() {
  const [activeTab, setActiveTab] = useState('general');
  const [showHistory, setShowHistory] = useState(false);
  
  const { data: settings, isLoading } = useSettings();
  const updateSettings = useUpdateSettings();
  const testEmail = useTestEmailConfiguration();
  const testPayment = useTestPaymentConfiguration();

  if (isLoading) return <div>Loading settings...</div>;

  const tabs = [
    { id: 'general', label: 'General' },
    { id: 'security', label: 'Security' },
    { id: 'email', label: 'Email' },
    { id: 'payment', label: 'Payment' },
    { id: 'features', label: 'Features' },
    { id: 'ui', label: 'UI & Branding' }
  ];

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '20px', borderBottom: '1px solid #ccc' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1>System Settings</h1>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setShowHistory(!showHistory)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#757575',
                color: 'white',
                border: 'none',
                borderRadius: '4px'
              }}
            >
              {showHistory ? 'Hide History' : 'Show History'}
            </button>
            
            <span style={{
              padding: '8px 12px',
              backgroundColor: '#e8f5e8',
              color: '#2e7d32',
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              Last updated: {settings?.metadata.lastUpdated ? 
                new Date(settings.metadata.lastUpdated).toLocaleString() : 'Never'
              }
            </span>
          </div>
        </div>
        
        {/* Tabs */}
        <div style={{ marginTop: '20px', display: 'flex', gap: '2px' }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderRadius: '4px 4px 0 0',
                backgroundColor: activeTab === tab.id ? '#2196f3' : '#f5f5f5',
                color: activeTab === tab.id ? 'white' : '#333'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      
      <div style={{ flex: 1, display: 'flex' }}>
        {/* Settings Panel */}
        <div style={{ flex: showHistory ? 1 : 1, padding: '20px', overflow: 'auto' }}>
          {activeTab === 'general' && (
            <GeneralSettingsPanel settings={settings} updateSettings={updateSettings} />
          )}
          
          {activeTab === 'security' && (
            <SecuritySettingsPanel settings={settings} updateSettings={updateSettings} />
          )}
          
          {activeTab === 'email' && (
            <EmailSettingsPanel settings={settings} updateSettings={updateSettings} testEmail={testEmail} />
          )}
          
          {activeTab === 'payment' && (
            <PaymentSettingsPanel settings={settings} updateSettings={updateSettings} testPayment={testPayment} />
          )}
          
          {activeTab === 'features' && (
            <FeatureSettingsPanel settings={settings} updateSettings={updateSettings} />
          )}
          
          {activeTab === 'ui' && (
            <UISettingsPanel settings={settings} updateSettings={updateSettings} />
          )}
        </div>
        
        {/* History Panel */}
        {showHistory && (
          <div style={{ width: '400px', borderLeft: '1px solid #ccc', padding: '20px', overflow: 'auto' }}>
            <SettingsHistoryPanel />
          </div>
        )}
      </div>
    </div>
  );
}

// Individual settings panels would be implemented as separate components
function GeneralSettingsPanel({ settings, updateSettings }) {
  // Implementation for general settings form
  return <div>General Settings Panel</div>;
}

function SecuritySettingsPanel({ settings, updateSettings }) {
  // Implementation for security settings form
  return <div>Security Settings Panel</div>;
}

function EmailSettingsPanel({ settings, updateSettings, testEmail }) {
  // Implementation for email settings form with test button
  return <div>Email Settings Panel</div>;
}

function PaymentSettingsPanel({ settings, updateSettings, testPayment }) {
  // Implementation for payment settings form with test button
  return <div>Payment Settings Panel</div>;
}

function FeatureSettingsPanel({ settings, updateSettings }) {
  // Implementation for feature flags management
  return <div>Feature Settings Panel</div>;
}

function UISettingsPanel({ settings, updateSettings }) {
  // Implementation for UI/branding settings
  return <div>UI Settings Panel</div>;
}

function SettingsHistoryPanel() {
  // Implementation for settings history display
  return <div>Settings History Panel</div>;
}
```

## Related Files

- `src/services/settingsService.ts` - Main service implementation
- `src/hooks/useSettings.ts` - React Query hooks
- `src/types/index.ts` - Type definitions
- `src/components/features/settings/` - Settings management components
- `src/pages/SettingsPage.tsx` - Main settings page
- `src/pages/SettingsHistoryPage.tsx` - Settings history page