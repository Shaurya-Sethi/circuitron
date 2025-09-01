# Serialize KiCad tool calls; unique temp paths + retry (01-09-2025)

## Summary
- Prevents parallel tool-call races against the KiCad Docker session by disabling parallel tool calls for KiCad-using agents.
- Hardens DockerSession by using unique container temp paths and adding a one-time restart+retry when the container is missing.

## Files Changed
- `circuitron/agents.py`
  - Set `parallel_tool_calls=False` in model settings for PartFinder, PartSelection, RuntimeCorrector, and ERCHandler agents.
- `circuitron/docker_session.py`
  - `exec_python_with_env`: use unique `/tmp/temp_script_<uuid>.py`; retry once on "No such container"; cleanup updated.
  - `exec_full_script_with_env`: use unique `/tmp/script_<uuid>.py`; retry once on missing container; cleanup updated.
  - `exec_erc_with_env`: keep `/tmp/script.py` (wrapper expects it) but use unique wrapper path `/tmp/wrapper_<uuid>.py`; retry once on missing container; cleanup updated.
  - `_run_docker_cp_with_retry`: restart container and retry if `docker cp` fails with "No such container".

## Rationale
- Some models (e.g., gpt-5) issue multiple tool calls in parallel, causing collisions on fixed container paths and occasionally killing the container. Serializing tool calls for KiCad-bound agents and avoiding filename collisions addresses these issues.
- If the container vanishes (OOM or external stop), a one-time restart+retry is a safe, fast recovery.

## Verification
- Sandbox lacks pytest; please run in the project venv:
  - Activate: `& C:/Users/shaur/circuitron/circuitron_venv/Scripts/Activate.ps1`
  - Run: `pytest -q`
- Manual reasoning: Changes are localized, default behavior preserved; existing tests for `exec_full_script` remain valid (static path kept). No API changes for tool functions.

## Issues
- `exec_erc_with_env` still uses a static script path (`/tmp/script.py`) because wrappers reference it; with serialized tool calls, collisions are avoided. If needed later, we can parameterize the script path in wrappers.

## Next Steps
- Consider adding an asyncio Semaphore to further cap concurrency even if parallel tool calls are re-enabled.
- Optionally expose memory/pid limits for the KiCad container via environment variables.
