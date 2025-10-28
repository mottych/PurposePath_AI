#!/usr/bin/env python3
"""Fix N815 errors in operations.py using proper Pydantic Field syntax."""

import re
from pathlib import Path

def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def fix_file():
    """Fix operations.py with proper Field syntax."""
    file_path = Path("coaching/src/api/models/operations.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Field mappings: camelCase -> snake_case - ALL fields
    field_map = {
        'reportedBy': 'reported_by',
        'dateReported': 'date_reported',
        'relatedActions': 'related_actions',
        'affectedAreas': 'affected_areas',
        'issueTitle': 'issue_title',
        'issueDescription': 'issue_description',
        'businessImpact': 'business_impact',
        'rootCause': 'root_cause',
        'availableResources': 'available_resources',
        'relatedGoals': 'related_goals',
        'currentActions': 'current_actions',
        'businessPriorities': 'business_priorities',
        'estimatedDuration': 'estimated_duration',
        'estimatedCost': 'estimated_cost',
        'assignmentSuggestion': 'assignment_suggestion',
        'expectedOutcome': 'expected_outcome',
        'alternativeSchedules': 'alternative_schedules',
        'resourceConsiderations': 'resource_considerations',
        'urgencyFactors': 'urgency_factors',
        'impactFactors': 'impact_factors',
        'recommendedAction': 'recommended_action',
        'estimatedBusinessValue': 'estimated_business_value',
        'assignedTo': 'assigned_to',
        'currentStartDate': 'current_start_date',
        'currentDueDate': 'current_due_date',
        'personId': 'person_id',
        'hoursPerWeek': 'hours_per_week',
        'unavailableDates': 'unavailable_dates',
        'teamCapacity': 'team_capacity',
        'criticalDeadlines': 'critical_deadlines',
        'teamAvailability': 'team_availability',
        'startDate': 'start_date',
        'dueDate': 'due_date',
        'actionId': 'action_id',
        'suggestedStartDate': 'suggested_start_date',
        'suggestedDueDate': 'suggested_due_date',
    }
    
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        modified = False
        
        for camel, snake in field_map.items():
            # Pattern: fieldName: Type = Field(
            if f'{camel}:' in line and '= Field(' in line:
                # Replace field name
                line = line.replace(f'{camel}:', f'{snake}:')
                
                # Add alias after the first parameter
                if 'Field(...' in line:
                    line = line.replace('Field(...', f'Field(..., alias="{camel}"')
                elif 'Field(None' in line:
                    line = line.replace('Field(None', f'Field(None, alias="{camel}"')
                elif 'Field(default_factory=' in line:
                    line = line.replace('Field(default_factory=', f'Field(alias="{camel}", default_factory=')
                    
                modified = True
                break
        
        new_lines.append(line)
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("Fixed operations.py")

if __name__ == "__main__":
    fix_file()
