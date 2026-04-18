# IssueFlow Requirements

**Status:** Draft
**Owner:** Engineering Productivity
**Version:** 0.1.0
**Last Updated:** 2026-04-17

## 1. Purpose

IssueFlow is a code-first, persistent orchestration system for multi-repository software delivery. It coordinates issue-driven work across repositories, people, agents, and deterministic automations while enforcing explicit workflow states, gates, scheduling, prioritization, and recovery.

This document defines product and behavior requirements only. It intentionally excludes implementation design, technology choices, deployment architecture, and storage design.

## 2. Goals

1. Orchestrate issue-driven work across multiple repositories that use different technologies.
2. Support autonomous progression between explicitly defined human gates.
3. Preserve a complete, auditable history of work state transitions and agent outputs.
4. Support repo-aware workflows after initial triage while maintaining a shared orchestration model.
5. Allow issue rerouting, cross-repo splitting, and dependency tracking as first-class behavior.
6. Support multiple execution modes, including agentic analysis, coding agents, human decisions, and deterministic automation.
7. Support repo-specific rules, prompts, and validator chains.
8. Support prioritization, scheduling, capacity control, failure handling, and operator recovery.
9. Learn from human approvals, corrections, and directives without silently mutating live policy.

## 3. Non-Goals

1. Define storage schema, cloud architecture, queue design, or hosting model.
2. Define implementation details for GitHub, AWS, Pulumi, or any specific vendor integration.
3. Replace repository-specific architecture and coding standards.
4. Require all repositories to share identical downstream workflows.
5. Require all states to expose different machine contracts beyond the canonical state model.

## 4. Operating Context

1. The full solution spans multiple repositories.
2. Repositories use different technologies, including React, Python, and .NET.
3. Each repository maintains its own issue list.
4. Issues reported in one repository may actually belong to another repository.
5. A single business problem may require coordinated work in multiple repositories.
6. Some work items are infrastructure related or technology-upgrade related rather than feature-repository specific.

## 5. Core Concepts

### 5.1 Work Item

A work item is the orchestrated unit of work. A work item may correspond to:
1. An issue in a repository.
2. A child issue created in another repository.
3. A non-issue internal orchestration item when required for future coordination models.

### 5.2 State

A state is a unit of work to be performed. Examples include:
1. `initial_triage`
2. `bug_triage`
3. `intent_requirements`
4. `design_plan`
5. `human_design_approval`
6. `implementation_prep`
7. `implementation`
8. `code_review`
9. `security_review`
10. `qa_deploy`
11. `e2e_test`
12. `human_qa_validation`
13. `prod_deploy`
14. `cleanup`

Repo-specific examples include:
1. `cost_review`
2. `data_model_review`
3. `intent_validation`
4. `ui_ux_review`

A state represents the work to be done, not how that work is executed.

### 5.3 Stage

Stage represents the execution progress of a state.

Allowed values:
1. `ready`
2. `pending`
3. `in_progress`
4. `done`

A failed or blocked state may still be `done` if the state reached a terminal execution result.

`pending` must be supported for work that is valid but not yet actively executing because it is waiting for capacity, a resume signal, or another orchestration condition.

### 5.4 Status

Status represents whether the state execution completed correctly from an orchestration perspective.

Allowed values must support at least:
1. `pass`
2. `fail`
3. `blocked`
4. `cancelled`
5. `aborted`
6. `timed_out`

IssueFlow must orchestrate based on state, stage, status, and repo context.

### 5.5 Execution Type

Execution type defines how a state is performed.

Required execution types:
1. `llm_analysis`
2. `coding_agent`
3. `human_gate`
4. `automation_execution`
5. `wait_for_signal`
6. `aggregation`
7. `routing_decision`
8. `policy_resolution`
9. `operator_override`
10. `artifact_processing`

Execution type determines what configuration a state must provide, such as prompt definition, deterministic workflow reference, or required human actor.

