# PurposePath AI Coaching Service - Business Requirements

**Document Version:** 1.0.0  
**Last Updated:** October 8, 2025  
**Status:** Draft - Ready for Implementation

---

## 📋 Executive Summary

The PurposePath AI Coaching Service provides intelligent guidance and analysis to help organizations and individuals align their goals, strategies, and operations with their core business foundation. The service offers two distinct interaction modes:

1. **One-Shot Analysis**: Instant AI-powered insights for specific business questions
2. **Conversational Coaching**: Multi-turn guided conversations for deep exploration of strategic topics

---

## 🎯 Business Objectives

### Primary Goals

1. **Strategic Alignment**: Help organizations ensure their goals align with vision, purpose, and core values
2. **Smart Decision Making**: Provide AI-powered recommendations for strategies, KPIs, and actions
3. **Operational Excellence**: Assist in root cause analysis, prioritization, and action planning
4. **Guided Development**: Support users through structured coaching conversations for core business elements

### Success Criteria

- Users receive actionable insights within 2 seconds
- Alignment scores are consistent and explainable
- Recommendations are contextual and relevant to business foundation
- Coaching conversations feel natural and productive
- 95% of AI suggestions are rated as helpful by users

---

## 👥 User Personas

### 1. Business Executive
**Needs:**
- Quick alignment checks for strategic goals
- AI-powered strategy recommendations
- Executive-level insights without technical jargon

**Use Cases:**
- Validate if new goal aligns with company vision
- Get suggestions for strategic initiatives
- Assess business impact of issues

### 2. Team Manager
**Needs:**
- Help prioritizing team actions
- Guidance on KPI selection
- Root cause analysis for operational issues

**Use Cases:**
- Prioritize quarterly action items
- Select relevant KPIs for team goals
- Analyze recurring operational problems

### 3. Individual Contributor
**Needs:**
- Guidance on personal goal setting
- Understanding how work connects to company strategy
- Coaching on professional development

**Use Cases:**
- Align personal OKRs with team objectives
- Explore career development through coaching
- Get action recommendations from identified issues

---

## 🔄 Interaction Modes

### Mode 1: One-Shot Analysis

**What It Is:**
Quick, instant AI-powered analysis that provides immediate insights without maintaining conversation context.

**Business Value:**
- Fast decision support
- No commitment to long conversations
- Repeatable for different scenarios
- Point-in-time analysis

**User Experience:**
1. User submits a specific question or data
2. AI analyzes and provides structured response
3. User receives actionable insights immediately
4. No follow-up required (but user can ask again)

**Examples:**
- "Does this goal align with our vision?"
- "What strategies should we consider?"
- "What KPIs measure this goal's success?"
- "What's causing this recurring issue?"

### Mode 2: Conversational Coaching

**What It Is:**
Multi-turn guided conversation where AI acts as a coach, asking probing questions and helping users think deeply about strategic topics.

**Business Value:**
- Deep exploration of complex topics
- Guided thinking process
- Documented journey and insights
- Personalized guidance based on responses

**User Experience:**
1. User selects coaching topic (Core Values, Purpose, Vision, Goals)
2. AI greets and explains the process
3. Multi-turn conversation with thoughtful questions
4. AI adapts questions based on user responses
5. Session concludes with summary and insights
6. User can pause and resume later

**Examples:**
- "Help me identify my company's core values"
- "Guide me in crafting our purpose statement"
- "Coach me through setting strategic goals"

---

## 📊 Feature Categories

### 1. Alignment & Strategy Guidance

#### 1.1 Alignment Scoring
**Business Purpose:** Measure how well goals align with business foundation

**User Story:**
> As a business leader, I want to validate if my new goal aligns with our vision and values, so I can ensure strategic coherence.

**Input:** Goal details, strategies, KPIs, business foundation
**Output:** Alignment score (0-100), component scores, explanation, improvement suggestions

**Business Rules:**
- Score reflects vision, purpose, values, strategy coherence, and KPI relevance
- Higher scores indicate better alignment
- Suggestions are specific and actionable

#### 1.2 Alignment Explanation
**Business Purpose:** Understand why a goal is or isn't aligned

**User Story:**
> As a team manager, I want to understand why my goal scored low on alignment, so I can improve it.

**Input:** Goal object, business foundation
**Output:** Detailed explanation of alignment factors

#### 1.3 Alignment Improvement Suggestions
**Business Purpose:** Get specific recommendations to improve alignment

**User Story:**
> As a goal owner, I want suggestions on how to better align my goal with company values, so I can refine it.

