# LLM Service Integration Guide

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Type System](#type-system)
- [Service Layer](#service-layer)
- [React Hooks](#react-hooks)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Testing](#testing)

## Overview

The LLM Service Integration provides a comprehensive system for managing Large Language Model interactions, configurations, templates, and models within the PurposePath Admin Portal. This infrastructure enables administrators to monitor, configure, and manage AI capabilities across the platform.

### Key Features

- **Interaction Management**: Track and analyze LLM API calls
- **Model Management**: Configure and monitor available AI models
- **Template Management**: Create and maintain prompt templates
- **Configuration Management**: Link templates to models with validation
- **Dashboard Metrics**: Real-time performance and usage analytics
- **Comprehensive Error Handling**: User-friendly error messages with retry logic
- **React Query Integration**: Optimized caching and state management
- **Type Safety**: Full TypeScript support with strict type checking

## Architecture

### Layer Overview

```
┌─────────────────────────────────────────────┐
│           React Components                   │
│     (Pages, UI Components, Forms)           │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│          React Query Hooks                   │
│  (useInteractions, useModels, etc.)         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│          Service Layer                       │
│  (API clients, business logic)              │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│          HTTP Client (Axios)                 │
│      (Base API configuration)               │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        Backend API Endpoints                 │
│  (/admin/llm/interactions, /models, etc.)   │
└─────────────────────────────────────────────┘
```

### Directory Structure

```
src/
├── types/llm/
│   ├── common.ts              # Shared types and enums
│   ├── interactions.ts        # Interaction-related types
│   ├── models.ts              # Model-related types
│   ├── templates.ts           # Template-related types
│   ├── configurations.ts      # Configuration-related types
│   ├── dashboard.ts           # Dashboard/metrics types
│   └── errors.ts              # LLM-specific error types
├── services/llm/
│   ├── interactionService.ts  # Interaction API client
│   ├── modelService.ts        # Model API client
│   ├── templateService.ts     # Template API client
│   ├── configurationService.ts # Configuration API client
│   └── dashboardService.ts    # Dashboard API client
├── hooks/llm/
│   ├── useInteractions.ts     # Interaction hooks
│   ├── useModels.ts           # Model hooks
│   ├── useTemplates.ts        # Template hooks
│   ├── useConfigurations.ts   # Configuration hooks
│   ├── useDashboard.ts        # Dashboard hooks
│   └── useLLMErrorHandler.ts  # Error handling hook
└── utils/
    └── llmErrorHandler.ts     # Error handling utilities
```

## Type System

### Core Enums

```typescript
// LLM Provider types
export enum LLMProvider {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GEMINI = 'gemini',
  OLLAMA = 'ollama'
}

// Status enums
export enum InteractionStatus {
  SUCCESS = 'success',
  ERROR = 'error',
  TIMEOUT = 'timeout',
  RATE_LIMITED = 'rate_limited'
}

export enum ModelStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  DEPRECATED = 'deprecated'
}

export enum TemplateStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  DRAFT = 'draft'
}

export enum ConfigurationStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  DEPRECATED = 'deprecated'
}
```

### Key Interfaces

#### LLMInteraction
```typescript
interface LLMInteraction {
  interaction_code: string;
  timestamp: string; // ISO 8601
  provider: LLMProvider;
  model_code: string;
  template_code?: string;
  configuration_code?: string;
  user_id: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  response_time_ms: number;
  status: InteractionStatus;
  error_message?: string;
  cost_usd?: number;
}
```

#### LLMModel
```typescript
interface LLMModel {
  model_code: string;
  provider: LLMProvider;
  model_name: string;
  display_name: string;
  description: string;
  context_window: number;
  max_output_tokens: number;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
  status: ModelStatus;
  capabilities: string[];
  created_at: string;
  updated_at: string;
}
```

#### LLMTemplate
```typescript
interface LLMTemplate {
  template_code: string;
  template_name: string;
  display_name: string;
  description: string;
  template_content: string;
  template_variables: string[];
  status: TemplateStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}
```

#### LLMConfiguration
```typescript
interface LLMConfiguration {
  configuration_code: string;
  configuration_name: string;
  template_code: string;
  model_code: string;
  temperature: number;
  max_tokens: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  status: ConfigurationStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}
```

## Service Layer

### Service Methods Overview

Each service provides standard CRUD operations and domain-specific methods:

#### LLM Interaction Service (`llmInteractionService`)

```typescript
// Get paginated list of interactions
getInteractions(params?: GetInteractionsParams): Promise<PaginatedResponse<LLMInteraction>>

// Get single interaction by code
getInteraction(interactionCode: string): Promise<LLMInteraction>

// Check template compatibility with model
checkCompatibility(params: {
  templateCode: string;
  modelCode: string;
}): Promise<InteractionCompatibility>
```

**Parameters:**
```typescript
interface GetInteractionsParams {
  page?: number;
  page_size?: number;
  provider?: LLMProvider;
  model_code?: string;
  template_code?: string;
  configuration_code?: string;
  status?: InteractionStatus;
  start_date?: string;
  end_date?: string;
  user_id?: string;
  min_tokens?: number;
  max_tokens?: number;
  min_cost?: number;
  max_cost?: number;
  min_response_time?: number;
  max_response_time?: number;
  sort_by?: 'timestamp' | 'total_tokens' | 'response_time_ms' | 'cost_usd';
  sort_order?: 'asc' | 'desc';
}
```

#### LLM Model Service (`llmModelService`)

```typescript
// Get all models with optional filters
getModels(params?: GetModelsParams): Promise<PaginatedResponse<LLMModel>>

// Get single model by code
getModel(modelCode: string): Promise<LLMModel>

// Create new model
createModel(data: CreateLLMModelData): Promise<LLMModel>

// Update existing model
updateModel(modelCode: string, data: UpdateLLMModelData): Promise<LLMModel>

// Delete model
deleteModel(modelCode: string): Promise<void>

// Get usage statistics
getModelUsage(modelCode: string, params?: UsageStatsParams): Promise<ModelUsageStats>
```

#### LLM Template Service (`llmTemplateService`)

```typescript
// Get all templates
getTemplates(params?: GetTemplatesParams): Promise<PaginatedResponse<LLMTemplate>>

// Get single template
getTemplate(templateCode: string): Promise<LLMTemplate>

// Create template
createTemplate(data: CreateLLMTemplateData): Promise<LLMTemplate>

// Update template
updateTemplate(templateCode: string, data: UpdateLLMTemplateData): Promise<LLMTemplate>

// Delete template
deleteTemplate(templateCode: string): Promise<void>

// Validate template syntax
validateTemplate(params: {
  templateContent: string;
  variables?: Record<string, any>;
}): Promise<TemplateValidation>
```

#### LLM Configuration Service (`llmConfigurationService`)

```typescript
// Get all configurations
getConfigurations(params?: GetConfigurationsParams): Promise<PaginatedResponse<LLMConfiguration>>

// Get single configuration
getConfiguration(configCode: string): Promise<LLMConfiguration>

// Create configuration
createConfiguration(data: CreateLLMConfigurationData): Promise<LLMConfiguration>

// Update configuration
updateConfiguration(configCode: string, data: UpdateLLMConfigurationData): Promise<LLMConfiguration>

// Delete configuration
deleteConfiguration(configCode: string): Promise<void>

// Test configuration
testConfiguration(configCode: string, testData: {
  variables?: Record<string, any>;
}): Promise<ConfigurationTestResult>
```

#### LLM Dashboard Service (`llmDashboardService`)

```typescript
// Get overview metrics
getMetrics(params?: DashboardMetricsParams): Promise<LLMDashboardMetrics>

// Get provider breakdown
getProviderStats(params?: StatsParams): Promise<ProviderStats[]>

// Get model performance
getModelPerformance(params?: StatsParams): Promise<ModelPerformanceStats[]>

// Get cost analysis
getCostAnalysis(params?: CostAnalysisParams): Promise<CostAnalysis>

// Get usage trends
getUsageTrends(params?: TrendsParams): Promise<UsageTrends>
```

## React Hooks

### Query Hooks (Data Fetching)

#### Interaction Hooks

```typescript
// Get list of interactions with filters
const { data, isLoading, error, refetch } = useLLMInteractions({
  page: 1,
  page_size: 20,
  provider: LLMProvider.OPENAI,
  status: InteractionStatus.SUCCESS,
  start_date: '2025-01-01',
  end_date: '2025-01-31'
});

// Get single interaction
const { data: interaction } = useLLMInteraction('INTR-001');

// Check template-model compatibility
const { data: compatibility } = useInteractionCompatibility({
  templateCode: 'TMPL-001',
  modelCode: 'MOD-GPT4',
  enabled: true // Only fetch when needed
});
```

#### Model Hooks

```typescript
// Get all models
const { data: models } = useLLMModels({
  provider: LLMProvider.OPENAI,
  status: ModelStatus.ACTIVE
});

// Get single model
const { data: model } = useLLMModel('MOD-GPT4');

// Get model usage stats
const { data: usage } = useModelUsage('MOD-GPT4', {
  start_date: '2025-01-01',
  end_date: '2025-01-31'
});
```

#### Template Hooks

```typescript
// Get all templates
const { data: templates } = useLLMTemplates({
  status: TemplateStatus.ACTIVE
});

// Get single template
const { data: template } = useLLMTemplate('TMPL-001');
```

#### Configuration Hooks

```typescript
// Get all configurations
const { data: configs } = useLLMConfigurations({
  status: ConfigurationStatus.ACTIVE
});

// Get single configuration
const { data: config } = useLLMConfiguration('CONF-001');
```

#### Dashboard Hooks

```typescript
// Get overview metrics
const { data: metrics } = useLLMMetrics({
  start_date: '2025-01-01',
  end_date: '2025-01-31'
});

// Get provider statistics
const { data: providerStats } = useProviderStats();

// Get model performance
const { data: performance } = useModelPerformance();

// Get cost analysis
const { data: costs } = useCostAnalysis({
  groupBy: 'provider'
});

// Get usage trends
const { data: trends } = useUsageTrends({
  interval: 'daily'
});
```

### Mutation Hooks (Data Modification)

#### Model Mutations

```typescript
// Create model
const createModel = useCreateLLMModel({
  onSuccess: (newModel) => {
    console.log('Model created:', newModel.model_code);
  },
  onError: (error) => {
    console.error('Failed to create model:', error);
  }
});

createModel.mutate({
  model_code: 'MOD-GPT4',
  provider: LLMProvider.OPENAI,
  model_name: 'gpt-4',
  display_name: 'GPT-4',
  description: 'OpenAI GPT-4 model',
  context_window: 8192,
  max_output_tokens: 4096,
  input_cost_per_1k: 0.03,
  output_cost_per_1k: 0.06,
  status: ModelStatus.ACTIVE,
  capabilities: ['chat', 'completion', 'function-calling']
});

// Update model
const updateModel = useUpdateLLMModel();
updateModel.mutate({
  modelCode: 'MOD-GPT4',
  data: {
    status: ModelStatus.DEPRECATED,
    description: 'Deprecated - use GPT-4 Turbo'
  }
});

// Delete model
const deleteModel = useDeleteLLMModel();
deleteModel.mutate('MOD-GPT4');
```

#### Template Mutations

```typescript
// Create template
const createTemplate = useCreateLLMTemplate();
createTemplate.mutate({
  template_code: 'TMPL-SUMMARY',
  template_name: 'document_summary',
  display_name: 'Document Summary',
  description: 'Summarizes documents',
  template_content: 'Summarize the following: {{document}}',
  template_variables: ['document'],
  status: TemplateStatus.ACTIVE
});

// Update template
const updateTemplate = useUpdateLLMTemplate();
updateTemplate.mutate({
  templateCode: 'TMPL-SUMMARY',
  data: {
    template_content: 'Provide a concise summary: {{document}}'
  }
});

// Delete template
const deleteTemplate = useDeleteLLMTemplate();
deleteTemplate.mutate('TMPL-SUMMARY');

// Validate template
const validateTemplate = useValidateLLMTemplate();
validateTemplate.mutate({
  templateContent: 'Hello {{name}}, your email is {{email}}',
  variables: {
    name: 'John',
    email: 'john@example.com'
  }
});
```

#### Configuration Mutations

```typescript
// Create configuration
const createConfig = useCreateLLMConfiguration();
createConfig.mutate({
  configuration_code: 'CONF-001',
  configuration_name: 'summary_config',
  template_code: 'TMPL-SUMMARY',
  model_code: 'MOD-GPT4',
  temperature: 0.7,
  max_tokens: 500,
  status: ConfigurationStatus.ACTIVE
});

// Update configuration
const updateConfig = useUpdateLLMConfiguration();
updateConfig.mutate({
  configCode: 'CONF-001',
  data: {
    temperature: 0.5,
    max_tokens: 1000
  }
});

// Delete configuration
const deleteConfig = useDeleteLLMConfiguration();
deleteConfig.mutate('CONF-001');

// Test configuration
const testConfig = useTestLLMConfiguration();
testConfig.mutate({
  configCode: 'CONF-001',
  testData: {
    variables: {
      document: 'Sample document text...'
    }
  }
});
```

## Error Handling

### Error Types

The system defines 12 specific error types for comprehensive error handling:

```typescript
enum LLMErrorCode {
  // Interaction errors
  INTERACTION_NOT_FOUND = 'INTERACTION_NOT_FOUND',
  INTERACTION_FETCH_FAILED = 'INTERACTION_FETCH_FAILED',
  
  // Model errors
  MODEL_NOT_FOUND = 'MODEL_NOT_FOUND',
  MODEL_RATE_LIMIT = 'MODEL_RATE_LIMIT',
  
  // Template errors
  TEMPLATE_NOT_FOUND = 'TEMPLATE_NOT_FOUND',
  TEMPLATE_VALIDATION_FAILED = 'TEMPLATE_VALIDATION_FAILED',
  TEMPLATE_COMPATIBILITY_ERROR = 'TEMPLATE_COMPATIBILITY_ERROR',
  
  // Configuration errors
  CONFIGURATION_NOT_FOUND = 'CONFIGURATION_NOT_FOUND',
  CONFIGURATION_CONFLICT = 'CONFIGURATION_CONFLICT',
  CONFIGURATION_TEST_FAILED = 'CONFIGURATION_TEST_FAILED',
  
  // General errors
  BULK_OPERATION_FAILED = 'BULK_OPERATION_FAILED',
  NETWORK_ERROR = 'NETWORK_ERROR'
}
```

### Error Handler Utility

```typescript
import { LLMErrorHandler } from '@/utils/llmErrorHandler';

// Normalize any error to LLMError
try {
  await llmModelService.createModel(data);
} catch (error) {
  const llmError = LLMErrorHandler.normalize(error);
  
  // Get user-friendly message
  const message = LLMErrorHandler.getUserMessage(llmError);
  console.error(message);
  
  // Check if retryable
  if (LLMErrorHandler.isRetryable(llmError)) {
    const delay = LLMErrorHandler.getRetryDelay(llmError);
    setTimeout(() => retry(), delay);
  }
}
```

### Error Handling Hook

```typescript
import { useLLMErrorHandler } from '@/hooks/llm/useLLMErrorHandler';

function MyComponent() {
  const { handleError, toast } = useLLMErrorHandler();
  
  const createModel = useCreateLLMModel({
    onError: (error) => {
      handleError(error, {
        action: 'creating model',
        details: { model_code: 'MOD-001' }
      });
    }
  });
  
  return (
    <Button onClick={() => createModel.mutate(modelData)}>
      Create Model
    </Button>
  );
}
```

### Specialized Error Handling

#### Configuration Conflicts

```typescript
try {
  await createConfiguration(data);
} catch (error) {
  const llmError = LLMErrorHandler.normalize(error);
  
  if (LLMErrorHandler.requiresConflictResolution(llmError)) {
    const resolutions = LLMErrorHandler.getConflictResolutions(llmError);
    // Show resolution options to user
    resolutions.forEach(resolution => {
      console.log(`Option: ${resolution.type}`, resolution.suggestion);
    });
  }
}
```

#### Validation Errors

```typescript
try {
  await validateTemplate(templateData);
} catch (error) {
  const llmError = LLMErrorHandler.normalize(error);
  const validationErrors = LLMErrorHandler.getValidationErrors(llmError);
  const warnings = LLMErrorHandler.getValidationWarnings(llmError);
  
  // Display errors to user
  validationErrors.forEach(err => {
    console.error(`${err.field}: ${err.message}`);
  });
}
```

## Usage Examples

### Example 1: Interaction List with Filters

```typescript
import React, { useState } from 'react';
import { useLLMInteractions } from '@/hooks/llm/useInteractions';
import { LLMProvider, InteractionStatus } from '@/types/llm/common';

function InteractionList() {
  const [page, setPage] = useState(1);
  const [provider, setProvider] = useState<LLMProvider | undefined>();
  
  const { data, isLoading, error } = useLLMInteractions({
    page,
    page_size: 20,
    provider,
    status: InteractionStatus.SUCCESS,
    sort_by: 'timestamp',
    sort_order: 'desc'
  });
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <select onChange={(e) => setProvider(e.target.value as LLMProvider)}>
        <option value="">All Providers</option>
        <option value={LLMProvider.OPENAI}>OpenAI</option>
        <option value={LLMProvider.ANTHROPIC}>Anthropic</option>
      </select>
      
      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Provider</th>
            <th>Model</th>
            <th>Tokens</th>
            <th>Cost</th>
            <th>Response Time</th>
          </tr>
        </thead>
        <tbody>
          {data?.results.map(interaction => (
            <tr key={interaction.interaction_code}>
              <td>{interaction.interaction_code}</td>
              <td>{interaction.provider}</td>
              <td>{interaction.model_code}</td>
              <td>{interaction.total_tokens}</td>
              <td>${interaction.cost_usd?.toFixed(4)}</td>
              <td>{interaction.response_time_ms}ms</td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <div>
        <button 
          disabled={!data?.has_previous} 
          onClick={() => setPage(p => p - 1)}
        >
          Previous
        </button>
        <span>Page {page} of {data?.total_pages}</span>
        <button 
          disabled={!data?.has_next} 
          onClick={() => setPage(p => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

### Example 2: Model Management Form

```typescript
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateLLMModel } from '@/hooks/llm/useModels';
import { useLLMErrorHandler } from '@/hooks/llm/useLLMErrorHandler';
import { LLMProvider, ModelStatus } from '@/types/llm/common';

const modelSchema = z.object({
  model_code: z.string().min(1),
  provider: z.nativeEnum(LLMProvider),
  model_name: z.string().min(1),
  display_name: z.string().min(1),
  description: z.string(),
  context_window: z.number().positive(),
  max_output_tokens: z.number().positive(),
  input_cost_per_1k: z.number().nonnegative(),
  output_cost_per_1k: z.number().nonnegative(),
  capabilities: z.array(z.string())
});

type ModelFormData = z.infer<typeof modelSchema>;

function CreateModelForm() {
  const { handleError } = useLLMErrorHandler();
  const { register, handleSubmit, formState: { errors } } = useForm<ModelFormData>({
    resolver: zodResolver(modelSchema)
  });
  
  const createModel = useCreateLLMModel({
    onSuccess: (model) => {
      console.log('Model created successfully:', model.model_code);
    },
    onError: (error) => {
      handleError(error, {
        action: 'creating model'
      });
    }
  });
  
  const onSubmit = (data: ModelFormData) => {
    createModel.mutate({
      ...data,
      status: ModelStatus.ACTIVE
    });
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label>Model Code</label>
        <input {...register('model_code')} />
        {errors.model_code && <span>{errors.model_code.message}</span>}
      </div>
      
      <div>
        <label>Provider</label>
        <select {...register('provider')}>
          <option value={LLMProvider.OPENAI}>OpenAI</option>
          <option value={LLMProvider.ANTHROPIC}>Anthropic</option>
          <option value={LLMProvider.GEMINI}>Google Gemini</option>
        </select>
      </div>
      
      <div>
        <label>Model Name</label>
        <input {...register('model_name')} />
      </div>
      
      <div>
        <label>Display Name</label>
        <input {...register('display_name')} />
      </div>
      
      <div>
        <label>Description</label>
        <textarea {...register('description')} />
      </div>
      
      <div>
        <label>Context Window</label>
        <input type="number" {...register('context_window', { valueAsNumber: true })} />
      </div>
      
      <div>
        <label>Max Output Tokens</label>
        <input type="number" {...register('max_output_tokens', { valueAsNumber: true })} />
      </div>
      
      <div>
        <label>Input Cost per 1K tokens (USD)</label>
        <input 
          type="number" 
          step="0.0001" 
          {...register('input_cost_per_1k', { valueAsNumber: true })} 
        />
      </div>
      
      <div>
        <label>Output Cost per 1K tokens (USD)</label>
        <input 
          type="number" 
          step="0.0001" 
          {...register('output_cost_per_1k', { valueAsNumber: true })} 
        />
      </div>
      
      <button type="submit" disabled={createModel.isPending}>
        {createModel.isPending ? 'Creating...' : 'Create Model'}
      </button>
    </form>
  );
}
```

### Example 3: Dashboard Overview

```typescript
import React from 'react';
import { 
  useLLMMetrics, 
  useProviderStats, 
  useModelPerformance 
} from '@/hooks/llm/useDashboard';

function LLMDashboard() {
  const { data: metrics, isLoading: metricsLoading } = useLLMMetrics({
    start_date: '2025-01-01',
    end_date: '2025-01-31'
  });
  
  const { data: providerStats } = useProviderStats();
  const { data: modelPerformance } = useModelPerformance();
  
  if (metricsLoading) return <div>Loading dashboard...</div>;
  
  return (
    <div>
      <h1>LLM Dashboard</h1>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Total Requests</h3>
          <p>{metrics?.total_requests.toLocaleString()}</p>
        </div>
        
        <div className="metric-card">
          <h3>Total Tokens</h3>
          <p>{metrics?.total_tokens.toLocaleString()}</p>
        </div>
        
        <div className="metric-card">
          <h3>Total Cost</h3>
          <p>${metrics?.total_cost_usd.toFixed(2)}</p>
        </div>
        
        <div className="metric-card">
          <h3>Avg Response Time</h3>
          <p>{metrics?.average_response_time_ms.toFixed(0)}ms</p>
        </div>
        
        <div className="metric-card">
          <h3>Success Rate</h3>
          <p>{(metrics?.success_rate * 100).toFixed(1)}%</p>
        </div>
      </div>
      
      <div className="provider-stats">
        <h2>Provider Breakdown</h2>
        <table>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Requests</th>
              <th>Tokens</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {providerStats?.map(stat => (
              <tr key={stat.provider}>
                <td>{stat.provider}</td>
                <td>{stat.total_requests}</td>
                <td>{stat.total_tokens}</td>
                <td>${stat.total_cost.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="model-performance">
        <h2>Model Performance</h2>
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Requests</th>
              <th>Avg Tokens</th>
              <th>Avg Response</th>
              <th>Success Rate</th>
            </tr>
          </thead>
          <tbody>
            {modelPerformance?.map(perf => (
              <tr key={perf.model_code}>
                <td>{perf.model_code}</td>
                <td>{perf.total_requests}</td>
                <td>{perf.average_tokens.toFixed(0)}</td>
                <td>{perf.average_response_time.toFixed(0)}ms</td>
                <td>{(perf.success_rate * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

### Example 4: Template Compatibility Check

```typescript
import React, { useState } from 'react';
import { useInteractionCompatibility } from '@/hooks/llm/useInteractions';
import { useLLMTemplates } from '@/hooks/llm/useTemplates';
import { useLLMModels } from '@/hooks/llm/useModels';

function CompatibilityChecker() {
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  
  const { data: templates } = useLLMTemplates({ status: 'active' });
  const { data: models } = useLLMModels({ status: 'active' });
  
  const { data: compatibility, isLoading } = useInteractionCompatibility({
    templateCode: selectedTemplate,
    modelCode: selectedModel,
    enabled: !!(selectedTemplate && selectedModel)
  });
  
  return (
    <div>
      <h2>Check Template-Model Compatibility</h2>
      
      <div>
        <label>Template</label>
        <select 
          value={selectedTemplate} 
          onChange={(e) => setSelectedTemplate(e.target.value)}
        >
          <option value="">Select a template...</option>
          {templates?.results.map(t => (
            <option key={t.template_code} value={t.template_code}>
              {t.display_name}
            </option>
          ))}
        </select>
      </div>
      
      <div>
        <label>Model</label>
        <select 
          value={selectedModel} 
          onChange={(e) => setSelectedModel(e.target.value)}
        >
          <option value="">Select a model...</option>
          {models?.results.map(m => (
            <option key={m.model_code} value={m.model_code}>
              {m.display_name}
            </option>
          ))}
        </select>
      </div>
      
      {isLoading && <div>Checking compatibility...</div>}
      
      {compatibility && (
        <div className={`compatibility-result ${compatibility.is_compatible ? 'compatible' : 'incompatible'}`}>
          <h3>{compatibility.is_compatible ? '✓ Compatible' : '✗ Incompatible'}</h3>
          
          {compatibility.compatibility_score && (
            <p>Compatibility Score: {(compatibility.compatibility_score * 100).toFixed(0)}%</p>
          )}
          
          {compatibility.warnings && compatibility.warnings.length > 0 && (
            <div className="warnings">
              <h4>Warnings:</h4>
              <ul>
                {compatibility.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
          
          {compatibility.issues && compatibility.issues.length > 0 && (
            <div className="issues">
              <h4>Issues:</h4>
              <ul>
                {compatibility.issues.map((issue, i) => (
                  <li key={i}>
                    <strong>{issue.severity}:</strong> {issue.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

## Best Practices

### 1. Error Handling

Always use the error handler hook in components:

```typescript
const { handleError } = useLLMErrorHandler();

const mutation = useSomeMutation({
  onError: (error) => {
    handleError(error, {
      action: 'performing operation',
      details: { /* relevant context */ }
    });
  }
});
```

### 2. Query Invalidation

Invalidate related queries after mutations:

```typescript
import { llmQueryKeys } from '@/config/queryClient';
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();

const createModel = useCreateLLMModel({
  onSuccess: () => {
    // Invalidate all model queries
    queryClient.invalidateQueries({ 
      queryKey: llmQueryKeys.models.all 
    });
  }
});
```

### 3. Loading States

Always handle loading states in components:

```typescript
const { data, isLoading, error } = useLLMModels();

if (isLoading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
if (!data) return null;

return <ModelList models={data.results} />;
```

### 4. Pagination

Use consistent pagination patterns:

```typescript
const [page, setPage] = useState(1);
const PAGE_SIZE = 20;

const { data } = useLLMInteractions({
  page,
  page_size: PAGE_SIZE
});

// Navigation
<Pagination
  currentPage={page}
  totalPages={data?.total_pages ?? 1}
  onPageChange={setPage}
  hasNext={data?.has_next}
  hasPrevious={data?.has_previous}
/>
```

### 5. Type Safety

Always use proper TypeScript types:

```typescript
import type { 
  LLMModel, 
  CreateLLMModelData 
} from '@/types/llm/models';

// Type function parameters
function renderModel(model: LLMModel) {
  return <ModelCard model={model} />;
}

// Type mutation data
const createModel = useCreateLLMModel();
const modelData: CreateLLMModelData = {
  // TypeScript will ensure all required fields are present
};
createModel.mutate(modelData);
```

### 6. Conditional Fetching

Use the `enabled` option to control when queries run:

```typescript
const { data } = useInteractionCompatibility({
  templateCode,
  modelCode,
  enabled: !!(templateCode && modelCode) // Only fetch when both are selected
});
```

### 7. Optimistic Updates

For better UX, use optimistic updates:

```typescript
const updateModel = useUpdateLLMModel({
  onMutate: async (variables) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ 
      queryKey: llmQueryKeys.models.detail(variables.modelCode) 
    });
    
    // Snapshot previous value
    const previous = queryClient.getQueryData(
      llmQueryKeys.models.detail(variables.modelCode)
    );
    
    // Optimistically update
    queryClient.setQueryData(
      llmQueryKeys.models.detail(variables.modelCode),
      (old: LLMModel) => ({ ...old, ...variables.data })
    );
    
    return { previous };
  },
  onError: (err, variables, context) => {
    // Rollback on error
    if (context?.previous) {
      queryClient.setQueryData(
        llmQueryKeys.models.detail(variables.modelCode),
        context.previous
      );
    }
  },
  onSettled: (data, error, variables) => {
    // Refetch to ensure sync
    queryClient.invalidateQueries({ 
      queryKey: llmQueryKeys.models.detail(variables.modelCode) 
    });
  }
});
```

## Testing

### Unit Tests

The LLM service layer includes comprehensive unit tests:

- **Error Handler Tests** (33 tests): Error normalization, message generation, retry logic
- **Type Guard Tests** (13 tests): Type validation and guards
- **Service Tests** (8 tests): API client methods, mocking, error handling
- **Hook Tests** (10 tests): React Query integration, state management

### Running Tests

```bash
# Run all tests
npm test

# Run tests in CI mode
npm run test:run

# Run with coverage
npm run test:coverage

# Run with UI
npm run test:ui
```

### Test Coverage

All LLM-specific modules have 100% test coverage:
- Types and error types
- Error handler utility
- Service layer (interaction service)
- React hooks (interaction hooks)

### Writing Tests

Use the provided test utilities:

```typescript
import { renderWithQueryClient, waitForLoadingToFinish } from '@/test/utils';
import { screen } from '@testing-library/react';

test('renders model list', async () => {
  renderWithQueryClient(<ModelList />);
  
  await waitForLoadingToFinish();
  
  expect(screen.getByText('GPT-4')).toBeInTheDocument();
});
```

## API Endpoint Reference

All LLM endpoints are prefixed with `/admin/llm/`:

### Interactions
- `GET /admin/llm/interactions` - List interactions
- `GET /admin/llm/interactions/:code` - Get interaction details
- `POST /admin/llm/interactions/compatibility` - Check compatibility

### Models
- `GET /admin/llm/models` - List models
- `GET /admin/llm/models/:code` - Get model details
- `POST /admin/llm/models` - Create model
- `PUT /admin/llm/models/:code` - Update model
- `DELETE /admin/llm/models/:code` - Delete model
- `GET /admin/llm/models/:code/usage` - Get model usage stats

### Templates
- `GET /admin/llm/templates` - List templates
- `GET /admin/llm/templates/:code` - Get template details
- `POST /admin/llm/templates` - Create template
- `PUT /admin/llm/templates/:code` - Update template
- `DELETE /admin/llm/templates/:code` - Delete template
- `POST /admin/llm/templates/validate` - Validate template

### Configurations
- `GET /admin/llm/configurations` - List configurations
- `GET /admin/llm/configurations/:code` - Get configuration details
- `POST /admin/llm/configurations` - Create configuration
- `PUT /admin/llm/configurations/:code` - Update configuration
- `DELETE /admin/llm/configurations/:code` - Delete configuration
- `POST /admin/llm/configurations/:code/test` - Test configuration

### Dashboard
- `GET /admin/llm/dashboard/metrics` - Get overview metrics
- `GET /admin/llm/dashboard/providers` - Get provider statistics
- `GET /admin/llm/dashboard/models/performance` - Get model performance
- `GET /admin/llm/dashboard/costs` - Get cost analysis
- `GET /admin/llm/dashboard/trends` - Get usage trends

---

## Support and Maintenance

For issues, questions, or contributions related to the LLM service integration, please refer to the main project documentation and follow the established Git workflow for pull requests.