### 5.6 Output

Each state produces output information for traceability and downstream use.

Output must be available in human-readable form and may also include a shared machine-readable envelope for clarity. IssueFlow must not require per-state bespoke output contracts for orchestration.

### 5.7 Repo Context

Each work item must carry repo context that includes at least:
1. Source repository.
2. Owning repository.
3. Solution context.
4. Work classification.
5. Relevant repo-specific rules and validation profile.

## 6. Global Workflow Rules

1. A workflow is authored by defining states first.
2. Each state must define its allowed stage progression.
3. Each state must define its allowed status values.
4. Each state must define its execution type.
5. Each state must define the configuration required by that execution type.
6. Each state must publish human-readable output accessible to later states.
7. IssueFlow orchestration decisions must be based on state, stage, status, and repo context.
8. Business interpretation of state-specific output belongs primarily to the state handler, not the orchestrator.
9. The orchestrator must still persist references to outputs, comments, created issues, created PRs, and other linked artifacts for auditability.
10. The orchestrator must distinguish between a state that is complete and should transition to a new state and a state that is paused and should later resume the same handler.
11. A state may temporarily pause for clarification or intervention without changing to a different business state.
12. When a paused state resumes, it must route back to the same state handler unless the workflow definition explicitly says otherwise.
13. IssueFlow must prioritize workflow orchestration and code quality without adding unnecessary orchestration restrictions.
14. State handlers may perform the workflow side effects needed to complete their unit of work.

## 7. State Execution Requirements

### 7.1 LLM Analysis States

1. Read-only analysis states must be supported.
2. These states may inspect code, docs, issues, logs, specifications, Pulumi state, deployment state, AWS logs, internet resources, and other contextual inputs.
3. These states must not directly modify code or external systems unless explicitly defined as a different execution type.
4. These states must publish a comment or artifact with findings, rationale, and recommendations.

Examples:
1. `initial_triage`
2. `bug_triage`
3. `intent_requirements`
4. `architecture_review`
5. `validation_review`

### 7.2 Coding Agent States

1. Coding agent states must support code modification and repository work.
2. These states may access all relevant resources needed to do their job, including code, issues, specs, logs, Pulumi state, AWS, and internet resources.
3. These states must publish a comment or artifact summarizing work completed, constraints, and evidence.
4. These states may create commits, branches, and PRs when allowed by the workflow definition.

Examples:
1. `implementation`
2. `test_creation`
3. `refactor`

### 7.3 Human Gate States

1. Human gate states must require explicit human response.
2. A human response must include an outcome and may include a required comment.
3. Human comments may include corrective instructions even when the gate status passes.
4. Human directives such as "never do this", "from now on", or "always do this" must be capturable as learning inputs.
5. Human gate states are standalone units of work with defined next-state behavior after completion.
6. Human gate states are different from a paused agent state that is waiting to resume the same work.

Examples:
1. `human_design_approval`
2. `human_deploy_approval`
3. `human_block_resolution`
4. `human_qa_validation`

### 7.3.1 Human Clarification and Same-State Resume

1. IssueFlow must support agentic states pausing to request human clarification or intervention.
2. These pauses must not require converting the work into a different business state when the intent is to resume the same state handler.
3. Example cases include prompts that require consultation before proceeding with:
   1. DB changes,
   2. API contract changes,
   3. infrastructure changes,
   4. other workflow-defined conditions.
4. After the required human response is received, the orchestrator must resume the same paused state handler.
5. The orchestrator must know which handler asked the question so it can resume the same handler assignment or equivalent handler type.
6. Multiple clarification rounds must be supported within the same state before that state reaches `done`.
7. Clarification pauses must be auditable and distinguishable from formal human gate states.

### 7.4 Automation Execution States

1. Deterministic automation states must be supported.
2. These states may run workflows, scripts, test jobs, deployment jobs, merge operations, or similar deterministic processes.
3. These states are not required to leave comments, although they may emit artifacts or references.
4. Their completion must still update the canonical state record.

