---
applyTo: '**'
---

# UI/UX: Model selection menu via '/'

## Summary
- Updated the `/model` flow to no longer inline the full model list in the prompt.
- Added a `ModelMenuCompleter` that displays available models when the user types `/`, mirroring the top-level command menu UX. Autocomplete while typing is retained.

## Files Changed
- `circuitron/ui/components/completion.py` — added `ModelMenuCompleter`.
- `circuitron/ui/app.py` — switched `/model` prompt to use the new completer and simplified the prompt message.

## Rationale
- Align the model selection UX with the existing slash-command menu and avoid long inline lists in the prompt.

## Verification
- Manual static review: ensures menu appears when typing `/` and validation still checks against `settings.available_models`.
- Could not run `pytest` in this sandbox; please run in venv locally.

## Next Steps
- Optional: show the currently active model in the status bar.

