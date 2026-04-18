# Squad Official Issue Operation

## Purpose

Define the supported way for PurposePath to hand GitHub issues to Squad while keeping routing customization in official Squad team-state.

## Source of Truth

1. `squad.config.ts` is the authored routing source of truth.
2. `squad build` generates `.squad/team.md`, `.squad/routing.md`, and related Squad artifacts.
3. Upgrade-managed `.github/workflows/squad-*.yml` files are adapters and must not carry PurposePath-specific routing logic.

## Recommended Operating Model

Use Squad issue-driven development instead of depending on the base `squad` label as the primary entry point.

### Start a Squad Session

1. `Connect to mottych/PurposePath_Api`
2. `Show backlog`
3. `Work on #N`

### Expected Workflow

1. Bug or defect-oriented issues route to Joseph for evidence and root-cause analysis.
2. Feature or intent-oriented issues route to Deborah for intent and outcome alignment.
3. Planning, design, and change-request loops route to Bezalel.
4. Human Gate 1 approval is expressed with `go:design-approved` or an explicit approval instruction in the Squad session.
5. After approval, implementation routes to Joshua.

### Recommended Approval Prompts

1. `Bezalel, create the Gate 1 plan for #N`
2. `The plan for #N is approved`
3. `Joshua, implement #N`

## Issue Design Requirements

### Bug Issues

1. Use labels `bug` and `type:bug`.
2. Include reproduction steps.
3. Include expected behavior and actual behavior.

### Feature Issues

1. Use labels `enhancement` and `type:feature`.
2. Include the problem to solve.
3. Include the desired outcome.
4. Include the value hypothesis.
5. Include explicit acceptance criteria.

## Optional Unattended Mode

For backlog polling without custom workflow routing, use the supported Squad runtime path:

`npx @bradygaster/squad-cli watch --interval 10`

This keeps routing decisions in Squad runtime and generated team-state instead of repository-owned workflow customization.
