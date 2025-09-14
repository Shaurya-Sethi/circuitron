# Fix: Guard CLI/UI when MCP server isn’t running

## Summary
Uncaught connection errors were crashing the CLI and UI when Circuitron was launched without the MCP server running (see `task.md` trace). I reintroduced and hardened MCP startup checks so that Circuitron:

- Detects MCP server availability before running the pipeline or setup.
- Shows a clear, actionable message to start the server.
- Exits gracefully instead of crashing.
- Restores container detection for `circuitron-mcp` via `docker ps`.

## Files Changed
- `circuitron/network.py`: Added `is_mcp_server_available`, `detect_running_mcp_docker_container`, and `verify_mcp_server`.
- `circuitron/cli.py`: Verify MCP before initializing agents; friendly error handling. Also applied to `/setup` subcommand.
- `circuitron/pipeline.py`: Verify MCP before `mcp_manager.initialize()`; friendly fallback.
- `circuitron/ui/app.py`: Verify MCP before UI run and `/setup`; added friendly messages.
- `tests/test_mcp_server_checks.py`: Unit tests for the new checks.

## Rationale
The `/setup` addition introduced code paths that connect to MCP without early validation. This caused exceptions from the Agents SDK HTTP/SSE client when MCP was not running. Centralizing the check and surfacing clear instructions prevents crashes and improves UX.

## Verification
- Added tests covering:
  - Success path when MCP is available.
  - Failure path with no container running (message includes `docker run` command).
  - Container present but endpoint not yet responding (booting) warning.
- Please run `pytest -q` in the project venv.

## Notes
- The check tries `/health` first, then `/sse` with a short timeout, and falls back to a Docker container scan (`docker ps`) to differentiate “not running” vs “booting”.
- Env override: Set `CIRCUITRON_SKIP_MCP_CHECK=1` to bypass preflight checks if needed in tests.

## Next Steps
- If desired, add a `circuitron doctor` command to validate all external dependencies (Docker, MCP, KiCad) in one go.

