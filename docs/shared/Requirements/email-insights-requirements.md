# Email Insights - Business Requirements (v1 Pilot + Dispatch Cutover Controls)

**Version:** 1.2  
**Date:** March 27, 2026  
**Status:** Proposed for Review (Generic AI Insight + Service Token Extension)

---

## 1. Purpose and Intent

PurposePath will introduce a new capability that sends users meaningful, activity-based insight emails.  
These messages will recognize progress, provide short guidance, and suggest next steps after specific actions in the product.

The first pilot use case is sending an insight email after a user creates a goal.

---

## 2. Business Outcomes

The capability is intended to:

- Increase user momentum immediately after key actions.
- Improve consistency in follow-through and execution.
- Create higher perceived value from the platform through timely guidance.
- Increase email engagement quality by making messages relevant and action-oriented.

---

## 3. Scope (v1 Pilot)

Included in v1:

- Activity-driven insight email for **goal creation**.
- AI-generated insight content embedded into existing email communication.
- Use of existing branded email templates with a dynamic insight section.
- Safe fallback behavior when AI content is unavailable or invalid.

Out of scope for v1:

- Broad rollout to all activity types.
- New standalone email channels or separate campaign tooling.
- Advanced personalization beyond approved pilot context.

---

## 4. Key Capabilities

### 4.1 Event-Based Triggering

- The system should detect when a user creates a goal and trigger an insight email flow.
- The trigger should be reliable, traceable, and idempotent.

### 4.2 AI-Generated Insight Section

- The message should include a short, clear insight section tailored to the user action.
- The insight should be encouraging, practical, and provide suggested next steps.
- The final email must remain readable in both primary email formats supported by the platform.

### 4.3 Template-Driven Communication

- Existing email templates remain the primary structure for brand consistency.
- AI content is embedded as a controlled runtime section, not a full replacement of template content.

### 4.4 Admin-Controlled Prompting

- Content strategy must remain configurable through existing admin prompt management workflows.
- Teams should be able to define topic behavior and guidance without rebuilding delivery flows.

### 4.5 Reliable Fallback Behavior

- If AI output cannot be used, the email should still be delivered using template-only content.
- User communication continuity is prioritized over AI completeness.

### 4.6 Observability and Governance

- The system should provide clear visibility into success, fallback, and quality outcomes.
- Teams should be able to track pilot performance and make informed rollout decisions.

---

## 5. User Experience Requirements

- The email should feel timely and context-aware after goal creation.
- Tone should be supportive and professional.
- Guidance should be concise and actionable.
- Content should avoid over-claiming and remain trustworthy.

---

## 6. Stakeholder Value

### Product and Growth

- Better activation and early retention signals.
- Increased completion likelihood of newly created goals.
- Stronger user perception of "helpful intelligence" in the product experience.

### Customer Success

- Additional touchpoint that nudges users toward productive behaviors.
- Better narrative for onboarding and success coaching.

### Operations and Compliance

- Controlled content pipeline with predictable fallback behavior.
- Auditable outcomes and measurable pilot performance.

---

## 7. Success Measures (Pilot)

Pilot success should be evaluated with agreed business metrics, such as:

- Delivery reliability for triggered insight emails.
- Engagement uplift versus comparable non-insight messages.
- Early behavior lift after goal creation (for example, follow-up actions within target time window).
- Fallback rate and trend reduction over pilot iterations.

---

## 8. Rollout Requirements

- Start with a controlled pilot audience and one trigger topic.
- Monitor quality and reliability before expanding to additional activities.
- Add new insight topics incrementally based on business impact and operational confidence.

---

## 9. Risks and Mitigations (Business View)

- **Risk:** Insight quality inconsistency.  
  **Mitigation:** Controlled prompt governance and pilot review loops.

- **Risk:** AI dependency affects communication continuity.  
  **Mitigation:** Template-first fallback policy ensures emails still send.

- **Risk:** Stakeholder concern over message safety or tone.  
  **Mitigation:** Guardrails, review criteria, and monitored rollout.

---

## 10. Approval Statement

These requirements define the approved business scope and expected value for the v1 `goal_created_email_insight` pilot.

---

