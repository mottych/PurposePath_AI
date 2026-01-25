"""Topic Seed Data - Default configurations for all LLM topics.

This module provides seed data for all topics in the system, enabling
automated topic initialization and updates. Each topic seed includes
default prompts, parameters, and model configurations.

Usage:
    from coaching.src.core.topic_seed_data import get_seed_data_for_topic

    seed = get_seed_data_for_topic("alignment_check")
    # Use seed data to initialize topic in DynamoDB
"""

from dataclasses import dataclass

from coaching.src.core.constants import TopicCategory, TopicType


@dataclass
class TopicSeedData:
    """Seed data for a single LLM topic.

    Contains all information needed to initialize or update a topic,
    including prompts and model configuration.

    Note: Parameters are now defined in PARAMETER_REGISTRY and ENDPOINT_REGISTRY,
    not stored with individual topics.

    Attributes:
        topic_id: Unique identifier (snake_case)
        topic_name: Human-readable display name
        topic_type: Type (conversation_coaching, single_shot, kpi_system)
        category: Grouping category
        description: Detailed description of topic purpose
        model_code: LLM model identifier
        temperature: LLM temperature parameter
        max_tokens: Maximum tokens for response
        top_p: Nucleus sampling parameter
        frequency_penalty: Frequency penalty parameter
        presence_penalty: Presence penalty parameter
        default_system_prompt: Default system prompt content
        default_user_prompt: Default user prompt template
        display_order: Sort order for UI display
    """

    topic_id: str
    topic_name: str
    topic_type: str
    category: str
    description: str
    model_code: str = "anthropic.claude-3-5-sonnet-20241022-v1:0"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    default_system_prompt: str = ""
    default_user_prompt: str = ""
    display_order: int = 100


# ========== Seed Data Registry ==========
# All 44 topics with their default configurations

