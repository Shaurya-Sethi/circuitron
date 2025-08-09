---
applyTo: '**'
---

# UI/UX: Remove themes and centralize model list

## Summary
- Removed theme support across the Terminal UI (no theme switching, default styling only).
- Centralized selectable model list in `settings.available_models` and expanded pool.
- Updated the `/model` command and input completion to read from settings.

## Files Changed
- `circuitron/ui/app.py` — removed theme handling and `/theme` command; wired `/model` to `settings.available_models`.
- `circuitron/ui/components/`:
  - `banner.py` — fixed default gradient (no Theme dependency).
  - `input_box.py` — removed Theme; uses `settings.available_models`; updated completer commands.
  - `prompt.py`, `status_bar.py`, `spinner.py`, `panel.py`, `tables.py`, `message_panel.py`, `code_panel.py` — removed Theme references; default accent set to `"cyan"`.
- `circuitron/ui/themes.py` — deleted.
- `circuitron/settings.py` — added `available_models` with expanded list.

## Rationale
- Simplify UX by eliminating theme switching per request and avoid persisting theme state.
- Single source of truth for supported models improves discoverability and consistency across UI and runtime.

## Verification
- Grepped for `themes`, `Theme`, `theme_manager`, and `/theme` to ensure removal.
- Local static import check passes; CLI/UI modules import without theme references.
- Could not run `pytest -q` in this sandbox due to missing pytest; please run in the project venv.

## Issues
- Minor visual change: panels and status now use a fixed accent (`cyan`). If fully neutral styling is preferred, we can remove border styles entirely.

## Next Steps
- Optionally display the active model in the status bar.
- Consider persisting `settings.available_models` overrides via env or config if needed.

