# Migration Guide: OpenAI Agents SDK 0.2.10

This repository has been upgraded from **openai-agents 0.1.0** to
**openai-agents 0.2.10**. The 0.2.x line introduces minor breaking
changes and new type requirements.

## Summary of Upstream Changes
- [`ToolContext` now requires a `tool_name` argument](https://openai.github.io/openai-agents-python/agents/tools/).
- Several APIs now accept `AgentBase` instead of `Agent` for type hints
  ([release notes](https://raw.githubusercontent.com/openai/openai-agents-python/main/docs/release.md)).

## Circuitron Updates
- Added `tool_name` whenever `ToolContext` is instantiated in tests.
- Patched CLI tests to mock `check_internet_connection` and
  `TerminalUI.prompt_user` to avoid real network calls and interactive
  prompts.
- Fixed `execute_final_script` mounting logic to default to
  `/workspace` on Unix paths.
- Added `scripts/run_compat.py` to run the test suite against arbitrary
  SDK versions.

## Behavior Notes
- No user‑facing CLI changes were introduced.
- Tests and tool adapters now require explicit tool names when using
  `ToolContext`.

Refer to the [OpenAI Agents SDK documentation](https://openai.github.io/openai-agents-python/)
for additional details and examples.
