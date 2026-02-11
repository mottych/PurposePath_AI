# Email Template Service Integration Guide

## Service Overview

- **Service Name**: Email Template Service
- **Base URL**: `{config.apiBaseUrl}/admin/email-templates`
- **Primary File**: `src/services/emailTemplateService.ts`
- **Hook File**: `src/hooks/useEmailTemplates.ts`
- **Authentication**: Bearer token required
- **Error Handling**: Automatic retry with exponential backoff

## Endpoints Reference

### 1. Get Email Templates List

```http
Method: GET
URL: /admin/email-templates
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

```typescript
interface EmailTemplateListParams {
  page?: number;                          // Page number (default: 1)
  pageSize?: number;                      // Items per page (default: 50)
  search?: string;                        // Search by name or subject
  category?: string;                      // Filter by category
  status?: 'active' | 'draft' | 'all';   // Filter by status (default: 'all')
  language?: string;                      // Filter by language code
}
```

**Response:**

```typescript
interface ApiResponse<PaginatedResponse<EmailTemplate>> {
  success: boolean;
  data: {
    items: EmailTemplate[];
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

interface EmailTemplate {
  id: string;                            // Unique template ID
  name: string;                          // Template name
  subject: string;                       // Email subject line
  description: string;                   // Template description
  category: string;                      // Template category
  language: string;                      // Language code (e.g., 'en', 'es')
  htmlContent: string;                   // HTML email content
  textContent: string;                   // Plain text content
  variables: TemplateVariable[];         // Available variables
  isActive: boolean;                     // Whether template is active
  isDefault: boolean;                    // Default template for category
  previewUrl?: string;                   // Preview URL if available
  lastUsed?: string;                     // Last used timestamp
  usageCount: number;                    // Number of times used
  createdAt: string;                     // ISO date string
  updatedAt: string;                     // ISO date string
  createdBy: string;                     // Admin who created
  metadata: TemplateMetadata;            // Additional metadata
}

interface TemplateVariable {
  name: string;                          // Variable name in PascalCase (e.g., 'UserName')
  description: string;                   // Variable description
  type: 'string' | 'number' | 'boolean' | 'date' | 'url'; // Variable type
  required: boolean;                     // Whether variable is required
  defaultValue?: any;                    // Default value if any
  example?: string;                      // Example value
  syntaxHint?: string;                   // Optional hint for RazorLight syntax (e.g., '@Model.UserName')
}

interface TemplateMetadata {
  openRate?: number;                     // Email open rate (percentage)
  clickRate?: number;                    // Click-through rate (percentage)
  bounceRate?: number;                   // Bounce rate (percentage)
  lastPerformanceUpdate?: string;        // Last performance data update
  tags: string[];                        // Template tags
  notes?: string;                        // Internal notes
}
```

### 2. Get Email Template Details

```http
Method: GET
URL: /admin/email-templates/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Email template ID
}
```

**Response:**

```typescript
interface ApiResponse<EmailTemplate> {
  success: boolean;
  data: EmailTemplate;
  error?: string;
}
```

### 3. Create Email Template

```http
Method: POST
URL: /admin/email-templates
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**

```typescript
interface CreateEmailTemplateData {
  name: string;                          // Template name
  subject: string;                       // Email subject line
  description: string;                   // Template description
  category: string;                      // Template category
  language: string;                      // Language code
  htmlContent: string;                   // HTML email content
  textContent: string;                   // Plain text content
  variables: TemplateVariable[];         // Template variables
  isActive: boolean;                     // Active status
  isDefault: boolean;                    // Default for category
  tags: string[];                        // Template tags
  notes?: string;                        // Internal notes
}
```

**Response:**

```typescript
interface ApiResponse<EmailTemplate> {
  success: boolean;
  data: EmailTemplate;
  error?: string;
}
```

### 4. Update Email Template

```http
Method: PATCH
URL: /admin/email-templates/{id}
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Email template ID
}
```

**Request Body:**

```typescript
interface UpdateEmailTemplateData extends Partial<CreateEmailTemplateData> {
  // All fields from CreateEmailTemplateData are optional for updates
}
```

**Response:**

```typescript
interface ApiResponse<EmailTemplate> {
  success: boolean;
  data: EmailTemplate;
  error?: string;
}
```

### 5. Clone Email Template

```http
Method: POST
URL: /admin/email-templates/{id}/clone
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Source template ID
}
```

**Request Body:**

```typescript
interface CloneTemplateData {
  name: string;                          // New template name
  description?: string;                  // New description (optional)
  language?: string;                     // New language (optional)
}
```

**Response:**

```typescript
interface ApiResponse<EmailTemplate> {
  success: boolean;
  data: EmailTemplate;
  error?: string;
}
```

### 6. Preview Email Template

```http
Method: POST
URL: /admin/email-templates/{id}/preview
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Email template ID
}
```

**Request Body:**

```typescript
interface PreviewTemplateData {
  variables?: Record<string, any>;       // Variable values for preview
  format?: 'html' | 'text' | 'both';    // Preview format (default: 'both')
}
```

**Response:**

```typescript
interface ApiResponse<EmailPreview> {
  success: boolean;
  data: {
    subject: string;                     // Rendered subject
    htmlContent?: string;                // Rendered HTML content
    textContent?: string;                // Rendered text content
    variables: Record<string, any>;      // Variables used
    previewUrl?: string;                 // Temporary preview URL
  };
  error?: string;
}
```

### 7. Send Test Email

```http
Method: POST
URL: /admin/email-templates/{id}/test
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Email template ID
}
```

**Request Body:**

```typescript
interface SendTestEmailData {
  toEmail: string;                       // Test recipient email
  variables?: Record<string, any>;       // Variable values for test
  fromName?: string;                     // Override sender name
  fromEmail?: string;                    // Override sender email
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
      to: string;
      from: string;
      subject: string;
      sentAt: string;
      provider: string;
    };
  };
  error?: string;
}
```

### 8. Get Template Usage Analytics

```http
Method: GET
URL: /admin/email-templates/{id}/analytics
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

```typescript
{
  id: string;  // Email template ID
}
```

**Query Parameters:**

```typescript
{
  period?: 'day' | 'week' | 'month' | 'year'; // Time period (default: 'month')
  startDate?: string;                    // Start date (ISO string)
  endDate?: string;                      // End date (ISO string)
}
```

**Response:**

```typescript
interface ApiResponse<TemplateAnalytics> {
  success: boolean;
  data: {
    templateId: string;
    templateName: string;
    period: {
      start: string;
      end: string;
    };
    metrics: {
      sent: number;                      // Total emails sent
      delivered: number;                 // Successfully delivered
      opened: number;                    // Emails opened
      clicked: number;                   // Links clicked
      bounced: number;                   // Bounced emails
      unsubscribed: number;              // Unsubscribes
    };
    rates: {
      deliveryRate: number;              // Delivery rate (%)
      openRate: number;                  // Open rate (%)
      clickRate: number;                 // Click rate (%)
      bounceRate: number;                // Bounce rate (%)
      unsubscribeRate: number;           // Unsubscribe rate (%)
    };
    timeline: AnalyticsDataPoint[];      // Time-based data points
  };
  error?: string;
}

interface AnalyticsDataPoint {
  date: string;                          // Date (ISO string)
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
}
```

### 9. Delete Email Template

```http
Method: DELETE
URL: /admin/email-templates/{id}
Authentication: Bearer {access_token}
```

**Path Parameters:**

```typescript
{
  id: string;  // Email template ID
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

### 10. Get Template Categories

```http
Method: GET
URL: /admin/email-templates/categories
Authentication: Bearer {access_token}
Content-Type: application/json
```

**Response:**

```typescript
interface ApiResponse<TemplateCategory[]> {
  success: boolean;
  data: TemplateCategory[];
  error?: string;
}

interface TemplateCategory {
  name: string;                          // Category name
  description: string;                   // Category description
  templateCount: number;                 // Number of templates in category
  defaultTemplate?: string;              // Default template ID for category
  requiredVariables: string[];           // Variables required for this category
}
```

## Service Methods

### Core Methods

#### Server-Side Methods (API Integration)

#### `getEmailTemplates(params?: EmailTemplateListParams)`

```typescript
async getEmailTemplates(params: EmailTemplateListParams = {}): Promise<PaginatedResponse<EmailTemplate>>
```

**Purpose**: Fetch paginated list of email templates with optional filters

**Parameters**:

- `params`: Optional filtering and pagination parameters

**Returns**: Paginated email template list

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

// Get all active templates
const activeTemplates = await emailTemplateService.getEmailTemplates({
  status: 'active',
  pageSize: 25
});

// Search for welcome templates
const welcomeTemplates = await emailTemplateService.getEmailTemplates({
  search: 'welcome',
  category: 'onboarding'
});
```

#### `getEmailTemplate(id: string)`

```typescript
async getEmailTemplate(id: string): Promise<EmailTemplate>
```

**Purpose**: Get email template details by ID

**Parameters**:

- `id`: Email template ID

**Returns**: Complete email template details

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

const template = await emailTemplateService.getEmailTemplate('template-123');
console.log(`Template: ${template.name}, Subject: ${template.subject}`);
```

#### `createEmailTemplate(data: CreateEmailTemplateData)`

```typescript
async createEmailTemplate(data: CreateEmailTemplateData): Promise<EmailTemplate>
```

**Purpose**: Create a new email template

**Parameters**:

- `data`: Email template creation data

**Returns**: Created email template

**Validation Rules**:

- Template name must be unique within category
- HTML content must be valid HTML
- Variables in content must be defined in variables array
- Subject line cannot be empty

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

const newTemplate = await emailTemplateService.createEmailTemplate({
  name: 'Welcome Email',
  subject: 'Welcome to {{appName}}, {{userName}}!',
  description: 'Welcome email sent to new users',
  category: 'onboarding',
  language: 'en',
  htmlContent: `
    <h1>Welcome {{userName}}!</h1>
    <p>Thank you for joining {{appName}}. We're excited to have you aboard!</p>
    <a href="{{dashboardUrl}}">Get Started</a>
  `,
  textContent: `
    Welcome {{userName}}!
    
    Thank you for joining {{appName}}. We're excited to have you aboard!
    
    Get Started: {{dashboardUrl}}
  `,
  variables: [
    {
      name: 'userName',
      description: 'User\'s display name',
      type: 'string',
      required: true,
      example: 'John Doe'
    },
    {
      name: 'appName',
      description: 'Application name',
      type: 'string',
      required: true,
      defaultValue: 'PurposePath',
      example: 'PurposePath'
    },
    {
      name: 'dashboardUrl',
      description: 'URL to user dashboard',
      type: 'url',
      required: true,
      example: 'https://app.purposepath.com/dashboard'
    }
  ],
  isActive: true,
  isDefault: false,
  tags: ['welcome', 'onboarding', 'user'],
  notes: 'Primary welcome email for new user registrations'
});
```

#### `previewTemplate(id: string, variables?: Record<string, any>)`

```typescript
async previewTemplate(id: string, variables: Record<string, any> = {}): Promise<EmailPreview>
```

**Purpose**: Preview email template with variable substitution

**Parameters**:

- `id`: Email template ID
- `variables`: Variable values for preview

**Returns**: Rendered email preview

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

const preview = await emailTemplateService.previewTemplate('template-123', {
  userName: 'John Doe',
  appName: 'PurposePath',
  dashboardUrl: 'https://app.purposepath.com/dashboard'
});

console.log('Preview Subject:', preview.subject);
console.log('Preview HTML:', preview.htmlContent);
```

#### `sendTestEmail(id: string, params: SendTestEmailData)`

```typescript
async sendTestEmail(id: string, params: SendTestEmailData): Promise<EmailTestResult>
```

**Purpose**: Send test email using template

**Parameters**:

- `id`: Email template ID
- `params`: Test email parameters

**Returns**: Test email result

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

const testResult = await emailTemplateService.sendTestEmail('template-123', {
  toEmail: 'admin@example.com',
  variables: {
    userName: 'Test User',
    appName: 'PurposePath',
    dashboardUrl: 'https://app.purposepath.com/dashboard'
  }
});

if (testResult.sent) {
  console.log('Test email sent:', testResult.messageId);
} else {
  console.error('Test failed:', testResult.error);
}
```

#### `getTemplateAnalytics(id: string, params?: AnalyticsParams)`

```typescript
async getTemplateAnalytics(id: string, params: AnalyticsParams = {}): Promise<TemplateAnalytics>
```

**Purpose**: Get email template usage analytics

**Parameters**:

- `id`: Email template ID
- `params`: Optional analytics parameters

**Returns**: Template performance analytics

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

// Get monthly analytics
const analytics = await emailTemplateService.getTemplateAnalytics('template-123', {
  period: 'month'
});

console.log(`Open Rate: ${analytics.rates.openRate}%`);
console.log(`Click Rate: ${analytics.rates.clickRate}%`);
```

### Client-Side Methods (RazorLight Processing) ✅ **NEW - Issue #7**

#### `validateTemplateClientSide(content: string)`

```typescript
validateTemplateClientSide(content: string): { isValid: boolean; errors: Array<{ line: number; message: string }> }
```

**Purpose**: Client-side RazorLight syntax validation (no server calls)

**Features**:

- PascalCase property name validation
- Balanced braces checking
- Conditional syntax validation (@if, @foreach)
- Invalid character detection
- Real-time feedback

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

const validation = emailTemplateService.validateTemplateClientSide(`
  <h1>Welcome @Model.UserName!</h1>
  <p>Email: @Model.userEmail</p>  <!-- Error: lowercase -->
`);

if (!validation.isValid) {
  validation.errors.forEach(error => {
    console.log(`Line ${error.line}: ${error.message}`);
  });
}
```

#### `generatePreviewClientSide(content: string, sampleData: Record<string, any>)`

```typescript
generatePreviewClientSide(content: string, sampleData: Record<string, any> = {}): string
```

**Purpose**: Client-side template preview generation with variable substitution

**Features**:

- Instant preview rendering
- No server round-trips
- Smart sample data generation
- Variable replacement

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

const preview = emailTemplateService.generatePreviewClientSide(
  '<h1>Welcome @Model.UserName!</h1>',
  { UserName: 'John Doe' }
);

console.log(preview); // <h1>Welcome John Doe!</h1>
```

#### `extractTemplateVariables(content: string)`

```typescript
extractTemplateVariables(content: string): string[]
```

**Purpose**: Extract @Model.PropertyName variables from template content

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

const variables = emailTemplateService.extractTemplateVariables(`
  <h1>Welcome @Model.UserName!</h1>
  <p>Your email: @Model.UserEmail</p>
  <p>Business: @Model.BusinessName</p>
`);

console.log(variables); // ['UserName', 'UserEmail', 'BusinessName']
```

#### `generateSampleDataForVariables(variables: string[])`

```typescript
generateSampleDataForVariables(variables: string[]): Record<string, any>
```

**Purpose**: Generate contextual sample data for template variables

**Features**:

- Smart data generation based on variable names
- Realistic sample values
- Date formatting
- URL generation

**Usage Example**:

```typescript
import { emailTemplateService } from '@/services/emailTemplateService';

const sampleData = emailTemplateService.generateSampleDataForVariables([
  'UserName',
  'UserEmail',
  'BusinessName',
  'VerificationUrl',
  'InvoiceDate'
]);

console.log(sampleData);
// {
//   UserName: 'John Doe',
//   UserEmail: 'john.doe@example.com',
//   BusinessName: 'Acme Corporation',
//   VerificationUrl: 'https://app.purposepath.com/verify',
//   InvoiceDate: 'January 15, 2025'
// }
```

## React Query Hooks

### Query Hooks (Server-Side)

#### `useEmailTemplates(params?: EmailTemplateListParams)`

```typescript
function useEmailTemplates(params: EmailTemplateListParams = {})
```

**Purpose**: Fetch email templates with caching and automatic refetching

**Cache Key**: `['emailTemplates', params]`

**Stale Time**: 5 minutes

**Usage Example**:

```typescript
import { useEmailTemplates } from '@/hooks/useEmailTemplates';

function EmailTemplatesList() {
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 20,
    status: 'all' as const,
    category: '',
    search: ''
  });

