# Circuitron Changelog (collab_progress index)

## Test suite stabilized; CLI/UI fixes after model switch
- Date: 2025-08-09
- Time (UTC): 12:23Z
- Branch/PR: main
- Files Changed (high level): cli, ui components, config, docker_session, pipeline, pyproject
- Details: See collab_progress/ci-fixes-model-switch-and-tests-09-08-2025.md
- Verification: pytest now restricted to tests/ via pyproject; 134 passed locally (`pytest`).
- Notes: Consider showing active model in the UI and persisting selection.

Purpose
- This file is the single, ordered index of all progress notes under collab_progress.
- It makes recent changes easy to find and links each entry to the detailed Markdown note(s).

Rules
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

---

## Model switch via /model command
- Date: 2025-08-09
- Time (UTC): 10:59Z
- Branch/PR: main
- Files Changed (high level): circuitron/settings.py, circuitron/ui/app.py, tests/
- Details: See collab_progress/model-switch-interactive-09-08-2025.md
- Verification: Added unit tests (see tests/test_model_switch.py). Execution deferred in sandbox; run `pytest -q` locally.
- Notes: Consider showing active model in status bar and persisting choice across sessions.
