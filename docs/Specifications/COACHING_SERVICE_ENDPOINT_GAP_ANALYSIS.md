# Coaching Service Endpoint Gap Analysis

**Generated**: 2025-12-02
**Source**: Comparison of frontend specification vs. current backend implementation
**Backend Branch**: dev
**Specification**: COACHING_SERVICE_ENDPOINTS_AI_AGENT.md

---

## Executive Summary

**Total Endpoints Expected**: 44
**Total Endpoints Implemented**: 21
**Missing Endpoints**: 23 (52%)
**Mismatched Paths**: 4 (9%)

**Status**: 🔴 **CRITICAL GAPS** - Major missing functionality for Operations-Strategic Integration

---

## Section 1: Onboarding & Business Intelligence (4 endpoints)

### ✅ IMPLEMENTED

| # | Endpoint | Method | Status | Backend Path |
|---|----------|--------|--------|--------------|
| 1 | `/website/scan` | POST | ✅ Implemented | `/website/scan` |
| 2 | `/suggestions/onboarding` | POST | ✅ Implemented | `/suggestions/onboarding` |
| 3 | `/coaching/onboarding` | POST | ✅ Implemented | `/coaching/onboarding` |
| 4 | `/multitenant/conversations/business-data` | GET | ✅ Implemented | `/multitenant/conversations/business-data` |

**Section Status**: ✅ **100% Complete** (4/4)

---

## Section 2: Conversation API (DEPRECATED - REMOVED)

> ⚠️ **DEPRECATED**: These endpoints were removed in favor of the Generic Coaching Engine (`/ai/coaching/*`).
> See "Conversation Coaching Endpoints (Topic-Based)" section for the replacement API.

| # | Endpoint | Method | Status | Migration Path |
|---|----------|--------|--------|----------------|
| 5 | `/conversations/initiate` | POST | ❌ Removed | Use `POST /ai/coaching/start` |
| 6 | `/conversations/{conversationId}/message` | POST | ❌ Removed | Use `POST /ai/coaching/message` |
| 7 | `/conversations/{conversationId}` | GET | ❌ Removed | Use `GET /ai/coaching/topics` |