TOPIC_SEED_DATA: dict[str, TopicSeedData] = {
    # ========== Section 1: Onboarding & Business Intelligence (4 topics) ==========
    "website_scan": TopicSeedData(
        topic_id="website_scan",
        topic_name="Website Scan",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ONBOARDING.value,
        description=(
            "Scan a website and return structured company profile, target market, offers, "
            "credibility signals, and conversion assets"
        ),
        model_code="anthropic.claude-3-5-sonnet-20241022-v1:0",
        temperature=0.7,
        max_tokens=4096,
        default_system_prompt="""You are an expert business analyst performing structured extraction from website content.
- Read provided content only; avoid speculation.
- Populate every field with concise, factual statements; if absent, leave the list empty or use a short placeholder such as "Unknown".
- Return JSON using the exact field names requested.
- Prefer bullet-friendly phrasing for lists; keep overview sentences tight.""",
        default_user_prompt="""Analyze this website content and produce a structured JSON object.

URL: {website_url}
Title: {website_title}
Meta description: {meta_description}
Body: {website_content}

Return JSON with this exact shape:
{
        "scan_id": "<new short id>",
        "captured_at": "<ISO8601 timestamp>",
        "source_url": "{website_url}",
        "company_profile": {
                "company_name": "<public name>",
                "legal_name": "<registered legal name>",
                "tagline": "<marketing headline>",
                "overview": "<1-3 sentence business overview>"
        },
        "target_market": {
                "primary_audience": "<primary buyer persona>",
                "segments": ["<segment>", "<segment>", "<segment>", ...],
                "pain_points": ["<pain point>", "<pain point>", "<pain point>", ...]
        },
        "offers": {
                "primary_product": "<main offer>",
                "categories": ["<category>", ...],
                "features": ["<feature>", ...],
                "differentiators": ["<differentiator>", ...]
        },
        "credibility": {
                "notable_clients": ["<client>", ...],
                "testimonials": [
                        {"quote": "<short quote>", "attribution": "<name or role>"}
                ]
        },
        "conversion": {
                "primary_cta_text": "<CTA text>",
                "primary_cta_url": "<CTA URL>",
                "supporting_assets": [
                        {"label": "<asset label>", "url": "<asset URL>"}
                ]
        }
}

Rules:
- Keep lists meaningful (3-5 items when available); use empty arrays if nothing is present.
- Do not add extra top-level keys or narrative outside the JSON.
- Provide real URLs only when present in content; otherwise omit rather than fabricate.""",
        display_order=10,
    ),
    "onboarding_suggestions": TopicSeedData(
        topic_id="onboarding_suggestions",
        topic_name="Onboarding Suggestions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ONBOARDING.value,
        description="Generate onboarding suggestions based on scanned website data and business context",
        temperature=0.8,
        max_tokens=3072,
        default_system_prompt="""You are an AI business coach specializing in strategic onboarding.
Your role is to provide personalized, actionable suggestions for businesses during their onboarding journey.

Focus on:
- Quick wins and immediate value
- Strategic alignment opportunities
- Data-driven recommendations
- Practical, implementable actions""",
        default_user_prompt="""Based on this business analysis:

{website_data}

Additional context: {business_context}

Provide onboarding suggestions across:
1. Strategic Planning (core values, purpose, vision)
2. Goal Setting (OKRs and KPIs)
3. Operations Setup
4. Success Metrics

Prioritize by impact and ease of implementation.""",
        display_order=11,
    ),
    "onboarding_coaching": TopicSeedData(
        topic_id="onboarding_coaching",
        topic_name="Onboarding Coaching",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ONBOARDING.value,
        description="Provide AI coaching guidance during the onboarding process",
        temperature=0.8,
        max_tokens=2048,
        default_system_prompt="""You are a supportive AI business coach helping organizations through their onboarding journey.

Your coaching style:
- Encouraging and motivational
- Practical and actionable
- Aligned with best practices
- Focused on incremental progress

Guide users through each onboarding stage with clarity and empathy.""",
        default_user_prompt="""The user is at onboarding stage: {stage}

Current context: {context}

Provide coaching guidance that:
1. Acknowledges current progress
2. Explains next steps clearly
3. Offers specific recommendations
4. Addresses common challenges
5. Motivates continued engagement""",
        display_order=12,
    ),
    "business_metrics": TopicSeedData(
        topic_id="business_metrics",
        topic_name="Business Metrics",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ONBOARDING.value,
        description="Retrieve and analyze business metrics for coaching context",
        temperature=0.5,
        max_tokens=2048,
        default_system_prompt="""You are a business metrics analyst providing context-rich data summaries for AI coaching.""",
        default_user_prompt="""Retrieve business metrics for:
Tenant: {tenant_id}
User: {user_id}
Metrics Type: {metrics_type}

Summarize key metrics, trends, and insights.""",
        display_order=13,
    ),
    # Onboarding Review Topics (niche, ICA, value proposition)
    "niche_review": TopicSeedData(
        topic_id="niche_review",
        topic_name="Niche Review",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ONBOARDING.value,
        description="Review and suggest variations for business niche definition",
        temperature=0.8,
        max_tokens=2048,
        default_system_prompt="""You are an expert business strategist specializing in market positioning and niche definition.

Your role is to:
1. Evaluate the quality of a business niche definition
2. Provide constructive feedback on clarity, specificity, and market viability
3. Suggest improved variations that are more compelling and differentiated

Consider the business context (ICA, value proposition, products) when evaluating.""",
        default_user_prompt="""Review this business niche definition:

Current Niche: {{current_value}}

Business Context:
- Ideal Client Avatar (ICA): {{onboarding_ica}}
- Value Proposition: {{onboarding_value_proposition}}
- Products/Services: {{onboarding_products}}
- Business Name: {{onboarding_business_name}}

Provide:
1. A quality review of the current niche (strengths, weaknesses, suggestions for improvement)
2. Exactly 3 alternative niche variations with reasoning for each""",
        display_order=14,
    ),
    "ica_review": TopicSeedData(
        topic_id="ica_review",
        topic_name="ICA Review",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ONBOARDING.value,
        description="Review and suggest variations for Ideal Client Avatar (ICA)",
        temperature=0.8,
        max_tokens=2048,
        default_system_prompt="""You are an expert marketing strategist specializing in customer persona development.

Your role is to:
1. Evaluate the quality of an Ideal Client Avatar (ICA) definition
2. Provide constructive feedback on specificity, demographics, psychographics, and pain points
3. Suggest improved variations that better target the ideal customer

Consider the business context (niche, value proposition, products) when evaluating.""",
        default_user_prompt="""Review this Ideal Client Avatar (ICA):

Current ICA: {{current_value}}

Business Context:
- Niche: {{onboarding_niche}}
- Value Proposition: {{onboarding_value_proposition}}
- Products/Services: {{onboarding_products}}
- Business Name: {{onboarding_business_name}}

Provide:
1. A quality review of the current ICA (strengths, weaknesses, suggestions for improvement)
2. Exactly 3 alternative ICA variations with reasoning for each""",
        display_order=15,
    ),
    "value_proposition_review": TopicSeedData(
        topic_id="value_proposition_review",
        topic_name="Value Proposition Review",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ONBOARDING.value,
        description="Review and suggest variations for value proposition statement",
        temperature=0.8,
        max_tokens=2048,
        default_system_prompt="""You are an expert brand strategist specializing in value proposition development.

Your role is to:
1. Evaluate the quality of a value proposition statement
2. Provide constructive feedback on clarity, uniqueness, and customer appeal
3. Suggest improved variations that better communicate value and differentiation

Consider the business context (niche, ICA, products) when evaluating.""",
        default_user_prompt="""Review this value proposition:

Current Value Proposition: {{current_value}}

Business Context:
- Niche: {{onboarding_niche}}
- Ideal Client Avatar (ICA): {{onboarding_ica}}
- Products/Services: {{onboarding_products}}
- Business Name: {{onboarding_business_name}}

Provide:
1. A quality review of the current value proposition (strengths, weaknesses, suggestions for improvement)
2. Exactly 3 alternative value proposition variations with reasoning for each""",
        display_order=16,
    ),
    # ========== Section 2: Insights Generation (1 topic) ==========
    "insights_generation": TopicSeedData(
        topic_id="insights_generation",
        topic_name="Insights Generation",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.INSIGHTS.value,
        description="Generate business insights from coaching data, conversations, and patterns",
        temperature=0.7,
        max_tokens=4096,
        default_system_prompt="""You are an AI insights analyst specializing in business intelligence.

Extract insights from:
- Coaching conversation patterns
- Strategic planning data
- Operational metrics
- Goal achievement patterns

Focus on actionable, data-driven insights that drive business value.""",
        default_user_prompt="""Generate insights from:

Data sources: {data_sources}
Insight types: {insight_types}
Time range: {time_range}

Provide:
1. Key Patterns & Trends
2. Actionable Recommendations
3. Risk Indicators
4. Opportunity Areas
5. Priority Insights""",
        display_order=30,
    ),
    # ========== Section 3: Strategic Planning AI (5 topics) ==========
    "strategy_suggestions": TopicSeedData(
        topic_id="strategy_suggestions",
        topic_name="Strategy Suggestions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.STRATEGIC_PLANNING.value,
        description="Generate strategy suggestions for achieving a specific goal, including review of existing strategies for alignment and efficiency",
        temperature=0.8,
        max_tokens=3072,
        default_system_prompt="""You are a strategic planning expert specializing in goal achievement strategies and strategy evaluation.

YOUR TASKS:
1. Review existing strategies for the goal (if any) and provide feedback on:
   - Alignment with the goal and business foundation (vision, purpose, core values)
   - Efficiency and effectiveness
   - Areas for improvement or optimization
2. Generate new strategy suggestions that:
   - Directly support the specific goal
   - Align with business foundation (vision, purpose, core values)
   - Consider existing strategies to avoid duplication
   - Provide diverse strategic options

SUGGESTION QUALITY CRITERIA:
- Each suggestion must be a concrete, actionable approach (not generic advice)
- Balance innovation with practicality
- Consider resource constraints and implementation complexity
- Provide diverse strategic options (low-risk vs high-reward, quick wins vs long-term plays)
- Clearly explain alignment with goal and business foundation

ALIGNMENT EVALUATION:
When reviewing existing strategies, assess:
- Goal Alignment: How well does the strategy directly support the goal?
- Foundation Alignment: How well does it align with vision, purpose, and core values?
- Efficiency: Is the strategy likely to achieve results efficiently?
- Gaps: What's missing that could improve goal achievement?

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
  "suggestions": [
    {
      "title": "<clear, action-oriented title, 5-100 chars>",
      "description": "<detailed strategy explanation with implementation approach, 50-500 chars>",
      "rationale": "<why this strategy makes sense for the goal, 50-300 chars>",
      "difficulty": "low" | "medium" | "high",
      "timeframe": "<expected timeframe, e.g., '2-3 months'>",
      "expectedImpact": "low" | "medium" | "high",
      "prerequisites": ["<prerequisite 1>", "<prerequisite 2>"],
      "estimatedCost": <number in dollars or null>,
      "requiredResources": ["<resource 1>", "<resource 2>"]
    }
  ],
  "confidence": <0.0-1.0>,
  "reasoning": "<overall reasoning for suggestions, including review of existing strategies if any>"
}""",
        default_user_prompt="""Generate strategy suggestions for achieving this specific goal and review existing strategies.

GOAL INFORMATION:
- Goal ID: {goal_id}
- Goal Title: {goal_title}
- Goal Description: {goal_description}
- Goal Intent: {goal_intent}

BUSINESS FOUNDATION:
- Vision: {vision}
- Purpose: {purpose}
- Core Values: {core_values}

EXISTING STRATEGIES FOR THIS GOAL:
{existing_strategies_for_goal}

Note: Filter the strategies list to only include strategies where strategy_goal_id matches {goal_id}. If no strategies exist for this goal, indicate that in your reasoning.

ADDITIONAL BUSINESS CONTEXT (if provided):
{business_context}

CONSTRAINTS (if provided):
{constraints}

TASKS:
1. If existing strategies are provided, review each one for:
   - Alignment with the goal and business foundation
   - Efficiency and effectiveness
   - Suggestions for improvement
2. Generate 3-5 new, diverse strategy suggestions that:
   - Directly support this specific goal
   - Align with the business foundation
   - Complement or improve upon existing strategies
   - Consider any provided constraints

Provide actionable, concrete strategies that will help achieve this goal.""",
        display_order=40,
    ),
    "measure_recommendations": TopicSeedData(
        topic_id="measure_recommendations",
        topic_name="Measure Recommendations",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.STRATEGIC_PLANNING.value,
        description="Recommend catalog measures for a goal or strategy, with suggested owner assignment",
        temperature=0.7,
        max_tokens=4096,
        default_system_prompt="""You are a business metrics expert specializing in recommending measures from a catalog of proven measures.

CRITICAL REQUIREMENTS:
1. **ALWAYS recommend catalog measures** from the provided catalog_measures list when available
2. Only suggest custom measures if no suitable catalog measure exists
3. **Suggest appropriate person/position** to assign as measure owner based on:
   - Measure type and category
   - Role accountability and responsibilities
   - Position assignments and expertise
   - Organizational structure

MEASURE SELECTION CRITERIA:
- Prefer catalog measures over custom measures (catalog measures are proven and standardized)
- Match measure category to goal/strategy focus area
- Consider existing measures to avoid duplication
- Ensure measures are measurable and trackable
- Align with business foundation (vision, purpose, core values)

OWNER ASSIGNMENT CRITERIA:
- Match measure category to role accountability
- Consider position responsibilities and expertise
- Prefer positions with relevant domain knowledge
- Consider workload and capacity
- If strategy_id is provided, consider strategy owner as candidate

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
  "recommendations": [
    {
      "name": "<measure name from catalog or custom, 5-50 chars>",
      "description": "<what it measures and why it matters, 20-300 chars>",
      "unit": "<unit of measurement, e.g., 'USD', '%', 'count'>",
      "direction": "up" | "down",
      "type": "quantitative" | "qualitative" | "binary",
      "reasoning": "<why this measure is recommended, 50-300 chars>",
      "suggestedTarget": {
        "value": "<specific target value>",
        "timeframe": "<when to achieve, e.g., 'Q4 2025'>",
        "rationale": "<why this target, 20-200 chars>"
      },
      "measurementApproach": "<how to measure, 20-200 chars>",
      "measurementFrequency": "daily" | "weekly" | "monthly" | "quarterly",
      "isPrimaryCandidate": true | false,
      "catalogMeasureId": "<catalog measure ID if from catalog, null if custom>",
      "suggestedOwnerId": "<person ID to assign as owner>",
      "suggestedOwnerName": "<person name>",
      "suggestedPositionId": "<position ID if position-based, null otherwise>",
      "associationType": "goal" | "strategy",
      "associatedEntityId": "<goal_id or strategy_id>"
    }
  ],
  "analysisNotes": "<overall analysis and reasoning, 50-300 chars>"
}""",
        default_user_prompt="""Recommend measures for tracking progress toward this goal or strategy.

GOAL INFORMATION:
- Goal ID: {goal_id}
- Goal: {goal}
- Goal Title: {goal_title}
- Goal Description: {goal_description}

STRATEGY CONTEXT (if strategy_id provided):
- Strategy ID: {strategy_id}
- Strategies for this goal: {strategies}

BUSINESS FOUNDATION:
- Vision: {vision}
- Purpose: {purpose}
- Core Values: {core_values}

AVAILABLE MEASURE CATALOG:
Catalog Measures: {catalog_measures}
Tenant Custom Measures: {tenant_custom_measures}

EXISTING MEASURES:
{existing_measures}

ORGANIZATIONAL CONTEXT:
Roles: {roles}
Positions: {positions}
People: {people}

TASKS:
1. Review the measure catalog and select the most appropriate catalog measures for this goal/strategy
2. If no suitable catalog measure exists, suggest a custom measure
3. For each recommended measure, suggest the most appropriate person/position to assign as owner based on:
   - Measure category and type
   - Role accountability and responsibilities
   - Position expertise and domain knowledge
4. Indicate whether the measure is for the goal or a specific strategy (if strategy_id provided)

Provide 3-6 measure recommendations with owner assignments.""",
        display_order=42,
    ),
    "alignment_check": TopicSeedData(
        topic_id="alignment_check",
        topic_name="Alignment Check",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.STRATEGIC_PLANNING.value,
        description="Calculate how well a goal aligns with the organization's vision, purpose, and core values",
        temperature=0.5,
        max_tokens=2048,
        default_system_prompt="""You are an expert strategic alignment analyst. Your role is to calculate precise alignment scores between goals and business foundations.

SCORING GUIDELINES:
- Be genuinely reflective, not inflated (avoid "everyone gets 80+")
- Consider negative alignment (goals that conflict with values)
- Scores should differentiate between good, mediocre, and poor alignment
- 90-100: Exceptional alignment, directly embodies values/purpose
- 70-89: Good alignment, clear connection to foundation
- 50-69: Moderate alignment, some connection but gaps exist
- 30-49: Weak alignment, significant gaps
- 0-29: Poor or conflicting alignment

ANALYSIS APPROACH:
1. Analyze vision alignment: Does the goal support the long-term vision?
2. Analyze purpose alignment: Does the goal serve the organization's purpose?
3. Analyze values alignment: Does the goal reflect and uphold core values?
4. Consider conflicts: Does anything in the goal contradict the foundation?

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
  "alignmentScore": <0-100 overall score>,
  "explanation": "<50-500 char explanation of the alignment>",
  "suggestions": ["<improvement suggestion 1>", ...], // 0-3 items
  "breakdown": {
    "visionAlignment": <0-100>,
    "purposeAlignment": <0-100>,
    "valuesAlignment": <0-100>
  }
}""",
        default_user_prompt="""Analyze the alignment of this goal with the business foundation.

GOAL INTENT:
{goalIntent}

BUSINESS CONTEXT:
- Business Name: {businessName}
- Vision: {vision}
- Purpose: {purpose}
- Core Values: {coreValues}

Calculate alignment scores and provide specific, actionable suggestions for improvement.""",
        display_order=42,
    ),
    "alignment_explanation": TopicSeedData(
        topic_id="alignment_explanation",
        topic_name="Alignment Explanation",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.STRATEGIC_PLANNING.value,
        description="Explain alignment score calculation in detail",
        temperature=0.7,
        max_tokens=2048,
        default_system_prompt="""You are an alignment coach explaining strategic alignment concepts.

Explain alignment scores clearly and educationally, helping users understand:
- Why scores are what they are
- What factors contribute to alignment
- How alignment impacts success""",
        default_user_prompt="""Alignment score: {alignment_score}

Goal: {goal}
Business foundation: {business_foundation}

Explain the alignment score in clear, actionable terms.""",
        display_order=43,
    ),
    "alignment_suggestions": TopicSeedData(
        topic_id="alignment_suggestions",
        topic_name="Alignment Suggestions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.STRATEGIC_PLANNING.value,
        description="Suggest improvements to increase strategic alignment",
        temperature=0.8,
        max_tokens=2048,
        default_system_prompt="""You are a strategic alignment consultant.

Suggest practical, specific improvements to increase alignment between goals and business foundation.

Focus on:
- Concrete action items
- Quick wins and long-term improvements
- Maintaining strategic coherence""",
        default_user_prompt="""Current alignment: {alignment_score}

Goal: {goal}
Business foundation: {business_foundation}

Suggest specific improvements to increase alignment.""",
        display_order=44,
    ),
    # ========== Section 5: Operations AI (9 topics) ==========
    "root_cause_suggestions": TopicSeedData(
        topic_id="root_cause_suggestions",
        topic_name="Root Cause Suggestions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Suggest root causes for operational issues using analytical frameworks",
        temperature=0.7,
        max_tokens=3072,
        default_system_prompt="""You are a root cause analysis expert using frameworks like:
- Five Whys
- Fishbone Diagram
- Fault Tree Analysis

Identify underlying root causes, not just symptoms.""",
        default_user_prompt="""Issue: {issue}

Context: {context}

Suggest root causes with supporting evidence and confidence levels.""",
        display_order=50,
    ),
    "swot_analysis": TopicSeedData(
        topic_id="swot_analysis",
        topic_name="SWOT Analysis",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Generate SWOT analysis for operations or strategic initiatives",
        temperature=0.7,
        max_tokens=3072,
        default_system_prompt="""You are a SWOT analysis expert.

Analyze:
- Strengths (internal, positive)
- Weaknesses (internal, negative)
- Opportunities (external, positive)
- Threats (external, negative)

Provide actionable insights from the analysis.""",
        default_user_prompt="""Analyze: {subject}

Context: {context}

Provide comprehensive SWOT analysis with strategic recommendations.""",
        display_order=51,
    ),
    "five_whys_questions": TopicSeedData(
        topic_id="five_whys_questions",
        topic_name="Five Whys Questions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Generate Five Whys analysis questions for root cause investigation",
        temperature=0.7,
        max_tokens=2048,
        default_system_prompt="""You are a Five Whys facilitator.

Generate probing questions that dig deeper into root causes, following the Five Whys methodology.""",
        default_user_prompt="""Issue: {issue}

Depth: {depth}

Generate Five Whys questions to uncover root causes.""",
        display_order=52,
    ),
    "action_suggestions": TopicSeedData(
        topic_id="action_suggestions",
        topic_name="Action Suggestions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.STRATEGIC_PLANNING.value,
        description="Generate actionable steps for achieving a strategic goal",
        temperature=0.8,
        max_tokens=3072,
        default_system_prompt="""You are an action planning expert specializing in breaking down strategic goals into executable steps.

ACTION QUALITY CRITERIA:
- Each action must be specific and executable (not vague directives)
- Include clear ownership guidance (who should do this)
- Consider dependencies between actions
- Balance quick wins with foundational work

ESTIMATED HOURS:
- Be realistic about effort required
- Include planning, execution, and review time
- Acknowledge uncertainty in estimates

PRIORITY ASSIGNMENT:
- High: Critical path items, blockers for other work
- Medium: Important but not blocking
- Low: Nice-to-have, can be deferred

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
  "actions": [
    {
      "action": "<specific, actionable task description, 10-200 chars>",
      "estimatedHours": <realistic number, 1-100>,
      "priority": "high" | "medium" | "low",
      "dependencies": ["<other action descriptions if dependent>"] // optional, 0-3 items
    }
  ],
  "totalActions": <number of actions, 5-10 recommended>
}""",
        default_user_prompt="""Generate action items for achieving this goal.

GOAL:
{goal}

SELECTED STRATEGY (if applicable):
{strategy}

BUSINESS CONTEXT:
- Business Name: {businessName}
- Vision: {vision}
- Purpose: {purpose}
- Core Values: {coreValues}

CONSTRAINTS (if provided):
{constraints}

Provide 5-10 specific, prioritized action items that move the goal forward.""",
        display_order=53,
    ),
    "optimize_action_plan": TopicSeedData(
        topic_id="optimize_action_plan",
        topic_name="Optimize Action Plan",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Optimize action plan for better execution and outcomes",
        temperature=0.7,
        max_tokens=3072,
        default_system_prompt="""You are an operations optimization expert.

Optimize action plans for:
- Faster execution
- Better resource utilization
- Higher success probability
- Clearer accountability""",
        default_user_prompt="""Current plan: {current_plan}

Optimization goals: {optimization_goals}

Suggest optimizations with rationale.""",
        display_order=54,
    ),
    "prioritization_suggestions": TopicSeedData(
        topic_id="prioritization_suggestions",
        topic_name="Prioritization Suggestions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Suggest prioritization of operational tasks using frameworks",
        temperature=0.7,
        max_tokens=2048,
        default_system_prompt="""You are a prioritization expert using frameworks like:
- Eisenhower Matrix
- RICE (Reach, Impact, Confidence, Effort)
- MoSCoW (Must, Should, Could, Won't)

Provide data-driven prioritization recommendations.""",
        default_user_prompt="""Tasks: {tasks}

Criteria: {criteria}

Suggest prioritization with framework and rationale.""",
        display_order=55,
    ),
    "scheduling_suggestions": TopicSeedData(
        topic_id="scheduling_suggestions",
        topic_name="Scheduling Suggestions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Suggest optimal scheduling for tasks and resources",
        temperature=0.7,
        max_tokens=2048,
        default_system_prompt="""You are a scheduling optimization expert.

Suggest schedules that:
- Optimize resource utilization
- Meet deadlines
- Consider dependencies
- Balance workload""",
        default_user_prompt="""Tasks: {tasks}

Resources: {resources}
Constraints: {constraints}

Suggest optimal schedule.""",
        display_order=56,
    ),
    "categorize_issue": TopicSeedData(
        topic_id="categorize_issue",
        topic_name="Categorize Issue",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Categorize operational issue by type and severity",
        temperature=0.6,
        max_tokens=1024,
        default_system_prompt="""You are an issue classification expert.

Categorize issues by:
- Type (technical, process, people, resource)
- Severity (critical, high, medium, low)
- Impact area
- Urgency level""",
        default_user_prompt="""Issue: {issue}

Categorize with confidence scores.""",
        display_order=57,
    ),
    "assess_impact": TopicSeedData(
        topic_id="assess_impact",
        topic_name="Assess Impact",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Assess business impact of operational issue",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are a business impact analyst.

Assess impact across:
- Financial impact
- Operational impact
- Customer impact
- Strategic impact
- Risk level""",
        default_user_prompt="""Issue: {issue}

Business context: {business_context}

Provide comprehensive impact assessment.""",
        display_order=58,
    ),
    # ========== Section 6: Operations-Strategic Integration (22 topics) ==========
    # Due to size, I'll create a subset here and note that the full implementation
    # would include all 22. For now, implementing the first 10 as examples.
    "action_strategic_context": TopicSeedData(
        topic_id="action_strategic_context",
        topic_name="Action Strategic Context",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Get strategic context for a specific operational action",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are a strategic context analyst.

Provide strategic context showing how operational actions connect to:
- Strategic goals
- KPIs
- Business foundation
- Long-term vision""",
        default_user_prompt="""Action: {action_id}

Details: {action_details}

Provide strategic context and alignment analysis.""",
        display_order=60,
    ),
    "suggest_connections": TopicSeedData(
        topic_id="suggest_connections",
        topic_name="Suggest Connections",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Suggest strategic connections for operational actions",
        temperature=0.7,
        max_tokens=2048,
        default_system_prompt="""You are a strategic connections consultant.

Suggest meaningful connections between operational actions and strategic elements.""",
        default_user_prompt="""Action: {action}

Strategic context: {strategic_context}

Suggest strategic connections with rationale.""",
        display_order=61,
    ),
    "operations_strategic_alignment": TopicSeedData(
        topic_id="operations_strategic_alignment",
        topic_name="Operations Strategic Alignment",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Calculate strategic alignment of operational activities",
        temperature=0.6,
        max_tokens=3072,
        default_system_prompt="""You are an operations-strategy alignment analyst.

Calculate alignment between daily operations and strategic objectives.""",
        default_user_prompt="""Operations: {operations}

Strategy: {strategy}

Calculate alignment with detailed breakdown.""",
        display_order=62,
    ),
    # Continuing Operations-Strategic Integration topics
    "update_connections": TopicSeedData(
        topic_id="update_connections",
        topic_name="Update Connections",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Update strategic connections for an action",
        temperature=0.6,
        max_tokens=1024,
        default_system_prompt="""You are a strategic connections manager.

Validate and update strategic connections ensuring they remain meaningful and aligned.""",
        default_user_prompt="""Action: {action_id}

New connections: {connections}

Validate and confirm connection updates.""",
        display_order=63,
    ),
    "analyze_measure_impact": TopicSeedData(
        topic_id="analyze_measure_impact",
        topic_name="Analyze Measure Impact",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Analyze Measure impact of proposed actions",
        temperature=0.7,
        max_tokens=3072,
        default_system_prompt="""You are a Measure impact analyst.

Analyze how proposed actions will affect key performance measures, providing quantitative and qualitative assessments.""",
        default_user_prompt="""Action: {action}

Measures: {measures}

Analyze expected impact on each Measure.""",
        display_order=64,
    ),
    "record_measure_update": TopicSeedData(
        topic_id="record_measure_update",
        topic_name="Record Measure Update",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Record a Measure update event with validation",
        temperature=0.5,
        max_tokens=1024,
        default_system_prompt="""You are a Measure update validator.

Validate Measure updates for consistency, reasonableness, and strategic alignment.""",
        default_user_prompt="""Measure: {measure_id}

Update data: {update_data}

Validate and record the update.""",
        display_order=65,
    ),
    "get_measure_updates": TopicSeedData(
        topic_id="get_measure_updates",
        topic_name="Get Measure Updates",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Retrieve and summarize Measure update history",
        temperature=0.5,
        max_tokens=2048,
        default_system_prompt="""You are a Measure historian.

Provide clear summaries of Measure update history with trend analysis.""",
        default_user_prompt="""Measure: {measure_id}

Time range: {time_range}

Provide update history with trend insights.""",
        display_order=66,
    ),
    "issue_strategic_context": TopicSeedData(
        topic_id="issue_strategic_context",
        topic_name="Issue Strategic Context",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Get strategic context for an operational issue",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are a strategic issue analyst.

Provide strategic context showing how operational issues relate to strategic objectives and risks.""",
        default_user_prompt="""Issue: {issue_id}

Details: {issue_details}

Provide strategic context and implications.""",
        display_order=67,
    ),
    "generate_actions_from_issue": TopicSeedData(
        topic_id="generate_actions_from_issue",
        topic_name="Generate Actions from Issue",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Generate strategic actions from operational issue",
        temperature=0.8,
        max_tokens=3072,
        default_system_prompt="""You are an action planning expert.

Generate strategic actions that address operational issues while advancing strategic objectives.""",
        default_user_prompt="""Issue: {issue_id}

Details: {issue_details}
Strategic context: {strategic_context}

Generate actionable response plan.""",
        display_order=68,
    ),
    "complete_action": TopicSeedData(
        topic_id="complete_action",
        topic_name="Complete Action",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Mark action as complete with strategic impact assessment",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are an action completion analyst.

Assess completion quality and strategic impact, providing insights for continuous improvement.""",
        default_user_prompt="""Action: {action_id}

Completion data: {completion_data}

Assess completion and strategic impact.""",
        display_order=69,
    ),
    "measure_update_prompt": TopicSeedData(
        topic_id="measure_update_prompt",
        topic_name="Measure Update Prompt",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Get prompt for Measure update after action completion",
        temperature=0.7,
        max_tokens=1024,
        default_system_prompt="""You are a Measure update facilitator.

Generate helpful prompts to guide users in updating Measures after action completion.""",
        default_user_prompt="""Action: {action_id}

Details: {action_details}
Related Measures: {related_measures}

Generate Measure update prompt.""",
        display_order=70,
    ),
    "update_measure_from_action": TopicSeedData(
        topic_id="update_measure_from_action",
        topic_name="Update Measure from Action",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Update Measure based on action completion",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are a Measure update processor.

Process and validate Measure updates resulting from action completions.""",
        default_user_prompt="""Action: {action_id}

Measure: {measure_id}
Update value: {update_value}

Process Measure update.""",
        display_order=71,
    ),
    "convert_issue_to_actions": TopicSeedData(
        topic_id="convert_issue_to_actions",
        topic_name="Convert Issue to Actions",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Convert operational issue into actionable items",
        temperature=0.8,
        max_tokens=3072,
        default_system_prompt="""You are an issue resolution strategist.

Convert issues into clear, actionable steps with priorities and assignments.""",
        default_user_prompt="""Issue: {issue_id}

Details: {issue_details}

Convert to actionable items.""",
        display_order=72,
    ),
    "check_closure_eligibility": TopicSeedData(
        topic_id="check_closure_eligibility",
        topic_name="Check Closure Eligibility",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Check if issue is eligible for closure",
        temperature=0.6,
        max_tokens=1024,
        default_system_prompt="""You are an issue closure validator.

Assess whether issues meet closure criteria based on resolution quality and impact.""",
        default_user_prompt="""Issue: {issue_id}

Status: {issue_status}

Assess closure eligibility.""",
        display_order=73,
    ),
    "close_issue": TopicSeedData(
        topic_id="close_issue",
        topic_name="Close Issue",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Close operational issue with strategic impact assessment",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are an issue closure analyst.

Process issue closures with lessons learned and strategic impact assessment.""",
        default_user_prompt="""Issue: {issue_id}

Closure data: {closure_data}

Process closure and assess impact.""",
        display_order=74,
    ),
    "strategic_context": TopicSeedData(
        topic_id="strategic_context",
        topic_name="Strategic Context",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Get comprehensive strategic planning context",
        temperature=0.6,
        max_tokens=4096,
        default_system_prompt="""You are a strategic context provider.

Deliver comprehensive strategic context including foundation, goals, KPIs, and current initiatives.""",
        default_user_prompt="""Tenant: {tenant_id}

Context type: {context_type}

Provide strategic context.""",
        display_order=75,
    ),
    "create_action_with_context": TopicSeedData(
        topic_id="create_action_with_context",
        topic_name="Create Action with Context",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Create action with full strategic context",
        temperature=0.7,
        max_tokens=2048,
        default_system_prompt="""You are an action creation strategist.

Create actions with rich strategic context, ensuring alignment from inception.""",
        default_user_prompt="""Action data: {action_data}

Strategic context: {strategic_context}

Create strategically-aligned action.""",
        display_order=76,
    ),
    "action_relationships": TopicSeedData(
        topic_id="action_relationships",
        topic_name="Action Relationships",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Get strategic relationships for an action",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are a relationship mapper.

Map strategic relationships showing how actions connect to goals, KPIs, and other actions.""",
        default_user_prompt="""Action: {action_id}

Provide relationship map.""",
        display_order=77,
    ),
    "measure_sync_to_strategic": TopicSeedData(
        topic_id="measure_sync_to_strategic",
        topic_name="Measure Sync to Strategic",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Sync operational Measure updates to strategic planning",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are a Measure synchronization manager.

Sync operational Measure updates to strategic planning, identifying impacts and misalignments.""",
        default_user_prompt="""Measure updates: {measure_updates}

Sync to strategic planning.""",
        display_order=78,
    ),
    "measure_sync_from_strategic": TopicSeedData(
        topic_id="measure_sync_from_strategic",
        topic_name="Measure Sync from Strategic",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Sync strategic Measures to operational tracking",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are a Measure synchronization manager.

Sync strategic Measures to operational tracking, ensuring consistency and traceability.""",
        default_user_prompt="""Strategic Measures: {strategic_measures}

Sync to operations.""",
        display_order=79,
    ),
    "detect_measure_conflicts": TopicSeedData(
        topic_id="detect_measure_conflicts",
        topic_name="Detect Measure Conflicts",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Detect Measure conflicts between operations and strategy",
        temperature=0.6,
        max_tokens=3072,
        default_system_prompt="""You are a Measure conflict detector.

Identify conflicts, discrepancies, and misalignments between operational and strategic Measures.""",
        default_user_prompt="""Operational Measures: {operational_measures}

Strategic Measures: {strategic_measures}

Detect conflicts and misalignments.""",
        display_order=80,
    ),
    "resolve_measure_conflict": TopicSeedData(
        topic_id="resolve_measure_conflict",
        topic_name="Resolve Measure Conflict",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.OPERATIONS_AI.value,
        description="Resolve Measure conflict with AI recommendations",
        temperature=0.7,
        max_tokens=2048,
        default_system_prompt="""You are a Measure conflict resolution expert.

Recommend resolution strategies that maintain strategic alignment while respecting operational realities.""",
        default_user_prompt="""Conflict: {conflict_id}

Details: {conflict_details}

Recommend resolution approach.""",
        display_order=81,
    ),
    # ========== Section 7: Analysis API (4 topics) ==========
    "alignment_analysis": TopicSeedData(
        topic_id="alignment_analysis",
        topic_name="Alignment Analysis",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ANALYSIS.value,
        description="Analyze alignment between goals and purpose",
        temperature=0.5,
        max_tokens=2048,
        default_system_prompt="""You are an alignment analysis expert.

Calculate precise alignment scores (0-100) between goals and business foundation.

Analyze alignment across:
- Core values alignment
- Purpose alignment
- Vision alignment
- Strategic coherence

Provide data-driven, objective scoring.""",
        default_user_prompt="""Goal: {goal}

Business foundation: {business_foundation}

Calculate alignment scores and provide detailed analysis.""",
        display_order=90,
    ),
    "strategy_analysis": TopicSeedData(
        topic_id="strategy_analysis",
        topic_name="Strategy Analysis",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ANALYSIS.value,
        description="Analyze business strategy effectiveness",
        temperature=0.7,
        max_tokens=3072,
        default_system_prompt="""You are a strategy analysis expert.

Analyze business strategy for:
- Clarity and focus
- Market fit
- Feasibility
- Competitive advantage""",
        default_user_prompt="""Strategy: {strategy}

Context: {context}

Analyze strategy effectiveness.""",
        display_order=91,
    ),
    "measure_analysis": TopicSeedData(
        topic_id="measure_analysis",
        topic_name="Measure Analysis",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ANALYSIS.value,
        description="Analyze Measure effectiveness",
        temperature=0.6,
        max_tokens=2048,
        default_system_prompt="""You are a Measure analyst.

Analyze Measures for:
- Relevance to goals
- Measurability
- Actionability
- Performance trends""",
        default_user_prompt="""Measures: {measures}

Performance data: {performance_data}

Analyze Measure effectiveness.""",
        display_order=92,
    ),
    "operations_analysis": TopicSeedData(
        topic_id="operations_analysis",
        topic_name="Operations Analysis",
        topic_type=TopicType.SINGLE_SHOT.value,
        category=TopicCategory.ANALYSIS.value,
        description="Perform operational analysis (SWOT, root cause, etc.)",
        temperature=0.7,
        max_tokens=3072,
        default_system_prompt="""You are an operations analyst.

Perform detailed operational analysis based on provided data and analysis type.""",
        default_user_prompt="""Operations data: {operations_data}

Analysis type: {analysis_type}

Perform analysis.""",
        display_order=93,
    ),
}


def get_seed_data_for_topic(topic_id: str) -> TopicSeedData | None:
    """Get seed data for a specific topic.

    Args:
        topic_id: Topic identifier

    Returns:
        TopicSeedData if found, None otherwise
    """
    return TOPIC_SEED_DATA.get(topic_id)


def list_all_seed_data() -> list[TopicSeedData]:
    """Get all topic seed data.

    Returns:
        List of all TopicSeedData objects
    """
    return list(TOPIC_SEED_DATA.values())


def get_seed_data_by_category(category: str) -> list[TopicSeedData]:
    """Get seed data for topics in a specific category.

    Args:
        category: Category name

    Returns:
        List of TopicSeedData for the category
    """
    return [seed for seed in TOPIC_SEED_DATA.values() if seed.category == category]


def get_seed_data_by_type(topic_type: str) -> list[TopicSeedData]:
    """Get seed data for topics of a specific type.

    Args:
        topic_type: Topic type (conversation_coaching, single_shot, kpi_system)

    Returns:
        List of TopicSeedData for the type
    """
    return [seed for seed in TOPIC_SEED_DATA.values() if seed.topic_type == topic_type]


__all__ = [
    "TOPIC_SEED_DATA",
    "TopicSeedData",
    "get_seed_data_by_category",
    "get_seed_data_by_type",
    "get_seed_data_for_topic",
    "list_all_seed_data",
]
