# Goal Created Email Insight User Prompt

Generate an email insight for the "goal created" trigger.

Context:

- Tenant business name: {business_name}
- User display name: {user_name}
- Goal id: {goal_id}
- Goal (full record as available): {goal}
- Goal title: {goal_title}
- Goal description: {goal_description}
- Goal intent (WHAT/WHY if present): {goal_intent}
- Business vision: {vision}
- Business purpose: {purpose}
- Core values: {core_values}
- Strategies linked to this goal (may be empty): {existing_strategies_for_goal}
- Measures linked to this goal (may be empty): {measures_formatted_for_goal}
- Locale hint: {locale}

Required behavior:

1. Return one JSON object only (no markdown/code fences).
2. Use schemaVersion "1.0".
3. Include 2-4 total blocks with at least:

   - one paragraph block
   - one list block with 2-4 short items
4. Add one cta block when a safe and useful next action exists.
5. Keep suggestions specific to this goal context; use foundation and strategy/measure context when helpful,
   without forcing a long alignment section.
6. Do not output HTML or XML in any field.
7. Do not add extra keys beyond the contract.

Return only JSON.
