"""Tests for IssueRootCauseCoachingResult (GitHub #132)."""

from coaching.src.models.coaching_results import (
    IssueRootCauseActionItem,
    IssueRootCauseCoachingResult,
    get_coaching_result_model,
)


def test_get_coaching_result_model_resolves_issue_root_cause() -> None:
    cls = get_coaching_result_model("IssueRootCauseCoachingResult")
    assert cls is IssueRootCauseCoachingResult


def test_issue_root_cause_coaching_result_round_trip() -> None:
    action = IssueRootCauseActionItem(
        title="Clarify onboarding handoff",
        description="Document the exact step where new customers stall and assign an owner.",
        due_date="2026-05-01",
        assignee="Head of Customer Success",
        priority="High",
        alignment_note="Supports purpose of customer-first delivery and current Q2 retention goal.",
    )
    result = IssueRootCauseCoachingResult(
        issue_one_sentence="Customers churn in the first 30 days after signup.",
        desired_outcome="Reduce early churn by clarifying ownership of the first success milestone.",
        relevant_business_context="Purpose: serve customers with clarity. Open issues include billing delays.",
        technique_selected="Five Whys",
        technique_rationale="Symptoms point to a linear handoff failure in onboarding.",
        symptoms="Users stop engaging after welcome email.",
        contributing_factors="No single owner for first-week check-ins.",
        root_cause="Unclear accountability between Sales and CS after handoff.",
        evidence_and_reasoning="Pattern repeats across five accounts; handoff doc is outdated.",
        hypothesis_notes="Validate with two customer interviews.",
        energy_pattern_current="Frustration and blame between teams.",
        energy_shift_needed="Move to shared facts and explicit ownership.",
        recommended_actions=[action],
        related_issues_to_track=["Improve invoice delivery reliability"],
        risks_and_watchouts="Competing priorities in CS may delay the due date.",
        next_coaching_question="What is the smallest experiment you can run in two weeks to test the new handoff?",
    )
    dumped = result.model_dump()
    parsed = IssueRootCauseCoachingResult.model_validate(dumped)
    assert parsed.recommended_actions[0].title == action.title
    assert parsed.recommended_actions[0].priority == "High"


def test_issue_root_cause_prompt_asset_loads() -> None:
    from coaching.src.core.prompt_static.issue_root_cause_coaching_system import (
        load_issue_root_cause_coaching_system_prompt,
    )

    text = load_issue_root_cause_coaching_system_prompt()
    assert "context-aware leadership coaching agent" in text
    assert "Final output format" in text
