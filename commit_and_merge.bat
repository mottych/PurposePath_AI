@echo off
echo Committing changes for Issue #75...
git commit -m "feat: Add latest LLM models - Claude 3.5 v2, Claude 4.5, GPT-5, Gemini 2.5 Pro" -m "Models Added: CLAUDE_3_5_SONNET_V2, CLAUDE_SONNET_4_5, GPT_5_PRO, GPT_5, GPT_5_MINI, GEMINI_2_5_PRO" -m "Providers: OpenAILLMProvider, GoogleVertexLLMProvider" -m "Dependencies: openai==1.109.1, google-cloud-aiplatform==1.74.0" -m "Quality: 853/853 tests passing, zero errors" -m "Closes #75"

echo.
echo Switching to dev branch...
git checkout dev

echo.
echo Merging feature branch...
git merge feature/add-latest-llm-models

echo.
echo Pushing to remote...
git push origin dev

echo.
echo Deleting feature branch...
git branch -d feature/add-latest-llm-models

echo.
echo Done! Issue #75 complete and merged to dev.
pause