Examples:
1. `qa_deploy`
2. `run_e2e`
3. `merge_pr`
4. `collect_logs`

### 7.5 Validators as Independent States

1. Validators must be modeled as separate states, not as one aggregated validation blob.
2. Each validator state may have its own prompt, artifacts, and status.
3. Different repositories may use different validator states and validator ordering.
4. Validators are LLM-based in v1.
5. Deterministic tooling may later be added as supporting evidence for validators, but validator orchestration must not depend on that in v1.
6. For v1, validator failures route back to `implementation`.
7. Validators may decide not to perform a substantive review when implementation reports that no code was changed, but that decision belongs to the validator state rather than the orchestrator.
8. Any validator may skip based on its own prompt, findings, or available context; validator skipping is not an orchestration concern in v1.
9. In v1, all configured validator states execute in workflow order, and each validator independently decides whether to perform a substantive review or skip.

Examples:
1. `code_review`
2. `security_review`
3. `cost_review`
4. `data_model_review`
5. `intent_validation`
6. `ui_ux_review`

## 8. Initial Triage Requirements

1. `initial_triage` is the shared entry state for all repos.
2. `initial_triage` must actively execute the routing decision.
3. If the issue belongs to the current repo, triage keeps the issue in that repo and transitions it into that repo's workflow profile.
4. If the issue belongs to a different repo, triage must:
   1. create the replacement issue in the owning repo,
   2. publish trace information,
   3. link the old and new issues,
   4. close the original issue as cancelled or equivalent terminal disposition.
5. If the issue spans multiple repos, triage must:
   1. create the necessary linked issues in the additional repos,
   2. record dependency and trace links,
   3. keep all downstream issues valid for the repos they belong to.
6. In v1, triage does not create a canonical parent coordination object.
7. After triage, downstream repo-owned work items must use the rules and workflow of their owning repo.

## 9. Repo-Aware Workflow Requirements

1. IssueFlow must support a shared initial triage model and repo-specific downstream workflow profiles.
2. IssueFlow must not require all repositories to use the same downstream states after triage.
3. The shared state catalog applies to `PurposePath_Api`, `PurposePath_Web`, `PurposePath_AI`, and `PurposePath_Admin` unless a state is explicitly identified as repo specific.
4. Repo-specific workflows may differ in:
   1. state catalog,
   2. prompts,
   3. validator states,
   4. automation states,
   5. required artifacts,
   6. review chains.
5. Example distinction:
   1. all repos share the same core pre-implementation states,
   2. API adds states such as `cost_review` and `data_model_review`,
   3. Web adds states such as `intent_validation` and `ui_ux_review`,
   4. AI and Admin currently use only the shared state catalog unless additional repo-specific validators are introduced later.
6. The orchestrator must load the correct repo-specific workflow profile after triage.
7. A core principle of IssueFlow is that the engine remains generic and extensible rather than tightly coupled to the current repositories or validator catalogs.

## 10. Cross-Repo Coordination Requirements

1. A single business problem may yield multiple repo-owned issues.
2. In v1, those issues are independent after creation.
3. If an issue is rerouted to another repo, the original issue must be closed with a comment and link to the new issue.
4. If work is split across repos, the resulting issues must be linked through comments or trace references.
5. In v1, dependencies between repo-owned issues are informational and are communicated through comments or trace references rather than a canonical dependency object.
6. The implementation agent may inspect those dependency comments and pause for clarification if needed.
7. Epic-style parent-child delivery and solution-level coordination objects are out of scope for v1 and may be introduced later.

## 11. Output and Traceability Requirements

