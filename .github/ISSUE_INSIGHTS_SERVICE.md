# Implement AI-Powered Business Insights Service

## 🎯 Overview

Implement the Insights Service to generate AI-powered coaching insights for business owners based on their operational data. The service will analyze business foundation, goals, performance metrics, actions, and issues to provide actionable recommendations.

## 📋 Requirements

### Business Requirements
- Generate 5-10 actionable insights per tenant
- Categories: strategy, operations, finance, marketing, leadership
- Priorities: low, medium, high, critical
- Insights should be specific and actionable
- Include suggested actions for each insight

### Data Sources (All from .NET APIs)

**1. Business Foundation** (Account Service)
- Endpoint: `GET /business/foundation`
- Data: vision, purpose, coreValues[], targetMarket, valueProposition

**2. Goals Data** (Traction Service)
- Endpoint: `GET /goals`
- Data: title, intent, strategies[], kpis[], progress, status

**3. Goal Statistics** (Traction Service)
- Endpoint: `GET /goals/stats`
- Data: totalGoals, completionRate, atRisk, behindSchedule

**4. Performance Score** (Traction Service)
- Endpoint: `GET /performance/score`
- Data: overallScore, goals score, strategies score, kpis score, actions score

**5. Actions** (Traction Service)
- Endpoint: `GET /api/operations/actions`
- Data: Recent actions, status, priority

**6. Issues** (Traction Service)
- Endpoint: `GET /api/operations/issues`
- Data: Open issues, businessImpact, priority

## 🏗️ Architecture

```
Frontend Request
    ↓
GET /insights/ (Coaching Service)
    ↓
InsightsService.get_insights()
    ↓
1. Check cache (Redis/DynamoDB TTL)
    ↓
2. Fetch data from .NET APIs via BusinessApiClient
    ↓
3. Load prompt template from S3
    ↓
4. Generate insights via LLM (Claude)
    ↓
5. Parse & validate response
    ↓
6. Store in DynamoDB with TTL (24 hours)
    ↓
7. Return paginated response
```

## 📁 Files to Modify/Create

### Modify
1. `coaching/src/services/insights_service.py`
   - Replace stub implementation
   - Add data fetching methods
   - Add LLM integration
   - Add caching logic

2. `coaching/src/api/routes/insights.py`
   - Already complete, no changes needed
   - Endpoints: GET /, GET /summary, GET /categories, POST /{id}/dismiss, POST /{id}/acknowledge

3. `coaching/src/models/responses.py`
   - `InsightResponse` - Already defined
   - `InsightsSummaryResponse` - Already defined
   - `InsightActionResponse` - Already defined

### Create
4. `coaching/prompts/insights_generation/v1.0.json` (S3)
   - Prompt template for insight generation

5. `coaching/src/infrastructure/cache/insights_cache.py` (Optional)
   - Caching layer for insights

## 🔧 Implementation Details

### Step 1: Data Fetching Service

```python
# coaching/src/services/insights_service.py

async def _fetch_business_context(self, tenant_id: str) -> Dict[str, Any]:
    """Fetch all business data needed for insights generation."""
    
    try:
        # Parallel data fetching
        foundation, goals, stats, performance, actions, issues = await asyncio.gather(
            self.business_api_client.get_organizational_context(tenant_id),
            self._fetch_goals(tenant_id),
            self._fetch_goal_stats(tenant_id),
            self._fetch_performance_score(tenant_id),
            self._fetch_actions(tenant_id),
            self._fetch_issues(tenant_id)
        )
        
        return {
            "foundation": foundation,
            "goals": goals,
            "stats": stats,
            "performance": performance,
            "actions": actions,
            "issues": issues,
            "tenant_id": tenant_id
        }
    except Exception as e:
        logger.error("Failed to fetch business context", tenant_id=tenant_id, error=str(e))
        raise
```

### Step 2: LLM Integration

