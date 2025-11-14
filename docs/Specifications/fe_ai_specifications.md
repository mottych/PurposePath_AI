# Frontend AI Specifications - Breaking Changes

- Created on 11/13/2025

## Overview

This document lists all breaking changes to AI-related endpoints that affect the frontend application. This is a technical reference for what has changed, not how to fix it.

## Affected Endpoints

### `POST /api/v1/conversations/initiate`

**Status:** Modified (Breaking Change)

**Request Changes:**

**BEFORE:**

```json
{
  "topic": "core_values"
}
```

**AFTER:**

```json
{
  "topic": "core_values_coaching"
}
```

**Breaking Changes:**

1. **Topic ID Format Changed**
   - Old: Simple category name (e.g., "core_values", "purpose", "vision", "goals")
   - New: Specific topic identifier (e.g., "core_values_coaching", "purpose_discovery")
   - **Impact:** Frontend must use new topic IDs
   - **Migration Required:** Topic selection dropdowns/buttons must be updated

2. **Response Structure Modified**
   - Removed: `template_id` field
   - Removed: `phase` field (phases are no longer used)
   - Added: `topic_type` field (e.g., "coaching", "assessment")
   - **Impact:** Any code reading these fields will break

**Response Changes:**

**BEFORE:**

```json
{
  "conversation_id": "conv_123",
  "topic": "core_values",
  "phase": "introduction",
  "template_id": "template_core_values_intro",
  "initial_message": "Welcome...",
  "progress": 0.1
}
```

**AFTER:**

```json
{
  "conversation_id": "conv_123",
  "topic": "core_values_coaching",
  "topic_type": "coaching",
  "status": "active",
  "initial_message": "Welcome...",
  "progress": 0.0
}
```

---

### `GET /api/v1/topics/available`

**Status:** New Endpoint (Not Breaking - New Feature)

**Purpose:** Get list of available topics for selection

**Response:**

```json
{
  "topics": [
    {
      "topic_id": "core_values_coaching",
      "topic_name": "Core Values - Coaching Session",
      "category": "core_values",
      "topic_type": "coaching",
      "description": "Explore your core values through conversation",
      "is_active": true,
      "display_order": 1
    },
    {
      "topic_id": "core_values_assessment",
      "topic_name": "Core Values - Quick Assessment",
      "category": "core_values",
      "topic_type": "assessment",
      "description": "Structured assessment of your values",
      "is_active": true,
      "display_order": 2
    }
  ]
}
```

**Required Frontend Changes:**

- Update topic selection UI to call this endpoint
- Display `topic_name` to users (not `topic_id`)
- Filter by `category` if grouping topics
- Respect `display_order` for sorting
- Only show topics where `is_active: true`

---

### `POST /api/v1/conversations/{conversation_id}/message`

**Status:** Modified (Non-Breaking Change)

**Request:** No changes

**Response Changes:**

**BEFORE:**

```json
{
  "conversation_id": "conv_123",
  "ai_response": "That's great...",
  "current_phase": "exploration",
  "progress": 0.3
}
```

**AFTER:**

```json
{
  "conversation_id": "conv_123",
  "ai_response": "That's great...",
  "status": "active",
  "progress": 0.3,
  "is_complete": false
}
```

**Breaking Changes:**

1. **Removed Fields:**
   - `current_phase` - No longer tracked
   - `phase_transition` - Not applicable
   - **Impact:** Any UI showing phase information will break

---

### `GET /api/v1/conversations/{conversation_id}`

**Status:** Modified (Breaking Change)

**Response Changes:**

**BEFORE:**

```json
{
  "conversation_id": "conv_123",
  "topic": "core_values",
  "current_phase": "deepening",
  "template_id": "template_core_values_deepening",
  "messages": [...],
  "progress": 0.6
}
```

**AFTER:**

```json
{
  "conversation_id": "conv_123",
  "topic": "core_values_coaching",
  "topic_type": "coaching",
  "status": "active",
  "messages": [...],
  "progress": 0.6
}
```

**Breaking Changes:**

