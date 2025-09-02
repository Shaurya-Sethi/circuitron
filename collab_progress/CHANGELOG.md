# Circuitron Changelog (collab_progress index)

## Purpose
- This file is the single, ordered index of all progress notes under collab_progress.
- It makes recent changes easy to find and links each entry to the detailed Markdown note(s).

## Rules
- Always append a new entry at the TOP after every task/change (feature, fix, refactor, tests, docs).
- Include Date and Time (prefer ISO 8601, UTC). Example: 2025-08-08T14:32Z
	To get the current time and date in the correct format, run this in PowerShell:
  
			Get-Date -Format o

- Keep the Summary concise; link to detailed files for depth.
- Reference the branch/PR when applicable.
- Do not remove or rewrite past entries; corrections should be a new entry.

Entry Template
- Copy/paste and fill all fields. Keep newest entries at the top.

```
## [Title]: Short description of the change
- Date: YYYY-MM-DD
- Time (UTC): HH:MMZ
- Branch/PR: <branch-name> (<PR link> if available)
- Files Changed (high level): <modules or folders>
- Details: See <relative-links-to-detailed-notes.md>
- Verification: <tests run, tools, results>
- Notes: <optional follow-ups/known issues>
```

### Fix: Guard CLI/UI when MCP server isn’t running
- Date: 2025-09-02
- Time (UTC): 18:30Z
- Branch/PR: main
- Files Changed (high level): network (new MCP checks), cli, pipeline, ui/app, tests
- Details: See collab_progress/mcp-startup-checks-09-02-2025.md
- Verification: Added tests for MCP checks (tests/test_mcp_server_checks.py). Please run `pytest -q` in the project venv.

### Experimental: Setup command and agent for KB initialization
- Date: 2025-09-02
- Time (UTC): 18:00Z
- Branch/PR: main
- Files Changed (high level): models, prompts, setup_agent, setup runner, cli, pipeline (args), ui (app, input_box), tests, docs
- Details: See collab_progress/setup-command-implementation-09-02-2025.md
- Verification: Added unit tests for models/agent/CLI/UI. Please run `pytest -q` in the project venv.
- Notes: Marked experimental; interfaces and behavior may change. One-time, idempotent initialization using MCP tools (`smart_crawl_url`, `parse_github_repository`).

### Docs: SKiDL KB refresh guidance
- Date: 2025-09-01
- Time (UTC): 17:55Z
- Branch/PR: main
- Files Changed (high level): docs
- Details: See collab_progress/docs-skidl-kb-refresh-01-09-2025.md
- Verification: Docs-only change; no tests affected.
### UI: Generated Files scoped to current session
- Date: 2025-09-01
- Time (UTC): 00:00Z
- Branch/PR: main
- Files Changed (high level): tools, tests
- Details: See collab_progress/generated-files-current-session-only-01-09-2025.md
- Verification: Added unit test for filtering; please run `pytest -q` in the project venv.

### KiCad tool calls serialized; session retry and unique temp paths
- Date: 2025-09-01
- Time (UTC): 00:00Z
- Branch/PR: main
- Files Changed (high level): agents, docker_session
- Details: See collab_progress/kicad-session-serialization-and-retry-01-09-2025.md
- Verification: Please activate venv and run `pytest -q` locally; sandbox lacks pytest.

### Runtime tools accept script_content; guard bad paths
- Date: 2025-09-01
- Time (UTC): 00:00Z
- Branch/PR: main
- Files Changed (high level): tools, prompts
- Details: See collab_progress/runtime-tool-accepts-script-content-01-09-2025.md
- Verification: Please run `pytest -q` locally; sandbox lacks pytest.

### UI: Prevent duplicate plan rendering
- Date: 2025-09-01
- Time (UTC): 00:00Z
- Branch/PR: main
- Files Changed (high level): pipeline, tests
- Details: See collab_progress/ui-plan-duplicate-display-01-09-2025.md
- Verification: Added tests/test_plan_display_once.py; please run `pytest -q` in the project venv.

### UI: Single Live Progress spinner; Logfire always-on
- Date: 2025-08-10
- Time (UTC): 00:00Z
- Branch/PR: main
- Files Changed (high level): ui components, config, pipeline, pyproject, requirements, README
- Details: See collab_progress/ui-one-live-progress-and-always-logfire-10-08-2025.md
- Verification: pytest -q passed locally in venv; spinner renders cleanly with logs above it.

