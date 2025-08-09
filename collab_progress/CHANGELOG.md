# Circuitron Changelog (collab_progress index)

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