**Input:** Goal object, business foundation
**Output:** List of specific improvement actions

#### 1.4 Strategy Recommendations
**Business Purpose:** Generate strategic approaches to achieve goals

**User Story:**
> As a strategist, I want AI-generated strategy options for my goal, so I can consider approaches I might not have thought of.

**Input:** Goal intent, existing strategies, business context
**Output:** 3-5 strategy options with rationale and feasibility scores

**Business Rules:**
- Strategies should be specific and actionable
- Feasibility considers business context
- Avoids duplicating existing strategies

#### 1.5 KPI Recommendations
**Business Purpose:** Identify relevant metrics to measure goal progress

**User Story:**
> As a team leader, I want suggestions for KPIs that measure my goal, so I can track progress effectively.

**Input:** Goal intent, strategies, business context, existing KPIs
**Output:** Recommended KPIs with relevance scores, time horizons, and explanations

**Business Rules:**
- KPIs should be measurable and specific
- Time horizons align with goal timeframe
- Avoids duplicating existing KPIs

---

### 2. Conversational Coaching

#### 2.1 Core Values Discovery
**Business Purpose:** Help users identify fundamental organizational values

**User Story:**
> As a founder, I want guided coaching to identify our 5-7 core values, so we can build culture intentionally.

**Process:**
1. Welcome and explain values importance
2. Explore motivation sources ("What energizes you?")
3. Investigate aversions ("What frustrates you?")
4. Examine relationship patterns
5. Analyze decision-making principles
6. Synthesize 5-7 core values
7. Validate and refine

**Duration:** 15-30 minutes
**Output:** 5-7 defined core values with descriptions

#### 2.2 Purpose Identification
**Business Purpose:** Guide users in articulating organizational purpose

**User Story:**
> As a business owner, I want coaching to discover our company's purpose, so we can communicate it clearly.

**Process:**
1. Explore passions and interests
2. Investigate desired impact
3. Identify natural strengths
4. Discuss legacy aspirations
5. Synthesize purpose statement
6. Refine and validate

**Duration:** 20-40 minutes
**Output:** Clear purpose statement

#### 2.3 Vision Creation
**Business Purpose:** Support crafting compelling future vision

**User Story:**
> As a CEO, I want help creating a 5-year vision, so our team has a clear direction.

**Process:**
1. Explore long-term aspirations
2. Define success indicators
3. Identify ideal outcomes
4. Create vivid future picture
5. Test clarity and inspiration
6. Refine vision statement

**Duration:** 25-45 minutes
**Output:** Compelling vision statement

#### 2.4 Goal Setting
**Business Purpose:** Guide effective goal formulation

**User Story:**
> As a manager, I want coaching on setting SMART goals, so they're achievable and measurable.

**Process:**
1. Clarify goal intent
2. Apply SMART criteria
3. Identify priorities
4. Assess resources
5. Anticipate obstacles
6. Finalize goal structure

**Duration:** 20-35 minutes
**Output:** Well-structured SMART goal

---

### 3. Operations AI Features

#### 3.1 Root Cause Analysis
**Business Purpose:** Help identify underlying causes of issues

**User Story:**
> As an operations manager, I want AI to suggest root cause analysis methods, so I can systematically investigate problems.

**Input:** Issue title, description, impact level, context
**Output:** Suggested analysis methods (SWOT, Five Whys, Fishbone) with confidence scores

#### 3.2 SWOT Analysis Generation
**Business Purpose:** Create structured SWOT analysis for issues

**User Story:**
> As a team lead, I want AI-generated SWOT analysis of an issue, so I can see all angles quickly.

**Input:** Issue details, impact level, context
**Output:** Strengths, Weaknesses, Opportunities, Threats

#### 3.3 Five Whys Questions
**Business Purpose:** Generate iterative "why" questions for root cause discovery

**User Story:**
> As an analyst, I want AI to generate follow-up "why" questions, so I can dig deeper into causes.

**Input:** Issue details, previous answers
**Output:** Next set of probing questions

#### 3.4 Action Plan Generation
**Business Purpose:** Convert issues into actionable plans

**User Story:**
> As a project manager, I want AI to suggest action items from an issue, so I can quickly create remediation plans.

**Input:** Issue details, impact, priority, context
**Output:** 3-5 action items with priorities, durations, assignments, dependencies

#### 3.5 Action Plan Optimization
**Business Purpose:** Optimize action sequencing and resource allocation

