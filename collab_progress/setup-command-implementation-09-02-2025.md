Title: Add Setup Agent and CLI/UX for Knowledge Base Initialization
Date: 2025-09-02

Summary
- Implemented an isolated Setup Agent and a `circuitron setup` CLI subcommand to initialize Supabase (docs) and Neo4j (knowledge graph) via MCP tools (`smart_crawl_url`, `parse_github_repository`).
- Added interactive `/setup` command in the Terminal UI.
- Kept setup isolated from the main pipeline (no KiCad container usage).

Changes
- Models: `SetupOutput` in `circuitron/models.py`.
- Prompts: `SETUP_AGENT_PROMPT` in `circuitron/prompts.py`.
- Agent: `circuitron/setup_agent.py` creates a dedicated agent with its own MCP server instance.
- Runner: `circuitron/setup.py` with `run_setup(...)` coroutine.
- CLI: `pipeline.parse_args()` now supports a `setup` subcommand; `cli.main()` branches to run setup without starting KiCad.
- UI: Added `/setup` handling in `TerminalUI.prompt_user()`; added `/setup` to default completer in `InputBox`.
- Docs: README and SETUP updated to recommend the new command.

Tests Added
- `tests/test_setup_models.py` — validates `SetupOutput` and strict field policy.
- `tests/test_setup_agent.py` — ensures dedicated MCP server and tool_choice behavior.
- `tests/test_cli_setup.py` — verifies CLI setup path calls runner and skips KiCad start.
- `tests/test_setup_ui.py` — asserts `/setup` appears in the default completer.

Verification
- Please run in venv (PowerShell):
  1) `& C:/Users/shaur/circuitron/circuitron_venv/Scripts/Activate.ps1`
  2) `pytest -q`

Notes
- The Setup Agent uses an ephemeral MCP connection (no impact on the pipeline’s shared manager).
- Defaults target SKiDL docs and repo; can be overridden via CLI flags.