1. **Topic Format Changed**
   - Old: Category name
   - New: Specific topic ID
   - **Impact:** Any logic comparing topic values will need updates

2. **Removed Fields:**
   - `current_phase`
   - `template_id`
   - **Impact:** UI components displaying these will break

3. **Added Fields:**
   - `topic_type`

---

## Data Model Changes

### Topic Enumeration

**BEFORE:**

```typescript
enum CoachingTopic {
  CORE_VALUES = "core_values",
  PURPOSE = "purpose",
  VISION = "vision",
  GOALS = "goals"
}
```

**AFTER:**

Topic IDs are now **dynamic** and loaded from the backend. Do not hardcode topic IDs.

**Migration Required:**

- Remove hardcoded topic enums
- Fetch available topics from `GET /api/v1/topics/available`
- Store topics in state management (Redux/Zustand/Context)
- Update any switches/conditionals based on topic

---

### Conversation Response Type

**BEFORE:**

```typescript
interface ConversationResponse {
  conversation_id: string;
  topic: CoachingTopic;
  phase: ConversationPhase;
  template_id: string;
  initial_message: string;
  progress: number;
}
```

**AFTER:**

```typescript
interface ConversationResponse {
  conversation_id: string;
  topic: string;  // Now a dynamic string, not enum
  topic_type: string;
  status: string; // "active" | "paused" | "completed"
  initial_message: string;
  progress: number;
}
```

**Breaking Changes:**

- `topic` type changed from enum to `string`
- `phase` field removed
- `template_id` field removed
- `topic_type` field added

---

### Message Response Type

**BEFORE:**

```typescript
interface MessageResponse {
  conversation_id: string;
  ai_response: string;
  current_phase: ConversationPhase;
  progress: number;
  is_complete: boolean;
}
```

**AFTER:**

```typescript
interface MessageResponse {
  conversation_id: string;
  ai_response: string;
  status: string; // "active" | "paused" | "completed"
  progress: number;
  is_complete: boolean;
}
```

**Breaking Changes:**

- `current_phase` field removed

---

## Progress Calculation

**Changed Behavior:**

**BEFORE:**

- Progress calculated based on conversation phase
- Fixed phase progression (introduction → exploration → deepening → synthesis → validation → completion)
- Each phase had a predetermined progress percentage

**AFTER:**

- Progress calculated based on message count and conversation depth
- No fixed phases
- Continuous progress from 0.0 to 1.0
- More granular and dynamic

**Impact:**

- Progress bar behavior may appear different
- No phase labels to show
- Progress is now a continuous flow

---

## Removed Features

### Phase-Based UI

**BEFORE:**

- UI could show current phase (e.g., "Exploration Phase")
- Phase transitions were events
- Different UI treatments per phase

**AFTER:**

- No phase concept
- Continuous conversation flow
- UI should focus on progress percentage only

**Migration Required:**

- Remove phase indicators from UI
- Remove phase-based styling/layouts
- Update progress visualization to be continuous

---

### Template Selection

**BEFORE:**

- Frontend could specify which template to use
- Templates were selected per phase

**AFTER:**

- No template selection
- Topic determines everything
- Backend manages all template logic

**Migration Required:**

- Remove any template selection UI
- Remove template-related API parameters

---

## New Features

### Topic Metadata

**Available Fields:**

- `topic_name`: Display name for UI
- `category`: Grouping (e.g., "core_values")
- `topic_type`: Type of interaction (e.g., "coaching", "assessment")
- `description`: Long description for tooltips/help text
- `display_order`: Suggested sort order

**Frontend Can:**

- Group topics by category
- Filter by topic_type
- Show descriptions in help text
- Sort by display_order

---

### Multiple Topics Per Category

**BEFORE:**

- One interaction per category (e.g., only "core_values" coaching)

**AFTER:**

- Multiple topics per category:
  - "core_values_coaching"
  - "core_values_assessment"
  - "core_values_quick_check"

**Frontend Must:**

- Show all available topics to user
- Let user choose specific interaction type
- Display differentiation clearly

---

## Validation Changes

### Topic Validation

