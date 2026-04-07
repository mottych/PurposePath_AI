# Notification Topic Onboarding Guide

Version: 1.0
Date: April 7, 2026
Status: Developer Guide

## 1. Purpose

This guide explains how to add a new notification topic end to end in PurposePath_Api.

It covers:
- Notification contract registration
- Parameter registration
- Resolver method mapping and implementation
- AI topic integration through the intermediate AI orchestrator pattern
- Test and validation requirements

This is an implementation guide for developers and assumes the canonical requirements and design are already approved.

## 2. Architecture Summary

The email notification system uses three registries plus runtime resolver implementations:

1. Notification registry:
- File: PurposePath.Domain/Constants/NotificationEvents.cs
- Defines event metadata and split contracts:
  - RequiredPublisherParameters
  - RequiredTemplateParameters
  - OptionalTemplateParameters

2. Parameter registry:
- File: Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters/TemplateParameterRegistry.cs
- Defines parameter to resolver-method mapping.

3. Retrieval method registry:
- File: Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters/TemplateRetrievalMethodRegistry.cs
- Defines resolver method to required business inputs mapping.

4. Resolver implementations:
- Folder: Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters
- Each method key must have one concrete resolver implementation, except payload_passthrough.

5. AI orchestration boundary:
- File: Services/PurposePath.NotificationProcessor.Lambda/Services/EmailInsights/EmailInsightOrchestrator.cs
- Owns envelope metadata generation and AI call lifecycle.
- Resolver methods should pass business inputs only.

## 3. End-to-End Onboarding Workflow

### Step 1: Define the notification contract

Edit:
- PurposePath.Domain/Constants/NotificationEvents.cs

Add a new NotificationEventDefinition with:
- EventType
- DisplayName
- Description
- Category
- TemplateId
- RequiredPublisherParameters
- RequiredTemplateParameters
- OptionalTemplateParameters
- Optional policy fields where applicable:
  - PreferenceCategory
  - IsMandatory
  - RecipientStrategy

Rules:
- RequiredTemplateParameters and OptionalTemplateParameters must only include parameters defined in NotificationParameters.
- RequiredPublisherParameters must include all business inputs needed by resolver methods for all required and optional template parameters.
- Do not rely on legacy RequiredParameters or OptionalParameters fallback behavior.

### Step 2: Add any new template parameters

Edit:
- PurposePath.Domain/Constants/NotificationParameters.cs

Add constants for every new template variable.

Naming rules:
- Keep names consistent with existing template variable naming conventions.
- Use stable parameter keys because templates and registries depend on them.

### Step 3: Register parameter to resolver-method mapping

Edit:
- Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters/TemplateParameterRegistry.cs

For each new parameter, decide one resolver method:
- payload_passthrough when publisher must provide value directly
- existing DB resolver method where available
- new resolver method key if enrichment source is new
- email_insight_payload for AI-generated template content

Rules:
- Every template parameter used by notifications must be registered.
- Enriched parameters must not be mapped to payload_passthrough unless intentionally approved.

### Step 4: Register resolver method required business inputs

Edit:
- Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters/TemplateRetrievalMethodRegistry.cs

If reusing an existing method key:
- Verify required input list still matches real business inputs.

If adding a new method key:
- Add method name constant in:
  - Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters/TemplateRetrievalMethodDefinition.cs
- Add method definition in TemplateRetrievalMethodRegistry with required business inputs only.

Important:
- Keep method required inputs limited to business inputs.
- Do not include orchestrator metadata fields if those are generated internally by runtime orchestration.

### Step 5: Implement or update resolver method runtime

Add or update implementation in:
- Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters

Resolver implementation requirements:
- Implement ITemplateParameterResolverMethod
- MethodName must match retrieval method registry key
- Resolve only parameters requested in the grouped call
- Return normalized parameter dictionary
- Log enrichment miss/failure as warnings where appropriate

If adding new resolver class:
- Register it in DI:
  - Services/PurposePath.NotificationProcessor.Lambda/Function.cs

