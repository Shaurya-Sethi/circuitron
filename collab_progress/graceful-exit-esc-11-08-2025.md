# Graceful exit with Esc key and friendly Ctrl+C handling

## Summary
- Allow exiting at any prompt by pressing `Esc`.
- Catch `KeyboardInterrupt` and display a friendly goodbye message.
- Informed users about `Esc` usage in UI banner and prompts.

## Files Changed
- `circuitron/cli.py`
- `circuitron/ui/app.py`
- `circuitron/ui/components/input_box.py`
- `circuitron/ui/components/prompt.py`
- `tests/test_cli.py`
- `tests/test_feedback_ui.py`
- `tests/test_input_box.py`
- `tests/test_model_switch.py`

## Rationale
Improve usability by offering an intuitive exit mechanism and clearer messaging when terminating the program.

## Verification
- `pytest -q`
- `ruff check .`
- `mypy --strict circuitron` *(fails: Unused type ignores and missing annotations)*

## Issues
- Existing mypy errors remain; repository not fully type-safe.

## Next Steps
- Address outstanding mypy errors across UI components.
