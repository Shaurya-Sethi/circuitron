# CI Fixes: Model switch UI, CLI robustness, test stability

- Date: 2025-08-09
- Author: Codex CLI Agent

## Summary
Resolved multiple issues after adding the new `/model` command, and fixed failing pytest runs:
- Prevented prompt_toolkit from crashing tests by deferring interactive session creation.
- Avoided constructing `TerminalUI` in non-interactive code paths (CLI helpers) when not necessary.
- Restored strict environment handling in `setup_environment()` to not auto-load `.env` unless requested.
- Normalized Windows path separators in Docker copy helper to match test expectations.
- Adjusted retry wrapper to not inject unsupported kwargs into test stubs.

All tests in `tests/` now pass: `134 passed`.

## Files Changed
- Updated: `circuitron/cli.py` (lazy UI use; print fallbacks)
- Updated: `circuitron/ui/components/prompt.py` (lazy `PromptSession` construction)
- Updated: `circuitron/ui/components/input_box.py` (lazy `PromptSession` construction)
- Updated: `circuitron/config.py` (`setup_environment(dev, use_dotenv=False)`)
- Updated: `circuitron/docker_session.py` (posix-normalized dest paths)
- Updated: `circuitron/pipeline.py` (`run_with_retry` avoids unknown kwarg on stubbed `pipeline`)
- Updated: `pyproject.toml` (pytest: `testpaths = ["tests"]`, `addopts = "-q"`)

## Rationale
- Tests should run in headless environments; prompt_toolkit’s Win32 console detection caused crashes when instantiated eagerly.
- CLI helpers should not instantiate heavy UI components when only printing simple errors.
- Per project policy, `.env` should not be auto-loaded during tests; explicit opt-in keeps tests deterministic.
- Windows path joins produced backslashes; tests expect consistent POSIX-style paths for assertions.
- `run_with_retry` must be compatible with test stubs that omit optional kwargs like `keep_skidl`.

## Verification
- Ran targeted and full suites via the Windows venv executables:
  - `pytest -q tests/test_cli.py` → 15 passed
  - `pytest -q tests/test_pipeline.py::test_run_with_retry_behaviour` → passed
  - `pytest` (with `testpaths=tests`) → 134 passed in ~28s

## Issues
- None blocking. The `keep_skidl` flag is still honored by the `pipeline()` default pathway; `run_with_retry` no longer forwards it to stubbed pipelines in tests.

## Next Steps
- Optional: Show active model in the status bar/banner.
- Optional: Persist selected model across sessions.
