# Unimplemented & Mock Features Report

**Date:** October 21, 2025  
**Branch:** `dev`  
**Purpose:** Comprehensive list of stub/mock/unimplemented functionality

---

## 🎯 Executive Summary

| Category | Count | Priority | Status |
|----------|-------|----------|--------|
| **Stub Services** | 3 | High | Post-MVP |
| **Placeholder Workflow Steps** | 4 | Medium | Functional but minimal |
| **Removed MVP Features** | 2 | Low | Intentionally excluded |
| **Partial Implementations** | 5 | Medium | Basic functionality only |

---

## 🚫 **1. STUB SERVICES (Empty/Mock Returns)**

### 1.1 Insights Service ⚠️ **STUB IMPLEMENTATION**

**File:** `coaching/src/services/insights_service.py`

**Status:** Returns empty results - no real logic implemented

**Methods:**
- `get_insights()` - Returns empty `PaginatedResponse`
- `get_insights_summary()` - Returns empty summary with zero counts
- `get_available_categories()` - Returns hardcoded list
- `get_available_priorities()` - Returns hardcoded list

**What's Missing:**
```python
# TODO: Implement real insight generation logic
# This method should:
# 1. Query conversation data from DynamoDB
# 2. Fetch business metrics from BusinessApiClient
# 3. Use AI/LLM to analyze patterns and generate contextual insights
# 4. Store insights in database or generate on-demand
# 5. Apply filters and pagination
```

**Impact:** 
- Insights API endpoint works but returns no data
- Users won't see any coaching recommendations
- Dashboard insights section will be empty

**Related Issue:** #48 Phase 2

---

### 1.2 Business Data Repository ⚠️ **PLACEHOLDER**

**File:** `coaching/src/repositories/business_data_repository.py`

**Status:** Returns mock/empty data - no database integration

**Methods:**
- `get_business_metrics()` - Returns hardcoded empty metrics
  ```python
  return MetricsResponse(
      metric_type="business_overview",
      time_period="current",
      data_points=[],
      summary={"total_goals": "0", "active_projects": "0", "completion_rate": "0.0"},
      generated_at=datetime.now(UTC),
  )
  ```

- `get_business_data()` - Returns `None` (no query)
  ```python
  # Placeholder implementation - would query DynamoDB
  return None
  ```

- `update_business_data()` - Returns input unchanged (no save)
  ```python
  # Placeholder implementation - would update DynamoDB
  return business_data
  ```

**Impact:**
- Business metrics dashboard shows zeros
- No historical business data tracking
- Foundation/vision data not persisted

---

### 1.3 Website Scanning (Onboarding) ⚠️ **NOT IMPLEMENTED**

**File:** `coaching/src/services/onboarding_service.py`

**Status:** Raises `NotImplementedError`

**Method:**
```python
async def scan_website(self, url: str) -> Dict[str, Any]:
    """
    Scan a business website to extract information.
    
    Note: This is a stub implementation. Real implementation would:
    1. Use web scraping (BeautifulSoup, Playwright)
    2. Extract text from homepage, about, products pages
    3. Use AI to analyze and categorize content
    4. Handle anti-scraping measures
    """
    logger.info("Scanning website (stub implementation)", url=url)
    
    # TODO: Implement real website scraping
    raise NotImplementedError(
        "Website scanning feature is not yet implemented. "
        "Please manually enter your business information."
    )
```

**Impact:**
- Onboarding flow requires manual data entry
- Cannot auto-populate business info from website
- User experience less streamlined

**API Endpoint:** `POST /coaching/api/v1/onboarding/scan-website`
- Returns 501 Not Implemented error

---

## 🔨 **2. PARTIAL IMPLEMENTATIONS (Basic Functionality)**

### 2.1 Coaching Workflow Steps 📝 **PLACEHOLDER LOGIC**

**File:** `coaching/src/workflows/coaching_workflow.py`

**Status:** Steps exist but have minimal implementation

**Steps with Placeholder Logic:**

