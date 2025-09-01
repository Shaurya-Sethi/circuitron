# Runtime tools accept script_content; guard bad paths (01-09-2025)

## Summary
- `run_runtime_check` and `run_erc` tools now accept either a host `script_path` or raw `script_content`. This prevents agents from passing container paths like `/tmp/script.py`, which caused Windows `CreateFile C:\\tmp` copy failures.
- Added preflight validation to return a clear error if a non-existent container-style path is provided, instructing the agent to pass `script_content` instead.
- Updated prompts to explicitly instruct agents to pass `script_content` when calling these tools.

## Files Changed
- `circuitron/tools.py`
  - `run_runtime_check`: new signature `(script_path: str | None = None, script_content: str | None = None)`; temp-file management when `script_content` is provided; friendly error when nonexistent `/tmp/...` path is passed.
  - `run_erc`: same pattern as above; preserves existing JSON result fields.
- `circuitron/prompts.py`
  - Added CRITICAL guidance under Runtime Correction and ERC Handling to always pass `script_content` and never container paths.

## Rationale
- Agents sometimes passed `/tmp/script.py` to the tool, which is a container path, not a host file. Docker on Windows failed with `CreateFile C:\\tmp\\script.py: The system cannot find the file specified.` Accepting `script_content` avoids this class of errors.

## Verification
- Static review; sandbox cannot run tests. Please validate locally:
  - Activate venv: `& C:/Users/shaur/circuitron/circuitron_venv/Scripts/Activate.ps1`
  - Run: `pytest -q`

## Issues
- None known. Pipeline calls remain backward compatible (pass `script_path`).

## Next Steps
- Consider migrating ERC tool callers to use `script_content` in all agent prompts for consistency.