1. Agentic states should publish human-readable comments or artifacts for downstream consumption.
2. These outputs should be accessible to later states as context.
3. A shared machine-readable envelope may be included for clarity.
4. Routing and orchestration must not depend exclusively on comment parsing.
5. Structured state completion must be recorded by the handler directly to the orchestration system.
6. The system must preserve links to comments, artifacts, created issues, PRs, and other important side effects.
7. Human-readable comments may be used as context for downstream states, but comments alone must not be treated as sufficient evidence that a human task is complete.
8. The workflow must support an explicit completion trigger for human tasks and clarification pauses, such as:
   1. a label,
   2. a specific phrase or command,
   3. another approved structured signal.
9. The workflow definition must declare which trigger or trigger set completes a given human gate or clarification pause.
10. Automatically generated comments from unrelated systems must not by themselves complete a human task or resume a paused state.
11. The v1 continuation trigger for human responses must support the phrase `{{cont}}` in a comment.
12. Human response outcomes must support at least:
   1. `pass`,
   2. `fail`,
   3. `redesign`,
   4. `abort`.
13. `pass` continues to the default next step.
14. `fail` continues on the failure route for the current workflow.
15. `redesign` routes the work back to `design_plan`.
16. `abort` cancels the whole execution.
17. In v1, `{{cont}}` in a human comment indicates that the handover or clarification step is complete and the current state can move to `done`.
18. In v1, labels provide the human response status for that completed handover or gate.
19. In v1, the only labels explicitly defined as routing or workflow-branching inputs are:
   1. `hotfix`,
   2. human-response status labels.
20. Additional routing labels may be introduced in the future, but they are not required for v1.

## 12. Resource Access Requirements

1. Agentic states may require broad access to available resources.
2. The system must support agentic states having access to:
   1. GitHub code and documents,
   2. GitHub issues and pull requests,
   3. AWS logs and deployment state,
   4. Pulumi state,
   5. Internet search or fetch capabilities,
   6. AWS CLI or equivalent access.
3. The system should not restrict workflow authoring by forcing narrow capability bundles for agentic states.
4. Resource availability must be sufficient for prompts to instruct agents to gather the information they need.

## 13. Repo-Specific Rules and Validation Profiles

1. Rules and guidelines must be repo specific.
2. Architecture and coding rules may differ by technology.
3. Prompting for coding and review states must support repo-specific guidance.
4. Validation chains may differ by repo and by technology.
5. The owning repo determines the effective policy and validation profile after triage.
6. Current policy sources live in each repository's own workflow documentation.
7. Branch naming and environment branch sources are repo-specific policy and must be supported.
8. The exact structured implementation comment format is a design concern and does not need to be finalized in the requirements phase beyond requiring structured comments.

### 13.1 Branching and Environment Route Policy

1. All repos use `dev` as the source branch for non-hotfix issues and the branch deployed to the dev environment.
2. All repos use feature branches following the pattern `issueFlow {issue number} - {issue short desc}`.
3. API uses:
   1. `preview` for staging,
   2. `main` for production,
   3. `main` as the source for hotfix branches.
4. Web, AI, and Admin use:
   1. `staging` for staging,
   2. `master` for production,
   3. `master` as the source for hotfix branches.
5. All repos use hotfix branches deployed to preprod before production release.

## 14. Scheduling, Prioritization, and Capacity

1. IssueFlow must support scheduling of ready work items.
2. It must support prioritization across work items.
3. It must support capacity limits for states, repos, or handlers.
4. It must support waiting and pending states without losing context.
5. It must support blocked states and later resumption.
6. These behaviors must be configurable independently from state business logic.
7. Priority order for v1 is:
   1. `hotfix` issues first,
   2. then priority label,
   3. then bugs before enhancements.
8. Priority labels affect prioritization but do not directly affect routing.
9. An active issue is any issue that is not blocked, including issues pending on human response.
10. V1 capacity limits are:
   1. maximum 5 active non-blocked issues in the flow,
   2. maximum 3 concurrent issues in `implementation`.
11. Other states do not have separate capacity limits in v1.

