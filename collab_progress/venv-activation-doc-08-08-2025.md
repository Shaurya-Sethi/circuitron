# Venv activation doc — 08-08-2025

## Summary
Documented mandatory Windows PowerShell virtual environment activation for all Python work.

## Files Changed
- .github/copilot-instructions.md — added explicit venv activation section with exact command.

## Rationale
Ensures consistent dependency resolution and prevents environment-related test failures.

## Verification
Activated the env in terminal and confirmed prompt shows `(circuitron_venv)`.

## Next Steps
- Keep this requirement in mind for all automated runs (tests, lint, scripts).
