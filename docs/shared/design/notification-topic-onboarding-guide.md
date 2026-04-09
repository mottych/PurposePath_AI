# Notification Topic Onboarding Guide

Version: 1.2
Date: April 8, 2026
Status: Developer Guide

## 1. Purpose

This guide explains how to add a new notification topic end to end in PurposePath_Api.

It covers:
- Notification contract registration
- Parameter registration
- Resolver method mapping and implementation
- AI topic integration through the intermediate AI orchestrator pattern (EventBridge-first with API fallback)
- Test and validation requirements

This is an implementation guide for developers and assumes the canonical requirements and design are already approved.

## 2. Architecture Summary

The email notification system uses canonical domain registries plus runtime resolver implementations:

1. Notification registry:
- File: PurposePath.Domain/Constants/NotificationEvents.cs
- Defines canonical NotificationEvent contracts using typed parameter objects:
  - PublisherParameters (IReadOnlyList<NotificationEventParameter>)
  - TemplateParameters (IReadOnlyList<NotificationEventParameter>)

2. Parameter registry:
- Canonical file: PurposePath.Domain/Constants/NotificationParameters.cs
- Defines NotificationParameter objects with ResolutionMethod and the authoritative All collection.
- Runtime projection file: Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters/TemplateParameterRegistry.cs
- Runtime registry auto-registers from NotificationParameters.All.

3. Retrieval method registry:
- Canonical file: PurposePath.Domain/Constants/NotificationResolutionMethods.cs
- Defines NotificationResolutionMethod objects and required publisher inputs.
- NotificationResolutionMethod owns `IsAsync` metadata (`true` for async enrichment methods such as AI).
- Runtime projection file: Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters/TemplateRetrievalMethodRegistry.cs
- Runtime registry must remain aligned with NotificationResolutionMethods.

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

Add a new NotificationEvent with:
- EventType
- DisplayName
- Description
- Category
- TemplateId
- PublisherParameters
- TemplateParameters
- Optional policy fields where applicable:
  - PreferenceCategory
  - IsMandatory
  - RecipientStrategy

Implementation pattern:
- Use CreatePublisherParameters(...) and CreateTemplateParameters(...) helpers.
- Use NotificationParameters.<ParameterName> references instead of raw string keys.

Rules:
- TemplateParameters must only include parameters defined in NotificationParameters.
- PublisherParameters should include explicit business inputs for readability, but canonicalization (EnsureSplitContract) will enforce method-derived required publisher inputs.
- Do not introduce legacy RequiredParameters or OptionalParameters fallback fields.

### Step 2: Add any new template parameters

Edit:
- PurposePath.Domain/Constants/NotificationParameters.cs

Add NotificationParameter entries for every new template variable.

Implementation pattern:
- Create a static readonly NotificationParameter using Create("parameter_name", NotificationResolutionMethods.<Method>)
- Add the parameter to NotificationParameters.All

Naming rules:
- Keep names consistent with existing template variable naming conventions.
- Use stable parameter keys because templates and registries depend on them.

### Step 3: Register parameter to resolver-method mapping

Edit:
- PurposePath.Domain/Constants/NotificationParameters.cs

For each new parameter, decide one resolution method:
- payload_passthrough when publisher must provide value directly
- existing DB resolver method where available
- new resolver method key if enrichment source is new
- email_insight_payload for AI-generated template content

Rules:
- Every template parameter used by notifications must exist in NotificationParameters.All.
- Enriched parameters must not be mapped to payload_passthrough unless intentionally approved.

Note:
- TemplateParameterRegistry is generated from NotificationParameters.All and should not require manual parameter registration.

### Step 4: Register resolver method required business inputs

Edit:
- Canonical: PurposePath.Domain/Constants/NotificationResolutionMethods.cs
- Runtime projection: Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters/TemplateRetrievalMethodRegistry.cs

If reusing an existing method key:
- Verify required input list still matches real business inputs.

If adding a new method key:
- Add method definition in NotificationResolutionMethods with required business inputs only.
- Set `IsAsync` on NotificationResolutionMethod when the method requires asynchronous external orchestration.
- Add corresponding method mapping in TemplateRetrievalMethodRegistry to keep runtime registry aligned.

Important:
- Keep method required inputs limited to business inputs.
- Do not include orchestrator metadata fields if those are generated internally by runtime orchestration.
- Do not encode sync/async behavior in template variables. Sync/async is owned by NotificationResolutionMethod (`IsAsync`).

### Step 5: Implement or update resolver method runtime