## 15. Stall Detection and Heartbeat Requirements

1. IssueFlow must support stall detection and heartbeat monitoring.
2. The system must be able to detect states that are stuck in `pending` or `in_progress` beyond configured expectations.
3. Stall detection must support at least:
   1. handlers that stopped reporting progress,
   2. paused work that exceeded expected wait time,
   3. work that appears stranded due to missing progress signals.
4. Formal human gate waits and explicit clarification waits must not be treated as failures solely because they are waiting.
5. Stall detection outcomes must support at least:
   1. informational alert,
   2. escalation,
   3. retry or restart path,
   4. blocked or operator-attention path.
6. The default stall timeout for v1 is 30 minutes for all states except:
   1. formal human gates,
   2. states in `pending` while waiting for human response.

## 16. Recovery and Resilience

1. IssueFlow must tolerate retries, restarts, and reprocessing without losing workflow state.
2. It must support explicit blocked, aborted, cancelled, and timed-out terminal statuses.
3. It must support resuming work after a human action, signal, or recovery path.
4. It must preserve traceability for failed and retried states.
5. It must support resuming the same paused state handler after a valid human clarification response.

## 17. Learning Requirements

1. Learning is primarily driven by human approvals, rejections, and directives.
2. The system must capture human statements such as:
   1. "never do this",
   2. "from now on",
   3. "we should always",
   4. similar durable guidance.
3. The system may also learn from recurring approval failures, repeated validator findings, and recurring reroute patterns.
4. Learning must not silently mutate live workflow or repo policies.
5. Learning outputs must be reviewable and applied intentionally.

## 18. Minimum Required State Model

The minimum canonical model for orchestration is:
1. `state`
2. `stage`
3. `status`
4. `execution_type`
5. `owning_repo`
6. routing labels or triggers when relevant to the active workflow step

The system may persist additional trace references, comments, artifacts, linked issues, and PRs, but orchestration correctness must rely on the canonical state model rather than state-specific bespoke contracts.

## 19. Initial Product Scope

IssueFlow v1 must support at least:
1. shared initial triage,
2. repo-aware downstream workflows,
3. active reroute and split execution in triage,
4. agentic and deterministic states,
5. human gate states,
6. validators as independent states,
7. cross-repo linked issue creation,
8. scheduling, prioritization, capacity, and recovery,
9. repo-specific rules and validation profiles,
10. comment and artifact traceability,
11. pending stage support,
12. heartbeat and stall detection,
13. explicit human completion triggers,
14. same-state resume after clarification pauses,
15. hotfix versus non-hotfix deployment branching,
16. repo-specific branch source policy.

## 20. Phase 2 Epic Delivery Model

1. Phase 2 may introduce an epic-based delivery model.
2. In that model, one issue acts as the epic holding the business outcome and overall requirement.
3. Implementation-specific work is represented by separate child issues linked back to the epic.
4. Child issues hold the detailed design and implementation specifics for each step.
5. The epic holds the intended sequence of execution of child issues.
6. Implementation proceeds one child issue at a time while remaining on a single branch for the duration of the epic.
7. When a child issue is completed, implementation must:
   1. write a completion comment in the child issue,
   2. close the child issue,
   3. update progress in the epic.
8. Validator states run for each child issue.
9. QA deployment to the QA environment does not occur per child issue.
10. After all child issues are completed, the workflow continues with:
   1. QA deployment,
   2. E2E tests,
   3. human QA validation,
   4. the normal post-QA route.
11. If E2E fails after epic completion, corrective work occurs at the epic level.

## 21. Requirements Status

The v1 requirements baseline is sufficiently defined to begin design.

Future extensions remain possible, including:
1. additional repo-specific validators for AI or Admin,
2. additional routing or workflow-branching labels,
3. epic-style parent-child delivery and solution-level coordination,
4. richer validator applicability policy,
5. broader repo-specific workflow divergence.
