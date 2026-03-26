# Email Insights - Business Requirements (v1 Pilot)

**Version:** 1.0  
**Date:** March 25, 2026  
**Status:** Approved for Pilot

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
