# Summary

Replaced Status spinner with a single Progress-based spinner to keep a single Live display while allowing direct prints/logging to flow above cleanly. Enabled Pydantic Logfire tracing by default (no longer tied to `--dev`), repurposed `--dev` to control verbosity only. Made `logfire` a required dependency. Updated README accordingly. Fixed `StatusBar` to log succinct updates above the spinner.

## Files Changed
- `circuitron/ui/components/spinner.py` — Progress-based spinner with stdout/stderr redirection.
- `circuitron/ui/components/status_bar.py` — Use `console.log` and correct indentation; avoid competing Live writes.
- `circuitron/config.py` — Always configure Logfire; `dev` now toggles verbosity only.
- `circuitron/pipeline.py` — Updated `--dev` help text.
- `pyproject.toml` — Added `logfire` to required dependencies; removed optional dev extra.
- `requirements.txt` — Added `logfire`.
- `README.md` — Installation/usage updated; dev mode semantics clarified; UI behavior documented.

## Rationale
- Rich supports a single Live display; Progress with `redirect_stdout/stderr` lets traces appear above the spinner without corruption.
- Tracing is core to debugging; making Logfire always-on simplifies behavior and docs.

## Verification
- Ran `pytest -q`: all tests passed locally in the project venv.

## Issues
- None known. If external code writes raw control sequences to stdout, output could still look odd; recommend routing via logging/Console.

## Next Steps
- Optionally style agent trace levels via logging configuration (colors per level), and add a small toggle for verbosity at runtime.
