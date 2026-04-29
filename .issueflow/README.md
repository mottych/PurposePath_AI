# IssueFlow Repository Configuration

This folder contains repo-local IssueFlow configuration for PurposePath AI Coaching Service.

Key files:
- epo.yaml describes the repo, app root, existing validation commands, ownership domains, and deployment workflows.
- gents/team.yaml maps IssueFlow role names to OpenCode agents.
- gents/<role>/agent.yaml, charter.md, prompt.md, and permissions.yaml provide role-specific context for local worker execution.
- lessons/approved/ is reserved for reviewed repo-local lessons that can be promoted into IssueFlow context.

Agents should use the commands in epo.yaml and the repository's existing docs/scripts. Deployment should use the existing GitHub Actions workflows listed in epo.yaml.