1. **Goal Exploration** (Line 258-264)
   ```python
   async def _process_goal_exploration(self, state: Dict[str, Any]) -> Dict[str, Any]:
       """Goal exploration - help user clarify their goals."""
       logger.info("Processing goal exploration", workflow_id=state["workflow_id"])
       
       # Placeholder implementation
       state["current_step"] = "action_planning"
       return state
   ```

2. **Action Planning** (Line 266-272)
   ```python
   async def _process_action_planning(self, state: Dict[str, Any]) -> Dict[str, Any]:
       """Action planning - create concrete next steps."""
       logger.info("Processing action planning", workflow_id=state["workflow_id"])
       
       # Placeholder implementation
       state["current_step"] = "reflection"
       return state
   ```

3. **Reflection** (Line 274-280)
   ```python
   async def _process_reflection(self, state: Dict[str, Any]) -> Dict[str, Any]:
       """Reflection - help user reflect on insights."""
       logger.info("Processing reflection", workflow_id=state["workflow_id"])
       
       # Placeholder implementation
       state["current_step"] = "next_steps"
       return state
   ```

4. **Next Steps** (Line 282-288)
   ```python
   async def _process_next_steps(self, state: Dict[str, Any]) -> Dict[str, Any]:
       """Next steps - summarize and plan follow-up."""
       logger.info("Processing next steps", workflow_id=state["workflow_id"])
       
       # Placeholder implementation
       state["current_step"] = "completion"
       return state
   ```

**Impact:**
- Workflow progresses through steps but doesn't do deep processing
- LLM integration works, but coaching logic is minimal
- Functional for MVP but lacks sophisticated coaching algorithms

---

### 2.2 LLM Streaming ⚠️ **NOT IMPLEMENTED**

**File:** `coaching/src/infrastructure/llm/bedrock_provider.py`

**Status:** Falls back to non-streaming

**Method:**
```python
async def generate_stream(
    self,
    messages: List[Dict[str, str]],
    model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    system_prompt: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Generate streaming response from Bedrock.
    
    Yields:
        Token strings as they are generated
    """
    # TODO: Implement streaming support with Bedrock's streaming API
    logger.warning("Streaming not yet implemented, falling back to non-streaming")
    
    response = await self.generate(messages, model, temperature, max_tokens, system_prompt)
    yield response
```

**Impact:**
- No real-time token streaming to UI
- Users see full response at once instead of progressively
- Perceived latency higher for long responses

---

### 2.3 Token Counting 📊 **APPROXIMATION**

**File:** `coaching/src/infrastructure/llm/bedrock_provider.py`

**Status:** Simple character-based estimation

**Method:**
```python
async def count_tokens(self, text: str, model: str) -> int:
    """
    Count tokens in text for a specific model.
    
    Note: Exact tokenization requires model-specific tokenizers
    """
    # Simple approximation: ~4 characters per token
    # TODO: Use proper tokenizer for each model
    return len(text) // 4
```

**Impact:**
- Inaccurate token counts (estimation only)
- May incorrectly calculate costs
- Could hit token limits unexpectedly

---

### 2.4 S3 Prompt Template Lookup ⚠️ **NOT EFFICIENT**

**File:** `coaching/src/infrastructure/repositories/s3_prompt_repository.py`

**Status:** ID lookup not implemented efficiently

**Method:**
```python
async def get_by_id(self, template_id: str) -> Optional[PromptTemplate]:
    """
    Get a prompt template by its ID.
    
    Note: This requires scanning S3 or maintaining an index.
          For now, this is not implemented efficiently.
    """
    # TODO: Implement efficient ID lookup (requires index)
    logger.warning("get_by_id not efficiently implemented", template_id=template_id)
    return None
```

**Impact:**
- Cannot retrieve templates by ID quickly
- Forces topic-based lookups only
- Performance issue if catalog grows

---

### 2.5 Conversation Resume Messages 📝 **TODO TEMPLATE**

**File:** `coaching/src/services/conversation_service.py`

**Status:** Uses hardcoded message instead of template

**Code:**
```python
# Generate resume message
# TODO: Use template for personalized resume message
_ = await self.prompt_service.get_template(conversation.topic)
resume_message = "Welcome back! Let's continue where we left off."
```

**Impact:**
- Resume messages not personalized
- Doesn't reference context from paused conversation
- Generic user experience