**User Story:**
> As a team lead, I want AI to optimize my action plan order, so we work efficiently.

**Input:** List of actions with dependencies, constraints (time, resources)
**Output:** Optimized sequence with rationale, completion estimate, risk factors

#### 3.6 Prioritization Suggestions
**Business Purpose:** Recommend action priority levels

**User Story:**
> As a manager with 50 actions, I want AI to suggest which are most urgent, so I can focus team effort.

**Input:** List of actions with current priorities, due dates, progress, connections
**Output:** Priority suggestions with reasoning, urgency factors, impact factors

#### 3.7 Scheduling Recommendations
**Business Purpose:** Optimize action timelines

**User Story:**
> As a scheduler, I want AI to suggest realistic start/due dates considering dependencies, so our timeline is achievable.

**Input:** Actions with dates, dependencies, constraints (working hours, holidays, capacity)
**Output:** Optimized schedule with resource considerations

#### 3.8 Issue Categorization
**Business Purpose:** Automatically tag and classify issues

**User Story:**
> As an issue tracker, I want AI to categorize new issues, so they're routed correctly.

**Input:** Issue title, description, current impact/priority
**Output:** Suggested impact level, priority, category, tags with reasoning

#### 3.9 Impact Assessment
**Business Purpose:** Evaluate business impact of issues

**User Story:**
> As a business analyst, I want AI to assess issue impact, so we prioritize correctly.

**Input:** Issue details, business context
**Output:** Impact assessment, reasoning, affected areas, mitigation suggestions

---

### 4. Strategic Integration

#### 4.1 Action Strategic Context
**Business Purpose:** Show how actions connect to strategic goals

**User Story:**
> As an action owner, I want to see how my action connects to company goals, so I understand its importance.

**Input:** Action ID
**Output:** Connected goals/strategies, alignment scores, KPI impacts, recommendations

#### 4.2 Connection Suggestions
**Business Purpose:** Suggest strategic connections for actions

**User Story:**
> As a planner, I want AI to suggest which goals this action supports, so I can link them properly.

**Input:** Action details, available goals
**Output:** Suggested goal/strategy connections with alignment scores

---

## 🔐 Security & Privacy

### Data Handling

**Business Context Data:**
- Organizations control what data enriches prompts
- No business data stored in AI service (passed through Step Functions)
- All data encrypted in transit and at rest

**Conversation Data:**
- Coaching sessions stored securely per tenant
- Users can pause/resume/delete conversations
- Data retention follows tenant settings

**AI Interactions:**
- No training on customer data
- Prompts and responses logged for debugging (tenant-isolated)
- Usage metrics tracked for billing and analytics

---

## 📈 Business Metrics

### Key Performance Indicators

1. **User Engagement:**
   - Coaching sessions initiated per user per month
   - One-shot analysis requests per user per week
   - Average coaching session completion rate

2. **AI Quality:**
   - User satisfaction rating (1-5 stars)
   - Suggestion acceptance rate
   - Alignment score consistency

3. **Business Impact:**
   - Goals created after coaching sessions
   - Actions generated from AI suggestions
   - Time saved in strategic planning

4. **Operational:**
   - Average response time
   - AI provider uptime
   - Cost per interaction

---

## 🔄 User Workflows

### Workflow 1: Create Aligned Goal

```
1. User: Creates new goal in system
2. System: Detects new goal
3. User: Clicks "Check Alignment"
4. System: Calls Alignment Check endpoint
5. AI: Analyzes goal vs business foundation
6. System: Shows alignment score + suggestions
7. User: Reviews suggestions
8. User: Edits goal based on suggestions
9. System: Re-checks alignment
10. User: Saves improved goal
```

### Workflow 2: Explore Core Values (Coaching)

```
1. User: Navigates to "Discover Core Values"
2. User: Clicks "Start Coaching Session"
3. System: Calls Initiate Conversation endpoint
4. AI: Sends welcome message and first question
5. User: Responds to question
6. System: Calls Send Message endpoint
7. AI: Asks follow-up question
8. [Repeat steps 5-7 for 15-30 minutes]
9. AI: Synthesizes 5-7 values
10. User: Reviews and confirms values
11. System: Saves values to business foundation
```

### Workflow 3: Analyze Recurring Issue

