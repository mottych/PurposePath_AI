# Archived Router Files

**Archived Date:** October 27, 2025  
**Issue Reference:** #61

## Reason for Archival

These router files were archived because they:
1. Contain only stub implementations with TODO comments
2. Have functionality that duplicates or conflicts with active routers
3. Are not included in main.py and not part of the API specification

## Archived Files

### suggestions.py
- **Status:** Stub implementation
- **Reason:** Duplicates functionality in `onboarding.py`
- **Endpoint:** `POST /onboarding` for suggestions
- **Notes:** Basic JWT auth implementation, can be reference for auth patterns if needed

### website.py
- **Status:** Stub implementation  
- **Reason:** Duplicates functionality in `onboarding.py` which has `POST /website/scan`
- **Endpoints:** `/scan`, `/analysis/{domain}`, `/bulk-scan`
- **Notes:** Contains TODO notes for future website analysis features

### coaching.py
- **Status:** Stub implementation
- **Reason:** Endpoints not in API specification, all stubs with TODO comments
- **Endpoints:** `/onboarding`, `/strategic-planning`, `/performance-coaching`, `/leadership-coaching`
- **Notes:** Contains ideas for future coaching features that may be implemented differently

## Recovery

If any functionality from these files is needed:
1. Review the archived file for the specific implementation
2. Extract the relevant code patterns or logic
3. Implement properly in the appropriate active router
4. Follow current architecture patterns and type safety standards

## Related Active Routers

- **onboarding.py** - Active implementation of onboarding AI features
- **conversations.py** - Active implementation of coaching conversations
- **analysis.py** - Active implementation of business analysis features

---

**Do not restore these files without reviewing current API specification and architecture.**