---

## ❌ **3. INTENTIONALLY REMOVED (MVP Exclusions)**

### 3.1 User Metrics API ⚠️ **REMOVED FROM MVP**

**File:** `coaching/src/infrastructure/external/business_api_client.py`

**Status:** Method removed, not in MVP scope

**Note in Code:**
```python
# NOTE: get_metrics() removed - not in MVP scope
# User performance metrics will be added post-MVP when tracking is implemented.
# For tenant-wide metrics, use Traction Service endpoints:
#   - GET /goals/stats
#   - GET /performance/score
```

**Impact:**
- Cannot fetch individual user performance metrics
- Dashboard metrics limited to organizational level
- User-specific analytics unavailable

**Post-MVP:** Requires:
- Performance tracking implementation
- Metrics calculation pipeline
- Historical data storage

---

### 3.2 User Roles & Departments 👥 **MVP SIMPLIFICATION**

**File:** `coaching/src/infrastructure/external/business_api_client.py`

**Status:** Hardcoded MVP fallbacks

**Current Implementation:**
```python
# Build context with MVP fallbacks
user_context = {
    "user_id": user_data.get("user_id"),
    "email": user_data.get("email"),
    "first_name": first_name,
    "last_name": last_name,
    "name": full_name,
    "tenant_id": tenant_id,
    # MVP Fallbacks
    "role": "Business Owner",      # Always "Business Owner"
    "department": None,             # No departments in MVP
    "position": "Owner",            # Always "Owner"
}
```

**MVP Assumptions:**
- Single user per tenant (business owner)
- No department structure
- No role hierarchy
- Default role = "Business Owner"

**Impact:**
- No multi-user support
- Cannot differentiate between team members
- No department-specific coaching

**Post-MVP:** Requires:
- User role management system
- Department structure
- Permission levels
- Team member profiles

---

## 📋 **4. SUMMARY BY PRIORITY**

### High Priority (Block Post-MVP Features)
1. ⚠️ **Insights Service** - Core feature for recommendations
2. ⚠️ **Business Data Repository** - Metrics and tracking
3. ⚠️ **Website Scanning** - Onboarding automation

### Medium Priority (Enhance UX)
4. 📝 **Coaching Workflow Steps** - Deeper coaching logic
5. ⚠️ **LLM Streaming** - Real-time response generation
6. 📊 **Token Counting** - Accurate billing/limits
7. ⚠️ **S3 Template Lookup** - Performance optimization

### Low Priority (Nice-to-Have)
8. 📝 **Resume Message Templates** - Personalization
9. 👥 **User Roles/Departments** - Multi-user support
10. ❌ **User Metrics API** - Individual analytics

---

## 🎯 **RECOMMENDATIONS**

### For Current MVP Deployment
✅ **SAFE TO DEPLOY** - All unimplemented features are:
- Clearly documented
- Not blocking core functionality
- Have appropriate fallbacks
- Return safe defaults

### Post-MVP Implementation Order

**Phase 1: Core Features (Sprint 1-2)**
1. Implement Insights Service (AI-driven recommendations)
2. Complete Business Data Repository (DynamoDB integration)
3. Add LLM Streaming (real-time responses)

**Phase 2: Enhanced UX (Sprint 3-4)**
4. Implement Website Scanning (auto-onboarding)
5. Enhance Coaching Workflow Steps (deeper logic)
6. Add proper Token Counting (accurate billing)

**Phase 3: Scale Features (Sprint 5+)**
7. Optimize S3 Template Lookup (indexing)
8. Add Resume Message Templates (personalization)
9. Implement User Roles/Departments (multi-user)
10. Add User Metrics API (analytics)

---

## 📞 **NEXT STEPS**

1. **Document**: Share this report with product team
2. **Prioritize**: Decide which features to implement first
3. **Plan**: Create tickets for each unimplemented feature
4. **Track**: Monitor user feedback on missing features
5. **Iterate**: Implement based on user needs and priorities

---

**Note:** This is a living document. Update as features are implemented or priorities change.

**Last Updated:** October 21, 2025  
**Prepared by:** Cascade AI  
**Status:** Complete and ready for product planning