```python
async def _generate_insights_with_llm(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate insights using LLM based on business context."""
    
    # Load prompt template
    template = await self.prompt_service.get_template("insights_generation")
    
    # Render prompt with context
    rendered_prompt = template.render({
        "vision": context["foundation"].get("vision", ""),
        "purpose": context["foundation"].get("purpose", ""),
        "core_values": ", ".join(context["foundation"].get("coreValues", [])),
        "goal_stats": json.dumps(context["stats"], indent=2),
        "performance": json.dumps(context["performance"], indent=2),
        "at_risk_goals": context["stats"].get("atRisk", 0),
        "behind_schedule": context["stats"].get("behindSchedule", 0),
        "completion_rate": context["stats"].get("completionRate", 0),
        "overall_score": context["performance"].get("overallScore", 0),
        "recent_actions": json.dumps(context["actions"][:10], indent=2),  # Last 10 actions
        "open_issues": json.dumps([i for i in context["issues"] if i.get("status") != "closed"], indent=2)
    })
    
    # Call LLM
    response = await self.llm_service.generate(
        messages=[
            {
                "role": "system",
                "content": template.system_prompt
            },
            {
                "role": "user",
                "content": rendered_prompt
            }
        ],
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        temperature=0.7,
        max_tokens=4000
    )
    
    # Parse JSON response
    insights_json = json.loads(response)
    return insights_json
```

### Step 3: Caching & Storage

```python
async def get_insights(
    self,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: str = None
) -> PaginatedResponse[InsightResponse]:
    """Get coaching insights with pagination and filtering."""
    
    # Check cache
    cache_key = f"insights:{tenant_id}"
    cached_insights = await self._get_from_cache(cache_key)
    
    if not cached_insights:
        # Fetch data
        context = await self._fetch_business_context(tenant_id)
        
        # Generate insights
        insights_raw = await self._generate_insights_with_llm(context)
        
        # Parse and validate
        insights = self._parse_insights(insights_raw, tenant_id)
        
        # Store in cache (24 hour TTL)
        await self._store_in_cache(cache_key, insights, ttl=86400)
    else:
        insights = cached_insights
    
    # Apply filters
    filtered = self._apply_filters(insights, category, priority, status)
    
    # Paginate
    paginated = self._paginate(filtered, page, page_size)
    
    return paginated
```

### Step 4: Prompt Template

**Upload to S3:** `s3://pp-ai-prompts/insights_generation/v1.0.json`

```json
{
  "topic": "insights_generation",
  "version": "v1.0",
  "phase": "analysis",
  "is_active": true,
  "metadata": {
    "title": "Business Insights Generator",
    "description": "Analyzes business data to generate actionable coaching insights",
    "category": "analytics",
    "tags": ["insights", "analysis", "recommendations"]
  },
  "system_prompt": "You are an expert business coach analyzing operational data to provide actionable insights. Generate 5-10 specific, actionable insights based on the business data provided. Focus on: 1) Alignment between vision/purpose and actual performance, 2) Goal achievement patterns, 3) Strategic opportunities, 4) Operational improvements, 5) Risk areas. Each insight must be specific, actionable, and include concrete suggested actions.",
  "user_prompt_template": "Analyze this business data and generate insights:\n\n## Business Foundation\nVision: {{vision}}\nPurpose: {{purpose}}\nCore Values: {{core_values}}\n\n## Performance Metrics\nOverall Score: {{overall_score}}/100\nGoal Completion Rate: {{completion_rate}}%\nGoals At Risk: {{at_risk_goals}}\nGoals Behind Schedule: {{behind_schedule}}\n\n## Detailed Performance\n{{performance}}\n\n## Goal Statistics\n{{goal_stats}}\n\n## Recent Actions (Last 10)\n{{recent_actions}}\n\n## Open Issues\n{{open_issues}}\n\n---\n\nProvide insights in this JSON format:\n[\n  {\n    \"title\": \"Brief title (max 60 chars)\",\n    \"description\": \"Detailed explanation of the insight (2-3 sentences)\",\n    \"category\": \"strategy|operations|finance|marketing|leadership\",\n    \"priority\": \"low|medium|high|critical\",\n    \"actionable\": true|false,\n    \"suggestedActions\": [\n      \"Specific action 1\",\n      \"Specific action 2\",\n      \"Specific action 3\"\n    ]\n  }\n]\n\nRules:\n- Generate 5-10 insights\n- Each insight must be specific to THIS business\n- Reference actual data points (scores, counts, etc.)\n- Prioritize based on business impact\n- Mix categories (don't focus only on one area)\n- Be constructive and actionable\n- Return ONLY valid JSON, no other text",
  "variables": [
    "vision",
    "purpose",
    "core_values",
    "goal_stats",
    "performance",
    "at_risk_goals",
    "behind_schedule",
    "completion_rate",
    "overall_score",
    "recent_actions",
    "open_issues"
  ],
  "created_at": "2025-10-21T00:00:00Z",
  "created_by": "system"
}
```

