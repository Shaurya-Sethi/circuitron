# Model Switch via /model Command

- Date: 2025-08-09
- Author: Codex CLI Agent

## Summary
Added interactive model selection to Circuitron. Users can change the active model between "o4-mini" and "gpt-5-mini" at runtime via a new `/model` command in the terminal UI. Introduced a helper to update all agent model fields consistently.

## Files Changed
- Updated: `circuitron/settings.py`
- Updated: `circuitron/ui/app.py`
- Added tests: `tests/test_model_switch.py`

## Rationale
- Provide an easy, discoverable way to switch models per session without restarting.
- Keep defaults stable ("o4-mini") and allow opting into "gpt-5-mini" when desired.
- Ensure all relevant agent roles use the same selected model for consistency.

## Verification
- Unit tests added:
  - `test_settings_set_all_models` verifies all Settings model fields update.
  - `test_ui_model_command_updates_settings_and_agents` simulates `/model` → selection → prompt, verifies settings updated, confirmation printed, and agents use the new model.
- Note: Tests were not executed in this sandbox due to missing runtime for `pytest`. Expected to pass in project environment. Run locally: `pytest -q`.

## Issues
- None observed. Tool choice logic remains compatible: non-"o4-mini" models use `tool_choice="required"` for MCP tools.

## Next Steps
- Optional: Display the active model in the status bar/banner.
- Optional: Persist selected model across sessions (e.g., via env or a config file) if desired.

