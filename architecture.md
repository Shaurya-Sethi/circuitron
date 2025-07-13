# Circuitron Architecture

_(Auto-generated overview of the current codebase)_

## Overview

Circuitron is an agent-driven PCB design accelerator. It turns natural language prompts into SKiDL scripts, KiCad schematics, and PCB layouts. The README explains the core pipeline and features:

- Multi-agent workflow using OpenAI Agents SDK.
- Retrieval-Augmented Generation via an MCP server.
- Real component search with KiCad libraries.
- Iterative validation and correction until code passes ERC.
- Dockerized toolchain for repeatability.

These aspects appear at the start of the README【F:README.md†L14-L24】【F:README.md†L25-L38】.

## Packages and Modules

```
/ (repository root)
│  README.md, overview.md, requirements.txt
│  circuitron/                 # main package
│  tests/                      # pytest suite
```

Key modules inside `circuitron/`:

- `cli.py` – command line entry, sets up environment and runs the UI.
- `pipeline.py` – orchestrates agents and handles retries.
- `agents.py` – factory functions creating each OpenAI agent.
- `tools.py` – pure functions exposed to the agents (KiCad search, ERC, runtime checks, etc.).
- `mcp_manager.py` – manages the single MCP server connection shared across agents.
- `docker_session.py` – helper for running KiCad or Python scripts inside Docker.
- `ui/` – terminal UI components built with Rich and prompt_toolkit.
- `models.py` – pydantic models defining inputs/outputs for each agent stage.
- `settings.py` – dataclass of configuration values loaded from env vars.

Tests cover these modules extensively (116 passing).

## Configuration

`settings.py` defines default models and Docker images. Environment variables override them. Example fields include the calculation and KiCad images and the MCP URL【F:circuitron/settings.py†L18-L38】. The README documents these variables for users【F:README.md†L166-L170】.

`config.setup_environment()` loads `.env`, verifies required variables, optionally enables tracing, and warns if the MCP server is unreachable.

## Network & Health Checks

`network.is_connected()` performs a HEAD request to check connectivity and prints a message when offline【F:circuitron/network.py†L9-L43】.

The CLI uses `check_internet_connection()` before running the pipeline.

## MCP Server Management

The MCP manager lazily creates one `MCPServer` and connects with retries on startup. It exposes `initialize()` and `cleanup()` so the CLI/UI can manage the connection lifecycle【F:circuitron/mcp_manager.py†L13-L61】.

## Terminal UI

`TerminalUI` composes banner, prompt, spinner and status bar components. It provides methods such as `start_stage()` and `finish_stage()` to update progress indicators. The UI collects feedback from the user, displays tables of parts, and shows generated files. It wraps a call to `run_with_retry()` while showing a persistent status bar【F:circuitron/ui/app.py†L23-L126】.

Theme settings are persisted under `~/.circuitron` and can be changed interactively via `/theme` commands.

## CLI Entry Point

`cli.main()` parses command line arguments, sets up environment, checks internet and container readiness, then launches the `TerminalUI`【F:circuitron/cli.py†L52-L91】. The CLI prints the banner, prompts the user for a design request, and displays the generated SKiDL code once finished.

## Agent Pipeline

`pipeline.run_with_retry()` repeatedly calls `pipeline()` on failure with a retry limit【F:circuitron/pipeline.py†L478-L500】.

`pipeline()` executes the following stages in sequence【F:circuitron/pipeline.py†L502-L537】【F:circuitron/pipeline.py†L553-L720】:

1. **Planning** – `run_planner()` generates the initial design plan.
2. **User Feedback** – `collect_user_feedback()` may gather edits or answers.
3. **Part Finder** – searches KiCad libraries for components.
4. **Part Selector** – chooses components and extracts pin details.
5. **Documentation** – retrieves SKiDL examples via MCP tools.
6. **Code Generation** – produces SKiDL code from plan, parts and docs.
7. **Validation** – static analysis and knowledge graph checks.
8. **Correction Loops** – validation corrections repeat until passing.
9. **Runtime Check** – execute the code in Docker to catch Python errors.
10. **ERC Handling** – run ERC and apply fixes/warning approvals.
11. **Final Execution** – full script run producing schematic, netlist and PCB files.【F:circuitron/pipeline.py†L640-L726】

Each stage prints panels or tables via the UI. Loops have iteration caps to avoid infinite retries.

## Tools and Docker Execution

`tools.py` defines pure function tools registered with Agents SDK. Highlights:

- `execute_calculation` – runs small Python snippets in a minimal container.
- `search_kicad_libraries` and `search_kicad_footprints` – query SKiDL/ KiCad libs.
- `extract_pin_details` – reads pin info with SKiDL `show()`.
- `run_erc` and `execute_final_script` – execute SKiDL code within a KiCad Docker container and capture generated files.

Docker sessions are managed by `DockerSession` which starts/stops containers and copies generated files out【F:circuitron/docker_session.py†L23-L181】【F:circuitron/docker_session.py†L320-L409】.

## Models

`models.py` contains Pydantic models for each agent’s input and output structures. Examples include `PlanOutput`, `PartFinderOutput`, `CodeGenerationOutput`, `CodeValidationOutput`, `ERCHandlingOutput` etc.【F:circuitron/models.py†L1-L80】【F:circuitron/models.py†L160-L232】【F:circuitron/models.py†L320-L387】.

`CorrectionContext` keeps track of validation, ERC, and runtime correction attempts, enabling agents to reason about past fixes and avoid loops【F:circuitron/correction_context.py†L12-L163】【F:circuitron/correction_context.py†L160-L320】.

## Session Memory & Projects

The project overview describes that each session is tied to a project and all prompts, plans and schematics are stored for recall【F:overview.md†L40-L44】. (Implementation of persistence is not yet in the repo but planned.)

## Testing

`pytest -q` reports **116 passed** confirming the suite exercises pipeline functions and CLI usage【b9da85†L1-L12】.

## Extensibility & Caveats

- Agents are created via factory functions in `agents.py`. New stages can be inserted by adding functions and adjusting the pipeline.
- The MCP server address and model names are configurable via environment variables.
- Docker interaction is isolated in `docker_session.py` making it possible to switch container images or run locally.
- ERC handling currently approves warnings based on agent judgment; further manual review is recommended.
- Future roadmap items include a web UI, DeepPCB autorouting integration, and team collaboration features (see overview.md for details).

## Mermaid Diagram

See `architecture_diagram.mmd` for a visual overview.

## Appendix: Analysis Log

1. Checked repository structure with `ls`.
2. Opened `overview.md` and `README.md` for high-level context.
3. Inspected main package modules (`settings.py`, `pipeline.py`, `agents.py`, etc.).
4. Examined terminal UI components and theme handling.
5. Reviewed pipeline orchestration and agent loops.
6. Noted configuration options and environment variable usage.
7. Ran the full test suite confirming 116 tests pass.
8. Summarized findings here.

