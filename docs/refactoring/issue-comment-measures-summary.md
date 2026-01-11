## 🔧 Amendment: GET /measures/summary Endpoint

I missed a critical optimization endpoint from the measures-api.md spec:

### GET /measures/summary

This single endpoint provides **comprehensive measure data** including:

**Per Measure:**
- Full measure details (name, description, unit, direction, type, category)
- Current value and date
- Latest target and actual values
- Progress calculation (percentage, status, variance, days until target)
- Owner information
- Goal links with progress per link
- Strategy links with progress per link
- Measurement configuration
- Sharing info
- Trend data (historical values)

**Summary Statistics:**
- Total measures (active/inactive)
- Status breakdown (on_track, at_risk, behind, no_data)
- Category breakdown with counts per status
- Owner breakdown with counts
- Overall health score

### Impact on Implementation

**Instead of:**
- GET /measures (list)
- Multiple GET /measures/{id} calls
- Separate progress calculations

**Use:**
- Single GET /measures/summary call

### New Parameters from this endpoint:

| Parameter | Type | Description |
|-----------|------|-------------|
| `measures_summary_data` | object | Complete summary response |
| `measures_health_score` | number | Overall health score (0-100) |
| `measures_status_breakdown` | object | Count by status |
| `measures_category_breakdown` | array | Count by category |
| `measures_owner_breakdown` | array | Count by owner |
| `measures_with_progress` | array | All measures with progress details |
| `at_risk_measures` | array | Measures with status "at_risk" |
| `behind_measures` | array | Measures with status "behind" |
| `on_track_measures` | array | Measures with status "on_track" |

### Updated Retrieval Method

```python
@register_retrieval_method(
    name="get_measures_summary",
    description="Retrieves comprehensive measure summary with progress, links, and statistics",
    provides_params=(
        "measures",
        "measures_count",
        "measures_summary",
        "measures_health_score",
        "measures_status_breakdown",
        "measures_category_breakdown",
        "measures_by_status",
        "at_risk_measures",
        "behind_measures",
        "on_track_measures",
        "measures_for_goal",
        "measures_for_strategy",
    ),
)
async def get_measures_summary(context: RetrievalContext) -> dict[str, Any]:
    data = await context.client.get_measures_summary(context.tenant_id)
    # Single call provides everything!
```

**Reference:** docs/shared/Specifications/user-app/traction-service/measures-api.md (lines 33-358)