## 11. Generic AI Insight Template Merge Requirements (Any Eligible Template)

These requirements extend the pilot model so any eligible email template can include AI-generated content using a topic-based runtime parameter.

### 11.1 Generic Topic Model

- The email enrichment system must support AI insights for any approved email topic, not only `goal_created_email_insight`.
- A topic must be onboarded by:
  - adding an email topic to the email topic registry;
  - wiring the topic to a triggering business event;
  - associating the topic with template/config metadata.
- Topic onboarding should not require new merge-engine code per topic.

### 11.2 Admin Template Authoring Model

- Admin users must be able to embed a predefined AI-insight parameter in templates, similar to existing predefined merge parameters.
- The predefined AI-insight parameter must include or resolve the target AI insight topic.
- If a template does not include an AI-insight parameter, the existing non-AI template merge path remains unchanged.

### 11.3 Runtime Merge Behavior

- During template merge, when a template includes the predefined AI-insight parameter:
  - backend must call AI execution via event-driven flow using tenant context, user context, and AI insight topic;
  - backend must include a backend-issued short-lived service token in the payload;
  - backend must merge the AI response payload into the template output through the existing render pipeline.
- Backend remains responsible for final template rendering and delivery.

### 11.4 AI Service Enrichment Responsibilities

- AI service must resolve the requested insight topic and load the corresponding LLM prompt assets.
- AI service must determine if prompt enrichment is needed for that topic.
- When enrichment is required, AI service calls standard backend user-facing APIs using the provided service token.
- AI service returns structured insight payload content for backend merge.

### 11.5 Backward Compatibility

- Existing `goal_created_email_insight` behavior must continue to function during rollout.
- Existing templates without AI-insight parameters must continue to merge/send exactly as before.
- Generic support must be additive and controlled through registry/configuration.

---

## 12. Service Token Requirements for AI Prompt Enrichment

These requirements define how backend-issued service tokens are used for AI-initiated enrichment calls.

### 12.1 Issuance and Ownership

- Backend API issues the token and includes it in the AI request payload.
- AI service does not mint, alter, or re-sign the token; it only forwards it when calling backend APIs.
- Backend API validates the same token through standard API authentication/authorization components.

### 12.2 Token Constraints

- Token must be short-lived and scoped to enrichment use.
- Token must carry tenant/user context required for authorized enrichment calls.
- Token claims must be compatible with the standard backend token validation pipeline.

### 12.3 Validation and Audit Expectations

- Producer-side validation: backend must validate outbound AI request envelope completeness before publish/send.
- Consumer-side validation: backend API endpoints must validate token and authorization through standard auth controls when AI calls for enrichment.
- Correlation and idempotency identifiers must remain traceable across:
  - event trigger;
  - AI execution request;
  - enrichment API calls;
  - final email send/audit records.

---

## 13. Streamlined Email Dispatch Cutover Readiness Requirements

These requirements define the minimum policy/documentation/validation evidence needed before retiring legacy runtime paths during the streamlined email cutover.

### 13.1 Policy and Decision Transparency

- Template resolution decisions must be auditable for direct-path sends, including source and fallback reason.
- Insight processing decisions must be auditable for async sends using decision metadata fields in existing audit contracts.
- Mandatory user communications must not depend on optional preference gates.

### 13.2 Contract Alignment Requirements

- Admin template analytics contracts must reflect repository-backed metrics and timeline responses.
- Documentation must match implemented behavior for:
  - DB-first template resolution with controlled inline fallback.
  - Insight fallback/degradation metadata enrichment in async audit decision context.
  - 30-day rolling analytics contract used by admin template analytics endpoint.

### 13.3 Validation Evidence Requirements

- A repository-persisted cutover validation artifact must exist and include:
  - command-level validation evidence;
  - impacted code/document references;
  - explicit statement of contract impact (changed/unchanged) per endpoint.
- Validation checklist references must be kept in-repo and linked from issue closure notes.

### 13.4 Cutover Exit Criteria

- Shared requirements, design, and API specification artifacts are aligned to implemented runtime behavior.
- Focused validation commands for notification processor and streamlined email behavior are green.
- Evidence links are posted in issue completion notes to support dev/staging gate decisions.