```
1. User: Reports recurring issue
2. User: Clicks "Analyze Root Cause"
3. System: Calls Root Cause Suggestions endpoint
4. AI: Suggests SWOT, Five Whys, Fishbone options
5. User: Selects SWOT Analysis
6. System: Calls SWOT Analysis endpoint
7. AI: Generates SWOT breakdown
8. User: Reviews analysis
9. User: Clicks "Generate Action Plan"
10. System: Calls Action Suggestions endpoint
11. AI: Suggests 3-5 actions
12. User: Selects actions to create
13. System: Creates actions in system
```

---

## 🌍 Multilingual Support (Future)

**Current:** English only
**Future:** Support for:
- Spanish
- French
- German
- Portuguese

**Implementation:** Language code parameter in all endpoints

---

## ♿ Accessibility Requirements

- All AI responses must be screen-reader friendly
- Coaching conversations support pause/resume for users who need breaks
- Text alternatives for any visual insights
- Keyboard navigation for all coaching interfaces

---

## 📱 Platform Support

**Current:**
- Web application (React)
- API-first design

**Future:**
- Mobile apps (iOS/Android)
- Slack integration
- Microsoft Teams integration

---

## 🔄 Integration Points

### With .NET Business API

**Purpose:** Enrich AI prompts with business context

**Integration Pattern:**
1. Frontend calls Coaching Service endpoint
2. Coaching Service calls Step Functions orchestrator
3. Step Functions calls .NET API for business data
4. .NET API returns structured business context
5. Step Functions passes enriched data to Coaching Service
6. Coaching Service includes context in AI prompt
7. AI generates context-aware response

**Business Data Examples:**
- Current goals and their status
- Recent KPI performance
- Team capacity and workload
- Historical decision patterns
- Organizational structure

---

## 📋 Requirements Traceability

| Requirement ID | Category | Priority | Status |
|---|---|---|---|
| REQ-001 | Alignment scoring | High | Planned |
| REQ-002 | Strategy recommendations | High | Planned |
| REQ-003 | KPI recommendations | High | Planned |
| REQ-004 | Coaching - Core Values | Medium | Planned |
| REQ-005 | Coaching - Purpose | Medium | Planned |
| REQ-006 | Coaching - Vision | Medium | Planned |
| REQ-007 | Coaching - Goals | Medium | Planned |
| REQ-008 | Root cause analysis | High | Planned |
| REQ-009 | SWOT analysis | Medium | Planned |
| REQ-010 | Action plan generation | High | Planned |
| REQ-011 | Prioritization | Medium | Planned |
| REQ-012 | Scheduling optimization | Low | Planned |
| REQ-013 | Issue categorization | Medium | Planned |
| REQ-014 | Impact assessment | High | Planned |
| REQ-015 | Strategic context | Medium | Planned |

---

## 🎓 Glossary

**Alignment:** The degree to which a goal, strategy, or action supports the organization's vision, purpose, and core values.

**Business Foundation:** The core elements that define an organization - vision, purpose, core values, target market, and value proposition.

**Coaching Session:** A multi-turn conversation where AI guides users through structured exploration of a topic.

**One-Shot Analysis:** A single-request AI interaction that provides immediate insights without conversation context.

**Strategic Context:** Information showing how tactical elements (actions, KPIs) connect to strategic elements (goals, strategies).

**KPI (Key Performance Indicator):** A measurable value that demonstrates how effectively an organization is achieving objectives.

**SMART Goal:** Specific, Measurable, Achievable, Relevant, Time-bound objective.

**SWOT Analysis:** Assessment framework examining Strengths, Weaknesses, Opportunities, and Threats.

**Five Whys:** Root cause analysis technique asking "why" iteratively to discover underlying issues.

**Prompt Template:** A structured template defining how to present information to the AI, including system instructions, input format, and output requirements.

**Enriched Context:** Additional business data from the database that makes AI responses more relevant and personalized.

---

## ✅ Acceptance Criteria

### For All Features

1. **Performance:** Response time < 2 seconds (P95)
2. **Reliability:** 99.5% uptime
3. **Accuracy:** AI suggestions rated helpful by 90%+ of users
4. **Security:** All tenant data isolated
5. **Usability:** Users can complete tasks without documentation

### Feature-Specific

**Alignment Scoring:**
- Score is between 0-100
- Component scores explain overall score
- Suggestions are specific and actionable

**Coaching Sessions:**
- Users can pause and resume
- Conversations feel natural and human-like
- Sessions complete within estimated time
- Insights are documented and retrievable

**Operations AI:**
- Analysis methods are appropriate for issue type
- Generated actions are realistic and achievable
- Prioritization considers multiple factors

---

**Document Status:** Ready for Technical Design
**Next Steps:** Technical architecture and implementation planning