Add or update implementation in:
- Services/PurposePath.NotificationProcessor.Lambda/Services/TemplateParameters

Resolver implementation requirements:
- Implement ITemplateParameterResolverMethod
- MethodName must match retrieval method registry key
- Resolve only parameters requested in the grouped call
- Return normalized parameter dictionary
- Log enrichment miss/failure as warnings where appropriate

Resolution ordering requirement:
- Processor resolves methods in two phases:
  1. Sync phase (`IsAsync == false`)
  2. Async phase (`IsAsync == true`)
- Final merge/render executes once after both phases complete.

If adding new resolver class:
- Register it in DI:
  - Services/PurposePath.NotificationProcessor.Lambda/Function.cs

### Step 6: AI-specific onboarding pattern

If the new notification relies on AI-generated email insight content, follow this pattern:

1. Parameter mapping:
- Map AI output template parameters to email_insight_payload in TemplateParameterRegistry.

2. Method inputs:
- In NotificationResolutionMethods (and matching runtime method registry), keep email_insight_payload inputs business-only.
- Example inputs: tenantId, userId, topicId.
- Mark email_insight_payload as async (`IsAsync = true`).

3. Intermediate topic method behavior:
- Update AI topic routing and activity-data shaping in:
  - Services/PurposePath.NotificationProcessor.Lambda/Services/EmailInsights/EmailInsightOrchestrator.cs
- Update:
  - ResolveAiTopicId for event-to-topic mapping
  - BuildActivityData for topic-specific business context packaging

4. Dual transport behavior (final design):
- Primary transport: EventBridge kickoff from backend resolver into AI async execution contract.
- Fallback transport: HTTP `POST /ai/execute-async` using the same canonical request payload contract.
- Contract rule: transport is interchangeable; payload semantics, validation rules, and response mapping remain unchanged.
- Mode isolation rule: EventBridge path is terminal-event-driven and must not API-poll. API polling is allowed only in API fallback mode.
- Fallback transition rule: API fallback starts as a new API-mode attempt when EventBridge publish fails or terminal SLA expires.
- Network rule: API fallback requires outbound HTTPS access on port 443 from backend runtime to AI API host.

5. Metadata envelope handling:
- Keep event and tracing metadata generation inside EmailInsightOrchestrator.
- Do not move envelope metadata requirements into template parameter definitions.

6. AI response mapping:
- Ensure output payload is parsed and mapped through:
  - EmailInsightTemplateParameterResolverMethod
  - EmailInsightTemplateVariableResolver
  - EmailInsightPayloadPipeline

### Step 7: Ensure notification contract propagation is complete

Edit or verify in:
- PurposePath.Domain/Constants/NotificationEvents.cs

No manual mapping table is required.

EnsureSplitContract in NotificationEvents automatically derives required publisher inputs from each template parameter's ResolutionMethod.RequiredPublisherParameters.

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
- Added all new NotificationParameter definitions and included them in NotificationParameters.All.
- Assigned ResolutionMethod on each new NotificationParameter.
- Registered method required business inputs in NotificationResolutionMethods and synchronized runtime method registry.
- Implemented and DI-wired any new non-passthrough resolver.
- For AI topic: updated orchestrator topic mapping and activity data shaping.
- For AI topic: verified EventBridge-first kickoff and API fallback behavior use the same contract payload.
- For AI topic: verified transport-mode isolation (no API polling in EventBridge mode; API polling only in API fallback mode).
- For API fallback: verified outbound HTTPS 443 requirement is documented and reflected in runtime/network policy.
- Verified notification required publisher inputs cover method-derived business inputs via contract tests.
- Updated or added contract and resolver tests.
- Ran required test projects and confirmed green.
- Updated requirements/design docs when behavior contracts changed.

## 5. Common Mistakes to Avoid

- Putting orchestrator metadata fields into parameter contracts.
- Using template parameters that do not exist in NotificationParameters.
- Forgetting to add a new NotificationParameter into NotificationParameters.All.
- Adding a retrieval method key without a concrete resolver implementation.
- Forgetting to register new resolver in Function DI.
- Manually editing TemplateParameterRegistry for parameter mappings instead of assigning ResolutionMethod in NotificationParameters.
- Updating mappings without updating contract tests.
- Introducing compatibility aliases that violate approved contract rules.

## 6. Related Docs

- docs/shared/Requirements/notification-email-processing-requirements.md
- docs/shared/design/notification-email-processing-design.md
- docs/shared/Specifications/ai-api/email-insights-api-contract.md
- docs/local/guides/architecture-standards.md
- docs/local/guides/coding-standards.md
