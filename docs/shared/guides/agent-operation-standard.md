# Agent Operation Standard

## Objective

Define how AI coding agents and automation operate in this repository.

## Core Principles

- Agents follow repository standards and issue scope.
- Agents prioritize safe, reversible, testable changes.
- Agents should not bypass governance gates.

## Required Behavior

- Use issue context before implementing changes.
- Keep pull requests scoped and reviewable.
- Provide validation evidence (build/tests) in issue or PR notes.
- Escalate ambiguities instead of guessing on business-critical behavior.

## Documentation Behavior

- Treat canonical standards as the first reference set.
- Keep `.github/copilot-instructions.md` as an index, not a policy dump.
- Add migration notes when moving guidance from old docs into canonical standards.

## Cross References

- Copilot instruction index: `.github/copilot-instructions.md`
- Canonical standards map: `docs/local/solution-overview.md`
- Migration notes: `docs/migration/documentation-standards-migration-2026-03-10.md`