## ✅ Acceptance Criteria

### Functional
- [ ] GET /insights/ returns paginated insights
- [ ] Insights are generated from real .NET API data
- [ ] Each insight has: title, description, category, priority, suggestedActions
- [ ] Filters work: category, priority, status
- [ ] Insights are cached for 24 hours per tenant
- [ ] POST /{id}/dismiss marks insight as dismissed
- [ ] POST /{id}/acknowledge marks insight as acknowledged
- [ ] GET /summary returns count by category and priority

### Data Quality
- [ ] Insights reference actual business data (scores, goals, etc.)
- [ ] Insights are specific to the tenant's business
- [ ] Suggested actions are concrete and actionable
- [ ] Categories are correctly assigned
- [ ] Priorities reflect actual business impact

### Performance
- [ ] Initial generation < 10 seconds
- [ ] Cached responses < 500ms
- [ ] Parallel API calls to .NET services
- [ ] Graceful degradation if some data sources unavailable

### Error Handling
- [ ] Handle .NET API failures gracefully
- [ ] Handle LLM failures with retry logic
- [ ] Handle malformed LLM responses
- [ ] Log all errors with context

## 🧪 Testing Requirements

### Unit Tests
```python
# tests/unit/test_insights_service.py

async def test_fetch_business_context_success(mocker):
    """Test successful data fetching from .NET APIs."""
    
async def test_generate_insights_with_llm(mocker):
    """Test LLM insight generation."""
    
async def test_parse_insights_valid_response():
    """Test parsing valid LLM JSON response."""
    
async def test_apply_filters():
    """Test category, priority, status filters."""
    
async def test_pagination():
    """Test pagination logic."""
```

### Integration Tests
```python
# tests/integration/test_insights_integration.py

async def test_insights_generation_end_to_end():
    """Test full insight generation flow."""
    
async def test_insights_caching():
    """Test cache hit/miss behavior."""
```

## 📊 Monitoring & Observability

### Metrics to Track
- Insight generation time (p50, p95, p99)
- Cache hit rate
- .NET API call latencies
- LLM call success rate
- Insights generated per tenant
- Filter usage patterns

### Logs to Add
```python
logger.info("Generating insights", tenant_id=tenant_id, cached=False)
logger.info("Insights generated", tenant_id=tenant_id, count=len(insights), duration_ms=duration)
logger.error("Failed to fetch business data", tenant_id=tenant_id, error=str(e))
```

## 🔗 Dependencies

- ✅ BusinessApiClient (exists)
- ✅ LLMService (exists)
- ✅ PromptService (exists)
- ✅ DynamoDB ConversationRepository (can extend for insights storage)
- ⚠️ Cache layer (Redis or DynamoDB TTL)

## 📈 Estimated Effort

- **Data fetching layer:** 4-6 hours
- **LLM integration:** 4-6 hours
- **Caching implementation:** 2-3 hours
- **Prompt template creation:** 2-3 hours
- **Testing:** 4-6 hours
- **Total:** 16-24 hours

## 🚀 Deployment Notes

1. Upload prompt template to S3
2. Set environment variables for cache TTL
3. Monitor LLM costs (Claude Sonnet ~$0.003/1K input tokens)
4. Set up CloudWatch alerts for generation failures
5. Consider batch generation for all tenants (nightly job)

## 📚 References

- Frontend Spec: `docs/Specifications/backend-integration-coaching-service.md` (Lines 639-684)
- .NET API Specs: `docs/Specifications/backend-integration-traction-service.md`
- Admin Template Spec: `docs/Specifications/pp_ai_backend_specification.md`

## 👥 Assignee

- Backend Developer familiar with LLM integration

## 🏷️ Labels

`feature`, `insights`, `llm`, `high-priority`, `backend`

---

**Created:** 2025-10-21  
**Status:** Ready for Implementation  
**Priority:** HIGH
