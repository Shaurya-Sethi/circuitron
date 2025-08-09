# Signal handlers stop KiCad session on termination

## Summary
- Register SIGINT and SIGTERM handlers that call `kicad_session.stop()` before exiting.
- Note that `atexit` remains a fallback cleanup.

## Files Changed
- `circuitron/cli.py`
- `tests/test_cli.py`

## Rationale
Ensure the KiCad Docker container is stopped promptly when the process receives termination signals.

## Verification
- `pytest -q`

## Issues
- None known.

## Next Steps
- None.