**BEFORE:**

```typescript
// Hardcoded validation
if (!["core_values", "purpose", "vision", "goals"].includes(topic)) {
  throw new Error("Invalid topic");
}
```

**AFTER:**

```typescript
// Dynamic validation
const availableTopics = await fetchAvailableTopics();
if (!availableTopics.some(t => t.topic_id === topic && t.is_active)) {
  throw new Error("Invalid topic");
}
```

**Migration Required:**

- Remove hardcoded topic validation
- Validate against dynamically loaded topics
- Check `is_active` flag

---

## URL/Routing Changes

### Topic in URL

**BEFORE:**

```
/coaching/core_values/start
/coaching/purpose/conversation/123
```

**AFTER:**

```
/coaching/core_values_coaching/start
/coaching/purpose_discovery/conversation/123
```

**Impact:**

- URL patterns changed
- Deep links may break
- Bookmarks may be invalid

**Migration Required:**

- Update route definitions
- Add redirects from old URLs to new format
- Update any hardcoded navigation links

---

## State Management Changes

### Topic State

**BEFORE:**

```typescript
const [selectedTopic, setSelectedTopic] = useState<CoachingTopic>(
  CoachingTopic.CORE_VALUES
);
```

**AFTER:**

```typescript
const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
const [availableTopics, setAvailableTopics] = useState<Topic[]>([]);

useEffect(() => {
  fetchAvailableTopics().then(setAvailableTopics);
}, []);
```

**Breaking Changes:**

- Topic type changed from enum to string
- Need to manage available topics list
- Topic selection requires lookup

---

### Conversation State

**BEFORE:**

```typescript
interface ConversationState {
  id: string;
  topic: CoachingTopic;
  phase: ConversationPhase;
  progress: number;
}
```

**AFTER:**

```typescript
interface ConversationState {
  id: string;
  topic: string;
  topic_type: string;
  status: string; // "active" | "paused" | "completed"
  progress: number;
}
```

**Breaking Changes:**

- Removed `phase` field
- Added `topic_type` field
- `topic` type changed

---

## Testing Impact

### Mock Data

**BEFORE:**

```typescript
const mockConversation = {
  conversation_id: "test_123",
  topic: "core_values",
  phase: "exploration",
  template_id: "template_test"
};
```

**AFTER:**

```typescript
const mockConversation = {
  conversation_id: "test_123",
  topic: "core_values_coaching",
  topic_type: "coaching"
};
```

### Test Cases to Update

1. Topic selection tests
2. Conversation initiation tests
3. Response parsing tests
4. Progress calculation tests
5. URL routing tests
6. State management tests

---

## Migration Checklist

### Required Changes

- [ ] Update `POST /conversations/initiate` request to use new topic IDs
- [ ] Remove phase-related code from conversation responses
- [ ] Remove template_id references
- [ ] Implement `GET /topics/available` endpoint call
- [ ] Update topic selection UI to use dynamic topics
- [ ] Remove hardcoded topic enums
- [ ] Update TypeScript interfaces/types
- [ ] Update URL routing patterns
- [ ] Add redirects for old topic URLs
- [ ] Update state management for topics
- [ ] Remove phase indicators from UI
- [ ] Update progress visualization (remove phase labels)
- [ ] Update tests and mock data
- [ ] Update documentation

### Optional Enhancements

- [ ] Add topic grouping by category
- [ ] Add topic filtering by type
- [ ] Show topic descriptions in UI
- [ ] Implement topic search/filter
- [ ] Add analytics for topic selection

---

## Timeline

**Phase 1: Backend Deployment**

- New endpoints available
- Old endpoints still supported (backward compatible)

**Phase 2: Frontend Migration Window**

- Update frontend to use new endpoints
- Test thoroughly
- Deploy updated frontend

**Phase 3: Deprecation**

- Remove backward compatibility
- Clean up old code

---

## Support

For questions or migration assistance:

- Backend team: Refer to `llm_topic_architecture.md`
- Admin team: Refer to `admin_ai_specifications.md`
- API documentation: [API docs URL]