**Section Status**: ❌ **DEPRECATED** (removed per issue #156)

---

## Section 3: Insights Generation (1 endpoint)

### ✅ IMPLEMENTED

| # | Endpoint | Method | Status | Backend Path |
|---|----------|--------|--------|--------------|
| 8 | `/insights/generate` | POST | ✅ Implemented | `/insights/generate` |

**Section Status**: ✅ **100% Complete** (1/1)

---

## Section 4: Strategic Planning AI (5 endpoints)

### ⚠️ PATH MISMATCHES

| # | Expected Endpoint | Method | Status | Backend Path | Issue |
|---|-------------------|--------|--------|--------------|-------|
| 9 | `/coaching/strategy-suggestions` | POST | ⚠️ Mismatch | `/coaching/strategy-suggestions` | ✅ Path correct |
| 10 | `/api/coaching/kpi-recommendations` | POST | ⚠️ Mismatch | `/analysis/kpi` | **Path differs** |
| 11 | `/api/coaching/alignment-check` | POST | ⚠️ Mismatch | `/analysis/alignment` | **Path differs** |
| 12 | `/api/coaching/alignment-explanation` | POST | ✅ Implemented | `/coaching/alignment-explanation` | ✅ Path correct |
| 13 | `/api/coaching/alignment-suggestions` | POST | ✅ Implemented | `/coaching/alignment-suggestions` | ✅ Path correct |

**Section Status**: ⚠️ **60% Aligned** (3/5 correct paths, 2/5 path mismatches)

### Issues:
1. **Endpoint #10**: Frontend expects `/api/coaching/kpi-recommendations` but backend has `/analysis/kpi`
2. **Endpoint #11**: Frontend expects `/api/coaching/alignment-check` but backend has `/analysis/alignment`

---

## Section 5: Operations AI (9 endpoints)

### ✅ IMPLEMENTED

| # | Endpoint | Method | Status | Backend Path |
|---|----------|--------|--------|--------------|
| 14 | `/api/operations/root-cause-suggestions` | POST | ✅ Implemented | `/operations/root-cause-suggestions` |
| 17 | `/api/operations/action-suggestions` | POST | ✅ Implemented | `/operations/action-suggestions` |
| 18 | `/api/operations/optimize-action-plan` | POST | ⚠️ Maybe | `/operations/strategic-alignment` |
| 19 | `/api/operations/prioritization-suggestions` | POST | ✅ Implemented | `/operations/prioritization-suggestions` |
| 20 | `/api/operations/scheduling-suggestions` | POST | ✅ Implemented | `/operations/scheduling-suggestions` |

### ❌ MISSING

| # | Endpoint | Method | Status |
|---|----------|--------|--------|
| 15 | `/api/operations/swot-analysis` | POST | ❌ **Missing** |
| 16 | `/api/operations/five-whys-questions` | POST | ❌ **Missing** |
| 21 | `/api/operations/categorize-issue` | POST | ❌ **Missing** |
| 22 | `/api/operations/assess-impact` | POST | ❌ **Missing** |

**Section Status**: 🟡 **56% Complete** (5/9 implemented, 4/9 missing)

---

## Section 6: Operations-Strategic Integration (22 endpoints)

### ❌ COMPLETELY MISSING

All 22 endpoints in this section are **NOT implemented**:

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 23 | `/api/operations/actions/{actionId}/strategic-context` | GET | Get strategic context for action |
| 24 | `/api/operations/actions/suggest-connections` | POST | Suggest strategic connections |
| 25 | `/api/operations/actions/{actionId}/connections` | PUT | Update strategic connections |
| 26 | `/api/operations/actions/analyze-kpi-impact` | POST | Analyze KPI impact |
| 27 | `/api/operations/kpi-updates` | POST | Record KPI update |
| 28 | `/api/operations/kpi-updates` | GET | Get KPI update history |
| 29 | `/api/operations/issues/{issueId}/strategic-context` | GET | Get issue strategic context |
| 30 | `/api/operations/issues/{issueId}/generate-actions` | POST | Generate actions from issue |
| 31 | `/api/operations/strategic-alignment` | POST | Calculate operations alignment |
| 32 | `/api/operations/actions/{actionId}/complete` | POST | Complete action |
| 33 | `/api/operations/actions/{actionId}/kpi-update-prompt` | GET | Get KPI update prompt |
| 34 | `/api/operations/actions/{actionId}/update-kpi` | POST | Update KPI from action |
| 35 | `/api/operations/issues/{issueId}/convert-to-actions` | POST | Convert issue to actions |
| 36 | `/api/operations/issues/{issueId}/closure-eligibility` | GET | Check issue closure eligibility |
| 37 | `/api/operations/issues/{issueId}/close` | POST | Close issue |
| 38 | `/api/strategic/context` | GET | Get strategic context |
| 39 | `/api/operations/actions/create-with-context` | POST | Create action with context |
| 40 | `/api/operations/actions/{actionId}/relationships` | GET | Get action relationships |
| 41 | `/api/operations/kpi-sync/to-strategic-planning` | POST | Sync KPI to strategic |
| 42 | `/api/operations/kpi-sync/from-strategic-planning` | POST | Sync KPI from strategic |
| 43 | `/api/operations/kpi-conflicts` | GET | Detect KPI conflicts |
| 44 | `/api/operations/kpi-conflicts/{conflictId}/resolve` | POST | Resolve KPI conflict |

**Section Status**: ❌ **0% Complete** (0/22 implemented)

---

## Implemented But Not In Spec

The following endpoints exist in the backend but are NOT in the frontend specification:

| Endpoint | Method | Backend Path | Notes |
|----------|--------|--------------|-------|
| Strategic Planning | POST | `/coaching/strategic-planning` | Legacy coaching endpoint |
| Performance Coaching | POST | `/coaching/performance-coaching` | Legacy coaching endpoint |
| Leadership Coaching | POST | `/coaching/leadership-coaching` | Legacy coaching endpoint |
| Strategy Analysis | POST | `/analysis/strategy` | May overlap with strategy suggestions |
| Operations Analysis | POST | `/analysis/operations` | Purpose unclear |
| Website Analysis | GET | `/website/analysis/{domain}` | Additional website feature |
| Website Bulk Scan | POST | `/website/bulk-scan` | Additional website feature |
| Topics Available | GET | `/topics/available` | Topics feature (may be deprecated) |
| Conversation Pause | POST | `/conversations/{conversation_id}/pause` | Not in spec |
| Conversation Complete | POST | `/conversations/{conversation_id}/complete` | Not in spec |
| Health Check | GET | `/health/` | Infrastructure endpoint |
| Health Ready | GET | `/health/ready` | Infrastructure endpoint |
| Insights Categories | GET | `/insights/categories` | Not in spec |
| Insights Priorities | GET | `/insights/priorities` | Not in spec |
| Insights Summary | GET | `/insights/summary` | Not in spec |
| Insight Dismiss | POST | `/insights/{insight_id}/dismiss` | Not in spec |
| Insight Acknowledge | POST | `/insights/{insight_id}/acknowledge` | Not in spec |

---

## Critical Path Mismatches

### Issue #1: KPI Recommendations Path Mismatch
- **Frontend expects**: `/api/coaching/kpi-recommendations`
- **Backend implements**: `/analysis/kpi`
- **Impact**: 🔴 **HIGH** - Frontend cannot call KPI recommendations
- **Action**: Update backend to match `/api/coaching/kpi-recommendations` OR update frontend client

### Issue #2: Alignment Check Path Mismatch
- **Frontend expects**: `/api/coaching/alignment-check`
- **Backend implements**: `/analysis/alignment`
- **Impact**: 🔴 **HIGH** - Frontend cannot calculate alignment
- **Action**: Update backend to match `/api/coaching/alignment-check` OR update frontend client

### Issue #3: API Prefix Inconsistency
- **Frontend spec**: Uses `/api/coaching/` and `/api/operations/` prefixes
- **Backend implements**: Uses `/coaching/`, `/operations/`, `/analysis/` without `/api` prefix
- **Impact**: 🟡 **MEDIUM** - Base URL configuration may compensate
- **Note**: Check if base URL in frontend already includes correct routing

---

## Priority Recommendations

### P0 - Critical (Blocks Core Features)
1. **Fix path mismatches** for KPI recommendations (#10) and alignment check (#11)
2. **Implement missing Operations AI endpoints** (#15, #16, #21, #22) - 4 endpoints

### P1 - High (Blocks Major Features)
3. **Implement Operations-Strategic Integration** (Section 6) - 22 endpoints
   - This is the largest missing piece
   - Required for full operations-strategic planning integration
   - May need phased implementation

### P2 - Medium (Nice to Have)
4. **Clean up deprecated endpoints** (coaching types, topics)
5. **Align `/api` prefix** usage across all endpoints
6. **Document extra backend endpoints** not in spec (insights actions, etc.)

---

## Implementation Effort Estimate

| Section | Missing | Complexity | Est. Hours | Priority |
|---------|---------|------------|------------|----------|
| Path Fixes | 2 | Low | 2-4h | P0 |
| Operations AI Missing | 4 | Medium | 12-16h | P0 |
| Ops-Strategic Integration | 22 | High | 60-80h | P1 |
| Cleanup & Alignment | Various | Low | 8-12h | P2 |
| **Total** | **28** | - | **82-112h** | - |

**Estimated Timeline**: 2-3 weeks for P0+P1

---

## Next Steps

1. **Verify Base URL Configuration**
   - Check if frontend base URL already handles `/api` prefix
   - May resolve some "mismatches" if base URL is configured correctly

2. **Prioritize Path Fixes** (P0)
   - Fix `/analysis/kpi` → `/api/coaching/kpi-recommendations`
   - Fix `/analysis/alignment` → `/api/coaching/alignment-check`

3. **Implement Missing Operations AI** (P0)
   - SWOT analysis generation (#15)
   - Five Whys questions (#16)
   - Issue categorization (#21)
   - Impact assessment (#22)

4. **Phase Operations-Strategic Integration** (P1)
   - Phase 1: Action strategic context (endpoints #23-26)
   - Phase 2: Issue strategic context (endpoints #29-30)
   - Phase 3: KPI sync and conflicts (endpoints #27-28, #31-34, #41-44)
   - Phase 4: Advanced operations (endpoints #35-40)

5. **Documentation**
   - Update API documentation with current endpoints
   - Remove/deprecate unused endpoints
   - Align naming conventions

---

## Appendix A: Full Endpoint Mapping

### Currently Implemented Endpoints

```
GET    /health/
GET    /health/ready
POST   /website/scan
GET    /website/analysis/{domain}
POST   /website/bulk-scan
POST   /suggestions/onboarding
POST   /coaching/onboarding
POST   /coaching/strategic-planning
POST   /coaching/performance-coaching
POST   /coaching/leadership-coaching
POST   /coaching/alignment-explanation
POST   /coaching/alignment-suggestions
POST   /coaching/strategy-suggestions
# Legacy /conversations/* endpoints REMOVED - use /ai/coaching/* instead
POST   /ai/coaching/start
POST   /ai/coaching/message
POST   /ai/coaching/complete
POST   /ai/coaching/pause
GET    /ai/coaching/topics
POST   /multitenant/conversations/initiate
POST   /multitenant/conversations/{conversation_id}/message
GET    /multitenant/conversations/business-data
GET    /multitenant/conversations/{conversation_id}
POST   /multitenant/conversations/{conversation_id}/complete
POST   /multitenant/conversations/{conversation_id}/pause
DELETE /multitenant/conversations/{conversation_id}
GET    /multitenant/conversations/
GET    /multitenant/conversations/tenant/all
POST   /insights/generate
GET    /insights/categories
GET    /insights/priorities
POST   /insights/{insight_id}/dismiss
POST   /insights/{insight_id}/acknowledge
GET    /insights/summary
POST   /analysis/alignment
POST   /analysis/strategy
POST   /analysis/kpi
POST   /analysis/operations
POST   /operations/strategic-alignment
POST   /operations/prioritization-suggestions
POST   /operations/scheduling-suggestions
POST   /operations/root-cause-suggestions
POST   /operations/action-suggestions
GET    /topics/available
```

**Total**: 43 implemented endpoints (including infrastructure and extras not in spec)

---

**Report Generated By**: AI Agent
**Review Required**: Yes
**Stakeholders**: Frontend Team, Backend Team, Product Owner