### Step 6: AI-specific onboarding pattern

If the new notification relies on AI-generated email insight content, follow this pattern:

1. Parameter mapping:
- Map AI output template parameters to email_insight_payload in TemplateParameterRegistry.

2. Method inputs:
- In TemplateRetrievalMethodRegistry, keep email_insight_payload inputs business-only.
- Example inputs: tenantId, userId, topicId.

3. Intermediate topic method behavior:
- Update AI topic routing and activity-data shaping in:
  - Services/PurposePath.NotificationProcessor.Lambda/Services/EmailInsights/EmailInsightOrchestrator.cs
- Update:
  - ResolveAiTopicId for event-to-topic mapping
  - BuildActivityData for topic-specific business context packaging

4. Metadata envelope handling:
- Keep event and tracing metadata generation inside EmailInsightOrchestrator.
- Do not move envelope metadata requirements into template parameter definitions.

5. AI response mapping:
- Ensure output payload is parsed and mapped through:
  - EmailInsightTemplateParameterResolverMethod
  - EmailInsightTemplateVariableResolver
  - EmailInsightPayloadPipeline

### Step 7: Ensure notification contract propagation is complete

Edit or verify in:
- PurposePath.Domain/Constants/NotificationEvents.cs

Update derived publisher input mapping table for new enriched parameters if needed so required business inputs are propagated consistently.

### Step 8: Add or update tests

Minimum test coverage:

1. Contract registry tests:
- Tests/PurposePath.Integration.Lambda.Tests/Services/NotificationTemplateContractRegistryTests.cs

Add assertions for:
- Parameter registry completeness for new template parameters
- Retrieval method registry completeness for any new method key
- Required publisher inputs include method-derived business inputs
- New method implementation exists if method is non-passthrough

2. Resolver behavior tests:
- Add or update dedicated resolver tests in:
  - Tests/PurposePath.Integration.Lambda.Tests/Services

3. Notification enqueue normalization tests:
- Tests/PurposePath.Application.Tests/Services/NotificationServiceTests.cs

For AI topics ensure coverage for:
- Required business inputs
- Topic category validation where relevant
- Service token generation and authContext structure

### Step 9: Run validation commands

Run at minimum:

1.
- dotnet test Tests/PurposePath.Integration.Lambda.Tests/PurposePath.Integration.Lambda.Tests.csproj -c Debug --nologo -v minimal

2.
- dotnet test Tests/PurposePath.Application.Tests/PurposePath.Application.Tests.csproj -c Debug --nologo -v minimal

Optional full-suite gate before merge:
- task: test-solution or test-solution-quiet

Note:
- E2E may require deployment-time secrets and can fail in local/default environments without those values.

## 4. Developer Checklist

Use this checklist before opening PR:

- Added notification contract with explicit split fields.
- Added all new template parameter constants.
- Registered every new parameter in parameter registry.
- Registered method required business inputs in retrieval method registry.
- Implemented and DI-wired any new non-passthrough resolver.
- For AI topic: updated orchestrator topic mapping and activity data shaping.
- Ensured notification required publisher inputs cover method-derived business inputs.
- Updated or added contract and resolver tests.
- Ran required test projects and confirmed green.
- Updated requirements/design docs when behavior contracts changed.

## 5. Common Mistakes to Avoid

- Putting orchestrator metadata fields into parameter contracts.
- Using template parameters that do not exist in NotificationParameters.
- Adding a retrieval method key without a concrete resolver implementation.
- Forgetting to register new resolver in Function DI.
- Updating mappings without updating contract tests.
- Introducing compatibility aliases that violate approved contract rules.

## 6. Related Docs

- docs/shared/Requirements/notification-email-processing-requirements.md
- docs/shared/design/notification-email-processing-design.md
- docs/shared/Specifications/ai-api/email-insights-api-contract.md
- docs/local/guides/architecture-standards.md
- docs/local/guides/coding-standards.md