### Docs: Cleanup command for KiCad containers
- Date: 2025-08-09
- Time (UTC): 22:46Z
- Branch/PR: main
- Files Changed (high level): README
- Details: See collab_progress/docs-cleanup-section-09-08-2025.md
- Verification: pytest -q

### Signal handlers stop KiCad session on termination
- Date: 2025-08-09
- Time (UTC): 22:40Z
- Branch/PR: main
- Files Changed (high level): cli, tests
- Details: See collab_progress/signal-handler-kicad-stop-09-08-2025.md
- Verification: pytest -q

### Graceful exit via Esc and friendly Ctrl+C
- Date: 2025-08-11
- Time (UTC): 00:00Z
- Branch/PR: main
- Files Changed (high level): cli, ui components, tests
- Details: See collab_progress/graceful-exit-esc-11-08-2025.md
- Verification: pytest -q; ruff check .; mypy --strict circuitron (fails: unused type ignores and missing annotations)

### UI/UX: Human-friendly ERC result display (Issue #5)
- Date: 2025-08-10
- Time (UTC): 00:00Z
- Branch/PR: main
- Files Changed (high level): utils, ui/app, pipeline, tests
- Details: See collab_progress/ui-ux-issue5-erc-display-10-08-2025.md
- Verification: pytest -q passed locally in venv; added tests/test_erc_formatting.py.

### UI/UX: Feedback input uses boxed UI
- Date: 2025-08-09
- Time (UTC): 20:05Z
- Branch/PR: main
- Files Changed (high level): pipeline, tests
- Details: See collab_progress/ui-ux-issue4-feedback-input-box-09-08-2025.md
- Verification: Added unit test to assert UI.collect_feedback is used when a UI is provided.

### UI UX: Remove themes; centralize models
- Date: 2025-08-09
- Time (UTC): 19:15Z
- Branch/PR: main
- Files Changed (high level): ui (app, components), settings
- Details: See collab_progress/ui-ux-remove-themes-and-centralize-models-09-08-2025.md
- Verification: Ran static checks locally; pytest unavailable in sandbox. UI compiles; no residual theme references. Model menu reads from settings.available_models.

### Model selection via '/' menu
- Date: 2025-08-09
- Time (UTC): 19:28Z
- Branch/PR: main
- Files Changed (high level): ui/app, ui/components/completion
- Details: See collab_progress/ui-ux-model-menu-for-slash-09-08-2025.md
- Verification: Manual static review. Please run `pytest -q` locally.

### Slash-command dropdowns and model menu (UI UX Issue #3)
- Date: 2025-08-09
- Time (UTC): 18:35Z
- Branch/PR: main
- Files Changed (high level): ui/components (input_box, completion), ui/app, tests
- Details: See collab_progress/ui-ux-issue3-slash-dropdown-09-08-2025.md
- Verification: New tests added for completer; ran subset with venv Python: tests/test_slash_completion.py and tests/test_input_box.py passed. Full suite requires local env due to external dependencies.

### Suppress noisy copy errors in CLI
- Date: 2025-08-09
- Time (UTC): 17:20Z
- Branch/PR: main
- Files Changed (high level): docker_session
- Details: See collab_progress/ui-ux-issue1-log-demotion-09-08-2025.md
- Verification: Local run of subset not possible in sandbox; change is isolated to logging level and should not affect behavior. Full suite should pass; please run `pytest -q` in the project venv.

### Test suite stabilized; CLI/UI fixes after model switch
- Date: 2025-08-09
- Time (UTC): 12:23Z
- Branch/PR: main
- Files Changed (high level): cli, ui components, config, docker_session, pipeline, pyproject
- Details: See collab_progress/ci-fixes-model-switch-and-tests-09-08-2025.md
- Verification: pytest now restricted to tests/ via pyproject; 134 passed locally (`pytest`).
- Notes: Consider showing active model in the UI and persisting selection.

## Model switch via /model command
- Date: 2025-08-09
- Time (UTC): 10:59Z
- Branch/PR: main
- Files Changed (high level): circuitron/settings.py, circuitron/ui/app.py, tests/
- Details: See collab_progress/model-switch-interactive-09-08-2025.md
- Verification: Added unit tests (see tests/test_model_switch.py). Execution deferred in sandbox; run `pytest -q` locally.
- Notes: Consider showing active model in status bar and persisting choice across sessions.

