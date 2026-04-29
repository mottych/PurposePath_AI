# cleanup prompt for PurposePath AI Coaching Service

Before making changes:
- Read .issueflow/repo.yaml for commands, app root, deployment workflows, and ownership domains.
- Inspect the issue context and gather concrete evidence from code, tests, docs, or workflow logs before deciding scope.
- Use existing project commands rather than inventing new tooling.

Repository facts:
- Repository: mottych/PurposePath_AI
- App root: $(System.Collections.Hashtable.AppRoot)
- Primary language/platform: python
- Install command: $(System.Collections.Hashtable.Install)
- Validation command: $(System.Collections.Hashtable.Validate)
- Test command: $(System.Collections.Hashtable.Test)
- Build command: $(System.Collections.Hashtable.Build)
- Dev deployment workflow: $(System.Collections.Hashtable.DevWorkflow)
- Staging deployment workflow: $(System.Collections.Hashtable.StagingWorkflow)
- Preprod deployment workflow: $(System.Collections.Hashtable.PreprodWorkflow)
- Production deployment workflow: $(System.Collections.Hashtable.ProdWorkflow)

Role guidance:
- Triage/planning roles should identify the responsible files and cite evidence before recommending implementation.
- Implementation roles should keep changes scoped and run the smallest relevant validation first, then broader validation when risk requires it.
- Validation/QA roles should verify behavior with existing tests, build commands, and any relevant deployment or smoke-test workflows.
- Deployment roles should use the workflow names in .issueflow/repo.yaml and collect workflow evidence instead of running ad hoc deployment commands.
- Cleanup roles should remove temporary artifacts and summarize final evidence without changing unrelated code.
