#!/usr/bin/env python3
"""Fix N815 errors in operations.py by adding Pydantic aliases."""

import re
from pathlib import Path

def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    # Insert underscore before uppercase letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def fix_operations_file():
    """Fix all N815 errors in operations.py."""
    file_path = Path("coaching/src/api/models/operations.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Camel case field names that need fixing
    camel_fields = [
        'businessVision', 'businessFoundation', 'strategicGoal', 'relatedGoals',
        'goalDescription', 'currentActions', 'businessContext', 'businessImpact',
        'businessMetrics', 'timeHorizon', 'dependentActions', 'actionType',
        'actionStatus', 'targetDate', 'currentResources', 'requiredResources',
        'teamMember', 'actionDescription', 'goalAlignment', 'foundationAlignment',
        'relatedStrategies', 'keyMetrics', 'resourceRequirements', 'nextSteps',
        'estimatedImpact', 'businessArea', 'currentCapacity', 'capacityConstraints',
        'teamConstraints', 'budgetConstraints', 'timelineConstraints',
        'dependencyConstraints', 'businessValue', 'implementationEffort',
        'strategicAlignment', 'urgencyScore', 'riskLevel', 'resourceAvailability',
        'dependencyComplexity', 'plannedStart', 'plannedEnd', 'estimatedDuration',
        'teamSize', 'criticalPath', 'resourceAllocation', 'alternativeTimelines',
        'resourceConsiderations', 'alternativeSchedules', 'reportedBy',
        'dateReported', 'relatedActions', 'affectedAreas', 'issueTitle',
        'issueDescription', 'rootCause', 'availableResources', 'businessPriorities',
        'estimatedCost', 'assignmentSuggestion', 'expectedOutcome'
    ]
    
    for camel in camel_fields:
        snake = to_snake_case(camel)
        # Pattern 1: field_name: Type = Field(..., -> field_name: Type = Field(..., alias="camelCase",
        pattern1 = rf'(\s+){camel}(:\s+[^=]+\s*=\s*Field\()(\.\.\.)'
        replacement1 = rf'\1{snake}\2\3, alias="{camel}"'
        content = re.sub(pattern1, replacement1, content)
        
        # Pattern 2: field_name: Type = Field(None, -> field_name: Type = Field(None, alias="camelCase",
        pattern2 = rf'(\s+){camel}(:\s+[^=]+\s*=\s*Field\()(None)'
        replacement2 = rf'\1{snake}\2\3, alias="{camel}"'
        content = re.sub(pattern2, replacement2, content)
        
        # Pattern 3: field_name: Type = Field(default_factory= -> field_name: Type = Field(alias="camelCase", default_factory=
        pattern3 = rf'(\s+){camel}(:\s+[^=]+\s*=\s*Field\()(default_factory=)'
        replacement3 = rf'\1{snake}\2alias="{camel}", \3'
        content = re.sub(pattern3, replacement3, content)
    
    # Add ConfigDict to models that have camelCase fields
    models_needing_config = [
        'ActionInput', 'GoalInput', 'BusinessFoundationInput', 'StrategicAlignmentRequest',
        'StrategicConnection', 'ActionAlignmentAnalysis', 'PrioritizationActionInput',
        'BusinessContext', 'PrioritizationRequest', 'PrioritizationSuggestion',
        'SchedulingActionInput', 'CriticalDeadline', 'TeamAvailability',
        'SchedulingConstraints', 'SchedulingRequest', 'AlternativeSchedule',
        'SchedulingSuggestion', 'IssueContext', 'RootCauseRequest',
        'RootCauseMethodSuggestion', 'ActionIssue', 'ActionConstraints',
        'ActionPlanContext', 'ActionPlanRequest', 'ActionSuggestion'
    ]
    
    for model in models_needing_config:
        # Add model_config right after class definition and docstring
        pattern = rf'(class {model}\(BaseModel\):)\n(\s+"""[^"]*""")\n'
        replacement = rf'\1\n\2\n\n    model_config = ConfigDict(populate_by_name=True)\n'
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed N815 errors in {file_path}")

if __name__ == "__main__":
    fix_operations_file()
