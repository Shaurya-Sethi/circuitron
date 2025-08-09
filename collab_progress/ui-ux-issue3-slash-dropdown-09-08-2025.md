# UI/UX Improvement: Slash-command dropdowns and model selection menu (Issue #3)

## Summary
Implemented interactive, context-aware dropdowns in the CLI input to improve discoverability and selection of commands and models:
- Typing '/' now shows a dropdown of available commands (with arrow-key navigation and Enter to select).
- Using '/model' triggers a follow-up prompt with a dropdown to choose from available models.

## Files Changed
- `circuitron/ui/components/completion.py` (new): SlashCommandCompleter implementation.
- `circuitron/ui/components/input_box.py`: Integrated completer support, boxed prompt retains styling.
- `circuitron/ui/app.py`: Model selection prompt now uses a dropdown completer.
- `tests/test_slash_completion.py` (new): Unit tests for completer behavior and InputBox integration.

## Rationale
Address Issue #3 in task.md by providing a familiar command palette experience in the terminal via prompt_toolkit’s completion UI, improving UX without altering core pipeline behavior.

## Verification
- Added tests covering:
  - Command suggestions upon typing '/'.
  - Contextual model suggestions after '/model'.
  - InputBox passes a completer to PromptSession.
- Ran subset tests with the project venv:
  - Passed: `tests/test_slash_completion.py`, `tests/test_input_box.py`.
  - Note: Full suite execution in this environment shows external dependency warnings; run `pytest -q` locally in the activated venv for full verification.

## Known Issues / Limitations
- Model list is currently static ("o4-mini", "gpt-5-mini"). If more models are supported later, update the lists in `InputBox` and `TerminalUI` or surface a single source of truth (e.g., settings).
- Theme name completion scaffolding exists in the completer but is not displayed by default; can be enabled by passing theme names.

## Next Steps
- Centralize available model names (e.g., in `settings` or config) and reuse in both UI and tests.
- Extend the completer to show available theme names on `/theme ` context.
- Consider showing the active model in the status bar and persisting the selection across sessions.

