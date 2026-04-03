# Contract Validation - Streamlined Email Insight Cutover Readiness

## Scope
- Issue/PR: #795
- Files checked:
  - PurposePath.Application/Services/NotificationService.cs
  - Services/PurposePath.NotificationProcessor.Lambda/Services/EmailInsights/EmailInsightTemplateVariableResolver.cs
  - Tests/PurposePath.Application.Tests/Services/NotificationServiceTests.cs
  - Tests/PurposePath.Integration.Lambda.Tests/Services/EmailInsightTemplateVariableResolverTests.cs

## Contract Impact
- Contract impact: none for external REST endpoints
- Endpoints reviewed:
  - POST /account/api/v1/auth/register (spot-check: no contract changes in this issue scope)

## Verification
- Request payload unchanged: yes
- Response payload unchanged: yes
- Validation/error behavior unchanged: yes for external REST APIs; internal email-insight orchestration validation expanded for required authContext
- Spec references:
  - docs/shared/Specifications/ai-api/email-insights-api-contract.md
  - docs/shared/Requirements/email-insights-requirements.md

## Evidence
- Generic AI merge path validated:
  - Test: EnqueueNotificationAsync_EmailInsightsEvent_ShouldNormalizeRoutingAndContextParameters
  - Test: Apply_WithValidPayload_MapsEnabledFlatVariables
- Existing goal path parity validated:
  - Test: Apply_WithExistingGoalPathWithoutTopicCategory_MaintainsBackwardCompatibleMerge
- Non-AI template path parity validated:
  - Test: Apply_WithNonAiEventWithoutInsightPayload_PreservesExistingTemplateInputs
- Token propagation assertions validated:
  - authContext.serviceToken emitted from backend token issuance
  - authContext.expiresAtUtc and authContext.issuer derived from issued JWT payload
  - authContext.tokenType=Bearer

## Notes
- This artifact satisfies streamlined-email cutover governance evidence requirements for issue #795.