  const {
    data: templates,
    isLoading,
    error
  } = useEmailTemplates(filters);

  if (isLoading) return <div>Loading templates...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Email Templates ({templates?.pagination.totalCount})</h1>
      
      {/* Filters */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '15px' }}>
        <input
          type="text"
          placeholder="Search templates..."
          value={filters.search}
          onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value, page: 1 }))}
          style={{ flex: 1, padding: '8px' }}
        />
        
        <select
          value={filters.category}
          onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value, page: 1 }))}
          style={{ padding: '8px' }}
        >
          <option value="">All Categories</option>
          <option value="onboarding">Onboarding</option>
          <option value="notifications">Notifications</option>
          <option value="marketing">Marketing</option>
          <option value="system">System</option>
        </select>
        
        <select
          value={filters.status}
          onChange={(e) => setFilters(prev => ({ 
            ...prev, 
            status: e.target.value as 'active' | 'draft' | 'all',
            page: 1 
          }))}
          style={{ padding: '8px' }}
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="draft">Draft</option>
        </select>
      </div>

      {/* Templates Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
        {templates?.items.map(template => (
          <div key={template.id} style={{ 
            border: '1px solid #ddd', 
            padding: '20px', 
            borderRadius: '8px',
            backgroundColor: template.isActive ? 'white' : '#f5f5f5'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: '0 0 5px 0' }}>{template.name}</h3>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                  {template.category} • {template.language}
                </div>
                <p style={{ margin: '0', fontSize: '14px', color: '#666' }}>
                  {template.description}
                </p>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {template.isDefault && (
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '10px',
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
                  fontSize: '10px',
                  backgroundColor: template.isActive ? '#4caf50' : '#757575',
                  color: 'white',
                  textAlign: 'center'
                }}>
                  {template.isActive ? 'ACTIVE' : 'DRAFT'}
                </span>
              </div>
            </div>
            
            {/* Subject Line */}
            <div style={{ marginBottom: '15px' }}>
              <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>
                Subject:
              </div>
              <div style={{ 
                fontSize: '13px', 
                fontStyle: 'italic', 
                color: '#333',
                backgroundColor: '#f8f9fa',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #e9ecef'
              }}>
                {template.subject}
              </div>
            </div>
            
            {/* Variables */}
            {template.variables.length > 0 && (
              <div style={{ marginBottom: '15px' }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>
                  Variables ({template.variables.length}):
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {template.variables.slice(0, 4).map(variable => (
                    <span key={variable.name} style={{
                      padding: '2px 6px',
                      backgroundColor: '#e3f2fd',
                      color: '#1976d2',
                      borderRadius: '12px',
                      fontSize: '10px',
                      fontFamily: 'monospace'
                    }}>
                      {variable.name}
                    </span>
                  ))}
                  {template.variables.length > 4 && (
                    <span style={{ fontSize: '10px', color: '#666' }}>
                      +{template.variables.length - 4} more
                    </span>
                  )}
                </div>
              </div>
            )}
            
            {/* Performance */}
            {template.metadata.openRate !== undefined && (
              <div style={{ marginBottom: '15px' }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>
                  Performance:
                </div>
                <div style={{ fontSize: '11px', color: '#666' }}>
                  📧 Used {template.usageCount} times • 
                  📈 {template.metadata.openRate}% open rate
                  {template.metadata.clickRate && ` • 🖱️ ${template.metadata.clickRate}% click rate`}
                </div>
              </div>
            )}
            
            {/* Tags */}
            {template.metadata.tags.length > 0 && (
              <div style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {template.metadata.tags.slice(0, 3).map(tag => (
                    <span key={tag} style={{
                      padding: '2px 6px',
                      backgroundColor: '#f5f5f5',
                      color: '#666',
                      borderRadius: '12px',
                      fontSize: '10px'
                    }}>
                      #{tag}
                    </span>
                  ))}
                  {template.metadata.tags.length > 3 && (
                    <span style={{ fontSize: '10px', color: '#666' }}>
                      +{template.metadata.tags.length - 3}
                    </span>
                  )}
                </div>
              </div>
            )}
            
            {/* Actions */}
            <div style={{ display: 'flex', gap: '8px', marginTop: '15px' }}>
              <button style={{
                flex: 1,
                padding: '6px 12px',
                fontSize: '12px',
                backgroundColor: '#2196f3',
                color: 'white',
                border: 'none',
                borderRadius: '4px'
              }}>
                Edit
              </button>
              
              <button style={{
                padding: '6px 12px',
                fontSize: '12px',
                backgroundColor: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '4px'
              }}>
                Preview
              </button>
              
              <button style={{
                padding: '6px 12px',
                fontSize: '12px',
                backgroundColor: '#ff9800',
                color: 'white',
                border: 'none',
                borderRadius: '4px'
              }}>
                Test
              </button>
            </div>
            
            <div style={{ fontSize: '11px', color: '#999', marginTop: '10px' }}>
              Updated {new Date(template.updatedAt).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div style={{ marginTop: '30px', textAlign: 'center' }}>
        <button
          disabled={!templates?.pagination.hasPrevious}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
          style={{ marginRight: '10px' }}
        >
          Previous
        </button>
        
        <span style={{ margin: '0 15px' }}>
          Page {templates?.pagination.page} of {templates?.pagination.totalPages}
        </span>
        
        <button
          disabled={!templates?.pagination.hasNext}
          onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
          style={{ marginLeft: '10px' }}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

#### `useEmailTemplate(id: string)`

```typescript
function useEmailTemplate(id: string)
```

**Purpose**: Fetch single email template details

**Cache Key**: `['emailTemplates', id]`

**Stale Time**: 2 minutes

**Usage Example**:

```typescript
import { useEmailTemplate } from '@/hooks/useEmailTemplates';

function EmailTemplateEditor({ templateId }: { templateId: string }) {
  const {
    data: template,
    isLoading,
    error
  } = useEmailTemplate(templateId);

  if (isLoading) return <div>Loading template...</div>;
  if (error) return <div>Error loading template</div>;

  return (
    <div>
      <h1>Edit Template: {template?.name}</h1>
      
      {/* Template editor form would go here */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div>
          <h3>Template Details</h3>
          <p><strong>Category:</strong> {template?.category}</p>
          <p><strong>Language:</strong> {template?.language}</p>
          <p><strong>Status:</strong> {template?.isActive ? 'Active' : 'Draft'}</p>
          <p><strong>Usage Count:</strong> {template?.usageCount}</p>
        </div>
        
        <div>
          <h3>Variables ({template?.variables.length})</h3>
          <ul>
            {template?.variables.map(variable => (
              <li key={variable.name}>
                <code>{variable.name}</code> ({variable.type})
                {variable.required && <span style={{ color: 'red' }}> *</span>}
                <br />
                <small>{variable.description}</small>
              </li>
            ))}
          </ul>
        </div>
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <h3>Subject Line</h3>
        <div style={{ 
          padding: '10px', 
          backgroundColor: '#f8f9fa', 
          border: '1px solid #dee2e6',
          borderRadius: '4px',
          fontFamily: 'monospace'
        }}>
          {template?.subject}
        </div>
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <h3>HTML Content</h3>
        <textarea
          value={template?.htmlContent}
          readOnly
          rows={10}
          style={{ 
            width: '100%', 
            fontFamily: 'monospace', 
            fontSize: '12px',
            padding: '10px'
          }}
        />
      </div>
    </div>
  );
}
```

### Client-Side RazorLight Hooks ✅ **NEW - Issue #7**

#### `useTemplateValidation(content: string)`

```typescript
function useTemplateValidation(content: string)
```

**Purpose**: Real-time RazorLight syntax validation with React Query caching

**Returns**: `{ isValid: boolean; errors: ValidationError[] }`

**Usage Example**:

```typescript
import { useTemplateValidation } from '@/hooks/useEmailTemplates';

function TemplateEditor() {
  const [content, setContent] = useState('');
  const validation = useTemplateValidation(content);

  return (
    <div>
      {validation && !validation.isValid && (
        <Alert severity="warning">
          {validation.errors.length} validation error(s) found
        </Alert>
      )}
    </div>
  );
}
```

#### `useTemplatePreview(content: string, sampleData: Record<string, any>)`

```typescript
function useTemplatePreview(content: string, sampleData: Record<string, any>)
```

**Purpose**: Real-time client-side template preview

**Returns**: Rendered HTML preview

**Usage Example**:

```typescript
import { useTemplatePreview, useGenerateSampleData } from '@/hooks/useEmailTemplates';

function LivePreview({ content }: { content: string }) {
  const variables = extractTemplateVariables(content);
  const sampleData = useGenerateSampleData(variables);
  const preview = useTemplatePreview(content, sampleData);

  return (
    <div dangerouslySetInnerHTML={{ __html: preview || '' }} />
  );
}
```

#### `useExtractTemplateVariables(content: string)`

```typescript
function useExtractTemplateVariables(content: string)
```

**Purpose**: Extract @Model.PropertyName variables from template

**Returns**: Array of variable names

#### `useGenerateSampleData(variables: string[])`

```typescript
function useGenerateSampleData(variables: string[])
```

**Purpose**: Generate contextual sample data for variables

**Returns**: Record of variable names to sample values

#### `useTemplateEditor(content: string)`

```typescript
function useTemplateEditor(content: string)
```

**Purpose**: Complete editor state management combining validation and preview

**Returns**:

```typescript
{
  validation: ValidationResult;
  preview: string;
  variables: string[];
  sampleData: Record<string, any>;
}
```

### Mutation Hooks (Server-Side)

#### `useCreateEmailTemplate()`

```typescript
function useCreateEmailTemplate()
```

**Purpose**: Create new email template with cache invalidation

**Cache Invalidation**: Invalidates email templates list

**Usage Example**:

```typescript
import { useCreateEmailTemplate } from '@/hooks/useEmailTemplates';
import { useToast } from '@/contexts/ToastContext';

function CreateEmailTemplateForm() {
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    description: '',
    category: 'notifications',
    language: 'en',
    htmlContent: '',
    textContent: '',
    variables: [] as TemplateVariable[],
    isActive: true,
    isDefault: false,
    tags: [] as string[],
    notes: ''
  });

  const createTemplate = useCreateEmailTemplate();
  const toast = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    createTemplate.mutate(formData, {
      onSuccess: (newTemplate) => {
        toast.showSuccess(`Email template "${newTemplate.name}" created successfully`);
        // Reset form or navigate away
      },
      onError: (error) => {
        toast.showError(`Failed to create template: ${error.message}`);
      }
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '800px' }}>
      <h2>Create Email Template</h2>
      
      {/* Basic Info */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
          <div>
            <label>Template Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            />
          </div>
          
          <div>
            <label>Category:</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
              style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            >
              <option value="onboarding">Onboarding</option>
              <option value="notifications">Notifications</option>
              <option value="marketing">Marketing</option>
              <option value="system">System</option>
            </select>
          </div>
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Description:</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            required
            rows={2}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Subject Line:</label>
          <input
            type="text"
            value={formData.subject}
            onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
            required
            placeholder="Welcome to {{appName}}, {{userName}}!"
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
          <small style={{ color: '#666' }}>
            Use {'{{'}}variableName{{'}}'}} for dynamic content
          </small>
        </div>
      </div>
      
      {/* Content */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Email Content</h3>
        
        <div style={{ marginBottom: '15px' }}>
          <label>HTML Content:</label>
          <textarea
            value={formData.htmlContent}
            onChange={(e) => setFormData(prev => ({ ...prev, htmlContent: e.target.value }))}
            required
            rows={8}
            style={{ 
              width: '100%', 
              padding: '8px', 
              marginTop: '5px',
              fontFamily: 'monospace',
              fontSize: '12px'
            }}
            placeholder="<h1>Welcome {{userName}}!</h1><p>Thank you for joining {{appName}}.</p>"
          />
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Plain Text Content:</label>
          <textarea
            value={formData.textContent}
            onChange={(e) => setFormData(prev => ({ ...prev, textContent: e.target.value }))}
            required
            rows={6}
            style={{ 
              width: '100%', 
              padding: '8px', 
              marginTop: '5px',
              fontFamily: 'monospace',
              fontSize: '12px'
            }}
            placeholder="Welcome {{userName}}! Thank you for joining {{appName}}."
          />
        </div>
      </div>
      
      {/* Variables */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Template Variables</h3>
        <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
          Define variables used in your template content
        </p>
        
        {/* Variable input form would go here */}
        <div style={{ 
          border: '1px solid #ddd', 
          padding: '15px', 
          borderRadius: '4px',
          backgroundColor: '#f8f9fa'
        }}>
          <p>Variable management interface would be implemented here</p>
        </div>
      </div>
      
      {/* Options */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Options</h3>
        
        <div style={{ display: 'flex', gap: '20px', marginBottom: '15px' }}>
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
            <span style={{ marginLeft: '5px' }}>Default template for category</span>
          </label>
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Tags (comma-separated):</label>
          <input
            type="text"
            value={formData.tags.join(', ')}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              tags: e.target.value.split(',').map(tag => tag.trim()).filter(Boolean)
            }))}
            placeholder="welcome, onboarding, user"
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        
        <div>
          <label>Internal Notes:</label>
          <textarea
            value={formData.notes}
            onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
            rows={2}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
            placeholder="Internal notes about this template..."
          />
        </div>
      </div>
      
      <button
        type="submit"
        disabled={createTemplate.isPending}
        style={{
          padding: '12px 24px',
          backgroundColor: '#2196f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          fontSize: '16px'
        }}
      >
        {createTemplate.isPending ? 'Creating Template...' : 'Create Email Template'}
      </button>
    </form>
  );
}
```

#### `useSendTestEmail()`

```typescript
function useSendTestEmail()
```

**Purpose**: Send test email using template

**Usage Example**:

```typescript
import { useSendTestEmail } from '@/hooks/useEmailTemplates';

function TestEmailButton({ templateId }: { templateId: string }) {
  const [testEmail, setTestEmail] = useState('admin@example.com');
  const sendTest = useSendTestEmail();

  const handleSendTest = () => {
    sendTest.mutate({
      templateId,
      toEmail: testEmail,
      variables: {
        userName: 'Test User',
        appName: 'PurposePath',
        dashboardUrl: 'https://app.purposepath.com/dashboard'
      }
    }, {
      onSuccess: (result) => {
        if (result.sent) {
          alert(`Test email sent successfully! Message ID: ${result.messageId}`);
        } else {
          alert(`Test email failed: ${result.error}`);
        }
      },
      onError: (error) => {
        alert(`Failed to send test email: ${error.message}`);
      }
    });
  };

  return (
    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
      <input
        type="email"
        value={testEmail}
        onChange={(e) => setTestEmail(e.target.value)}
        placeholder="test@example.com"
        style={{ padding: '6px', borderRadius: '4px', border: '1px solid #ccc' }}
      />
      
      <button
        onClick={handleSendTest}
        disabled={sendTest.isPending || !testEmail}
        style={{
          padding: '6px 12px',
          backgroundColor: '#ff9800',
          color: 'white',
          border: 'none',
          borderRadius: '4px'
        }}
      >
        {sendTest.isPending ? 'Sending...' : 'Send Test'}
      </button>
    </div>
  );
}
```

## Error Handling

### Common Error Types

```typescript
enum EmailTemplateErrorType {
  TEMPLATE_NOT_FOUND = 'TEMPLATE_NOT_FOUND',
  TEMPLATE_NAME_EXISTS = 'TEMPLATE_NAME_EXISTS',
  INVALID_HTML_CONTENT = 'INVALID_HTML_CONTENT',
  INVALID_VARIABLES = 'INVALID_VARIABLES',
  MISSING_REQUIRED_VARIABLES = 'MISSING_REQUIRED_VARIABLES',
  EMAIL_SEND_FAILED = 'EMAIL_SEND_FAILED',
  TEMPLATE_IN_USE = 'TEMPLATE_IN_USE'
}
```

### Validation Error Details

```typescript
interface EmailTemplateValidationError {
  field: string;
  message: string;
  code: string;
  details?: any;
}

// Example validation errors
const validationErrors = [
  {
    field: 'htmlContent',
    message: 'Invalid HTML syntax',
    code: 'INVALID_HTML_SYNTAX',
    details: { line: 5, column: 10 }
  },
  {
    field: 'variables',
    message: 'Variable "userName" used in content but not defined',
    code: 'UNDEFINED_VARIABLE',
    details: { variable: 'userName' }
  }
];
```

## RazorLight Template Syntax Guide

**IMPORTANT**: All email templates use **RazorLight** C# templating syntax.

### Basic Syntax

RazorLight uses `@Model.PropertyName` to access dynamic content:

```csharp
// Correct RazorLight syntax
<h1>Welcome @Model.UserName!</h1>
<p>Your email is: @Model.UserEmail</p>
<p>Subscription tier: @Model.SubscriptionTier</p>
```

### Naming Convention - PascalCase Required

All model properties **MUST** use **PascalCase** (first letter capitalized):

✅ **Correct**:

- `@Model.UserName`
- `@Model.UserEmail`
- `@Model.BusinessName`
- `@Model.SubscriptionTier`
- `@Model.ResetPasswordUrl`

❌ **Incorrect**:

- `@Model.userName` (camelCase)
- `@Model.user_name` (snake_case)
- `{{user_name}}` (old syntax - not supported)

### Advanced RazorLight Features

```csharp
// Conditionals
@if (Model.IsPremium) {
    <div class="premium-banner">
        <strong>Premium Member Benefits</strong>
    </div>
}

@if (!string.IsNullOrEmpty(Model.DiscountCode)) {
    <p>Your discount code: <strong>@Model.DiscountCode</strong></p>
}

// Loops
@foreach (var item in Model.OrderItems) {
    <li>@item.Name - @item.Price.ToString("C")</li>
}

// String formatting
<p>Total: @Model.InvoiceAmount.ToString("C")</p>
<p>Date: @Model.InvoiceDate.ToString("MMMM dd, yyyy")</p>

// Null coalescing
<p>Business: @(Model.BusinessName ?? "N/A")</p>

// HTML encoding (automatic by default)
<p>@Model.UserMessage</p>  <!-- Automatically HTML-encoded -->

// Raw HTML (use with caution)
<div>@Html.Raw(Model.TrustedHtmlContent)</div>
```

### Template Variable Definition

When defining variables in the API, use this pattern:

```typescript
{
  name: 'UserName',              // PascalCase for RazorLight
  description: 'User\'s full name',
  type: 'string',
  required: true,
  example: 'John Doe',
  syntaxHint: '@Model.UserName'  // Optional: helps UI display correct syntax
}
```

### Subject Line Syntax

Subject lines also support RazorLight:

```csharp
"Welcome to @Model.AppName, @Model.UserName!"
"Your @Model.SubscriptionTier subscription is active"
"Invoice #@Model.InvoiceNumber for @Model.BusinessName"
```

## Business Rules & Constraints

### Template Content Rules

1. **RazorLight Syntax**: All templates must use valid RazorLight C# syntax
2. **PascalCase Naming**: All model properties must be PascalCase
3. **HTML Validation**: HTML content must be valid and safe
4. **Variable Usage**: All variables used in content must be defined
5. **Required Variables**: Templates must include all required variables for their category
6. **Subject Line**: Cannot be empty and should include relevant variables

### Template Management Rules

1. **Uniqueness**: Template names must be unique within the same category
2. **Default Templates**: Only one default template per category allowed
3. **Active Templates**: At least one active template required per category
4. **Deletion**: Cannot delete templates that are currently in use

### Performance Rules

1. **Content Size**: HTML content should not exceed reasonable size limits
2. **Variable Count**: Limited number of variables to prevent complexity
3. **Preview Generation**: Previews cached for performance
4. **Analytics**: Performance data updated periodically

## Integration Examples

### Complete Email Template Management

```typescript
import React, { useState } from 'react';
import {
  useEmailTemplates,
  useEmailTemplate,
  useCreateEmailTemplate,
  useUpdateEmailTemplate,
  usePreviewTemplate,
  useSendTestEmail,
  useDeleteEmailTemplate
} from '@/hooks/useEmailTemplates';

function EmailTemplateManagement() {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  
  const {
    data: templates,
    isLoading: templatesLoading
  } = useEmailTemplates();

  const {
    data: selectedTemplate,
    isLoading: templateLoading
  } = useEmailTemplate(selectedTemplateId!);

  const deleteTemplate = useDeleteEmailTemplate();
  const sendTest = useSendTestEmail();

  const handleDeleteTemplate = (templateId: string, templateName: string) => {
    if (confirm(`Are you sure you want to delete "${templateName}"?`)) {
      deleteTemplate.mutate(templateId, {
        onSuccess: () => {
          if (selectedTemplateId === templateId) {
            setSelectedTemplateId(null);
          }
        }
      });
    }
  };

  if (templatesLoading) return <div>Loading templates...</div>;

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Templates List */}
      <div style={{ width: '50%', padding: '20px', borderRight: '1px solid #ccc', overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1>Email Templates ({templates?.pagination.totalCount})</h1>
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
            Create Template
          </button>
        </div>

        <div>
          {templates?.items.map(template => (
            <div
              key={template.id}
              onClick={() => setSelectedTemplateId(template.id)}
              style={{
                border: selectedTemplateId === template.id ? '2px solid #2196f3' : '1px solid #ddd',
                padding: '15px',
                marginBottom: '10px',
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: template.isActive ? 'white' : '#f5f5f5'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: '0 0 5px 0' }}>{template.name}</h3>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                    {template.category} • {template.language}
                  </div>
                  <p style={{ margin: '0', fontSize: '14px', color: '#666' }}>
                    {template.description}
                  </p>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {template.isDefault && (
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
                    backgroundColor: template.isActive ? '#4caf50' : '#757575',
                    color: 'white',
                    textAlign: 'center'
                  }}>
                    {template.isActive ? 'ACTIVE' : 'DRAFT'}
                  </span>
                </div>
              </div>
              
              <div style={{ fontSize: '12px', fontStyle: 'italic', color: '#666', marginBottom: '10px' }}>
                "{template.subject}"
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: '#666' }}>
                <div>
                  📧 {template.usageCount} uses
                  {template.metadata.openRate && ` • 📈 ${template.metadata.openRate}% open`}
                </div>
                
                <div>
                  {template.variables.length} variables
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '5px', marginTop: '10px' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowPreview(true);
                  }}
                  style={{
                    padding: '4px 8px',
                    fontSize: '10px',
                    backgroundColor: '#4caf50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px'
                  }}
                >
                  Preview
                </button>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    // Handle test email
                  }}
                  style={{
                    padding: '4px 8px',
                    fontSize: '10px',
                    backgroundColor: '#ff9800',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px'
                  }}
                >
                  Test
                </button>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteTemplate(template.id, template.name);
                  }}
                  style={{
                    padding: '4px 8px',
                    fontSize: '10px',
                    border: '1px solid #f44336',
                    backgroundColor: 'white',
                    color: '#f44336',
                    borderRadius: '3px'
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Template Details */}
      <div style={{ width: '50%', padding: '20px', overflow: 'auto' }}>
        {selectedTemplateId ? (
          templateLoading ? (
            <div>Loading template details...</div>
          ) : selectedTemplate ? (
            <div>
              <h2>{selectedTemplate.name}</h2>
              <p>{selectedTemplate.description}</p>
              
              <div style={{ marginBottom: '20px' }}>
                <h3>Subject Line</h3>
                <div style={{ 
                  padding: '10px', 
                  backgroundColor: '#f8f9fa', 
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  fontStyle: 'italic'
                }}>
                  {selectedTemplate.subject}
                </div>
              </div>
              
              <div style={{ marginBottom: '20px' }}>
                <h3>Variables ({selectedTemplate.variables.length})</h3>
                {selectedTemplate.variables.length > 0 ? (
                  <div style={{ display: 'grid', gap: '8px' }}>
                    {selectedTemplate.variables.map(variable => (
                      <div key={variable.name} style={{ 
                        padding: '8px', 
                        border: '1px solid #ddd', 
                        borderRadius: '4px',
                        fontSize: '13px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <code>{variable.name}</code>
                          <span style={{
                            padding: '2px 6px',
                            backgroundColor: variable.required ? '#f44336' : '#4caf50',
                            color: 'white',
                            borderRadius: '10px',
                            fontSize: '10px'
                          }}>
                            {variable.required ? 'Required' : 'Optional'}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                          {variable.description} ({variable.type})
                        </div>
                        {variable.example && (
                          <div style={{ fontSize: '11px', color: '#999', marginTop: '2px' }}>
                            Example: {variable.example}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#666' }}>No variables defined</p>
                )}
              </div>
              
              <div style={{ marginBottom: '20px' }}>
                <h3>Performance</h3>
                <div style={{ fontSize: '14px' }}>
                  <div>📧 Usage Count: {selectedTemplate.usageCount}</div>
                  {selectedTemplate.metadata.openRate && (
                    <div>📈 Open Rate: {selectedTemplate.metadata.openRate}%</div>
                  )}
                  {selectedTemplate.metadata.clickRate && (
                    <div>🖱️ Click Rate: {selectedTemplate.metadata.clickRate}%</div>
                  )}
                  {selectedTemplate.lastUsed && (
                    <div>🕒 Last Used: {new Date(selectedTemplate.lastUsed).toLocaleString()}</div>
                  )}
                </div>
              </div>
              
              <div style={{ marginBottom: '20px' }}>
                <h3>Content Preview</h3>
                <div style={{ 
                  maxHeight: '300px', 
                  overflow: 'auto', 
                  border: '1px solid #ddd',
                  padding: '10px',
                  backgroundColor: '#f8f9fa'
                }}>
                  <div dangerouslySetInnerHTML={{ __html: selectedTemplate.htmlContent }} />
                </div>
              </div>
              
              <div style={{ fontSize: '12px', color: '#666' }}>
                <div>Created: {new Date(selectedTemplate.createdAt).toLocaleString()}</div>
                <div>Updated: {new Date(selectedTemplate.updatedAt).toLocaleString()}</div>
                <div>Created by: {selectedTemplate.createdBy}</div>
              </div>
            </div>
          ) : (
            <div>Failed to load template details</div>
          )
        ) : (
          <div style={{ textAlign: 'center', marginTop: '50px', color: '#666' }}>
            Select a template to view details
          </div>
        )}
      </div>
    </div>
  );
}
```

## Related Files

- `src/services/emailTemplateService.ts` - Main service implementation
- `src/hooks/useEmailTemplates.ts` - React Query hooks
- `src/types/index.ts` - Type definitions
- `src/components/features/emailTemplates/` - Email template components
- `src/pages/EmailTemplatesPage.tsx` - Main templates page
- `src/pages/EmailTemplateEditorPage.tsx` - Template editor page
