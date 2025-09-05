# Instructions for working on Circuitron

Circuitron is an AI-powered PCB design accelerator that converts natural language requirements into SKiDL scripts, KiCad schematics, and PCB layouts using a multi-agent orchestration pipeline.

## Architecture Overview

### Core Pipeline Flow
The system follows a sophisticated, multi-stage agent workflow defined in `circuitron/pipeline.py`. It is not a simple linear sequence but includes robust, nested correction loops.

1.  **Planner** → **Plan Editor** (optional user feedback loop)
2.  **Part Finder** → **Part Selector**
3.  **Documentation Agent** (gathers context via RAG)
4.  **Code Generator**
5.  **Validation & Correction Loop**:
    *   The **Validator** agent checks the generated code.
    *   If validation fails, the **Corrector** agent attempts to fix it. This loop continues until the code is valid or a retry limit is reached.
6.  **Runtime Check & Correction Loop**:
    *   A runtime check is performed in a Docker container.
    *   If it fails, the **Runtime Corrector** agent attempts a fix. This loop continues until the script runs successfully.
7.  **ERC (Electrical Rule Check) & Handling Loop**:
    *   The **ERC Handler** agent runs ERC checks.
    *   If errors or unapproved warnings are found, it attempts to fix them. This loop continues until ERC passes or warnings are explicitly accepted by the agent.
8.  **Final Execution**: The final, validated script is executed to produce KiCad files.

Each agent has specific responsibilities and uses the OpenAI Agents SDK with structured Pydantic models defined in `circuitron/models.py`.

### Key Components
- **Agents** (`circuitron/agents.py`): Specialized OpenAI agents for each pipeline stage.
- **MCP Server** (`circuitron/mcp_manager.py`): A single, shared connection for RAG documentation, code validation, and hallucination detection.
- **Tools** (`circuitron/tools.py`): Docker-isolated functions for calculations, KiCad library searches, and ERC checks.
- **UI** (`circuitron/ui/app.py`): A Rich-based terminal interface for progress tracking and interactive plan editing.

## Project Map (high‑value files)
- `circuitron/pipeline.py` – Orchestration and correction loops.
- `circuitron/agents.py` – Agent factory functions and `_tool_choice_for_mcp`.
- `circuitron/tools.py` – Function tools and Docker integration.
- `circuitron/models.py` – Pydantic schemas.
- `circuitron/docker_session.py` – Container/session/mount logic.
- `circuitron/mcp_manager.py` – Shared MCP server connection.
- `circuitron/prompts.py` – System instructions for each agent.
- `circuitron/ui/app.py` – Terminal UI.
- `circuitron/correction_context.py` – Correction attempt tracking.
- `circuitron/settings.py`, `circuitron/config.py` – Defaults and env bootstrap.
- `circuitron/cli.py` – CLI entrypoint.
- `tests/` – Unit/integration tests with mocks.
- `README.md`, `SETUP.md` – End‑to‑end setup and diagrams.
- `collab_progress/` – Mandatory progress notes and changelog entries.

## Documentation & Knowledge Sources

**CRITICAL: ALWAYS reference official documentation for OpenAI Agents SDK (And other libraries/frameworks) before implementing anything new or changing existing behavior.**

###  **Primary Sources**: 

> **Note:** If working in a cloud environment (not locally), you would not have `context7` access. In that case, rely on the official docs.

1. The available tools with the `context7` MCP server will provide you with documentation for ANY library/framework/language,etc in the world.
2. If `context7` is not available, your primary source for technical reference should be the official documentation available on the internet (if you have access)

When using any API, class, method, or tool:
1. Look up the relevant section in the official documentation.
2. Verify syntax, arguments, return types, and intended behavior.
3. Follow usage patterns recommended in the official examples.
4. If uncertain, re-check the official docs or ask the user for clarification — never guess or hallucinate API usage.

**SKiDL Documentation**
*   **URL**: [https://devbisme.github.io/skidl/](https://devbisme.github.io/skidl/)
*   **Use For**: Understanding SKiDL functions, classes, and circuit generation patterns.

## Development Patterns

### Agent Creation Pattern
Agents are created in `circuitron/agents.py` as pure functions. They are configured with a prompt, model, output type, tools, and model settings. When an agent needs RAG/validation, attach the shared MCP server. Use guardrails where appropriate.

```python
# From circuitron/agents.py
def create_planning_agent() -> Agent:
    """Create and configure the Planning Agent."""
  model_settings = ModelSettings(tool_choice="required")

  tools: list[Tool] = [execute_calculation]

  return Agent(
    name="Circuitron-Planner",
    instructions=PLAN_PROMPT,
    model=settings.planning_model,
    output_type=PlanOutput,
    tools=tools,
    # Optional: constrain inputs
    input_guardrails=[pcb_query_guardrail],
    # Attach MCP for agents that need RAG/validation (omit here if not needed):
    # mcp_servers=[mcp_manager.get_server()],
    model_settings=model_settings,
  )
```

Notes
- For tools that call KiCad inside Docker, disable parallel tool calls to avoid container contention:
  `ModelSettings(tool_choice="required", parallel_tool_calls=False)`.
- Use `_tool_choice_for_mcp(model)` to allow `tool_choice="auto"` only for models that support it.

### Tool Definition Pattern
Agent tools are defined in `circuitron/tools.py`. Prefer the `@function_tool` decorator for new async functions. You can also wrap existing callables with `function_tool(...)` to expose them without a decorator.

```python
# From circuitron/tools.py
@function_tool
async def search_kicad_libraries(query: str, max_results: int = 50) -> str:
    """Search KiCad libraries using ``skidl.search``."""
    # ... implementation using DockerSession ...
```

```python
# Also supported: expose an existing function as a tool by wrapping it
async def run_runtime_check(... ) -> str:
  # ... implementation ...

run_runtime_check_tool = function_tool(run_runtime_check)
```

### Docker Integration
- All external tool execution (KiCad, calculations) occurs in isolated Docker containers.
- Persistent KiCad session: use `DockerSession` for tools that need SKiDL/KiCad. Calls like `exec_python_with_env`, `exec_erc_with_env`, and `exec_full_script_with_env` set KiCad env vars (KICAD5_SYMBOL_DIR, KICAD5_FOOTPRINT_DIR, KISYSMOD) and call `set_default_tool(KICAD5)`. Each run uses unique temp paths; container health is checked and recovered automatically.
- Final execution mounts outputs: for producing artifacts, a dedicated `DockerSession` mounts the host output directory into the container. On Windows, compute the mount path with `convert_windows_path_for_docker()`; otherwise default to a stable mount such as `/workspace`. Generated files are copied back with `copy_generated_files`, and only new/modified files are surfaced.
- Ephemeral calc runs: pure-Python calculations run via a short-lived `docker run` with restricted resources (no network, low memory/pids) using `settings.calculation_image`.
- Windows specifics: the code ensures `C:\tmp` exists to avoid Docker Desktop issues and retries `docker cp` on transient failures; always use `convert_windows_path_for_docker()` when mapping host paths.
- Concurrency: for tools backed by the KiCad container, set `ModelSettings(parallel_tool_calls=False)` to avoid container races.

### MCP Integration Pattern
Attach the shared MCP server for agents that need documentation/RAG or validation tools. Use model-aware `tool_choice` so only compatible models use `auto`.

```python
# Helper (from circuitron/agents.py)
def _tool_choice_for_mcp(model: str) -> str:
  return "auto" if model == "o4-mini" else "required"

def create_documentation_agent() -> Agent:
  model_settings = ModelSettings(tool_choice=_tool_choice_for_mcp(settings.documentation_model))
  return Agent(
    name="Circuitron-DocSeeker",
    instructions=DOC_AGENT_PROMPT,
    model=settings.documentation_model,
    output_type=DocumentationOutput,
    mcp_servers=[mcp_manager.get_server()],
    model_settings=model_settings,
  )
```

### Error Handling & Correction

- The pipeline is designed to be resilient. Correction loops are managed in `circuitron/pipeline.py`.
- The `CorrectionContext` class (`circuitron/correction_context.py`) tracks validation failures and correction attempts to prevent infinite loops. When modifying correction logic, ensure this context is updated correctly.

### Virtual Environment Activation (Windows/PowerShell - IF WORKING LOCALLY)
Always activate the project's virtual environment before running any Python commands, tests, or tools. Use this exact command in Windows PowerShell:

```powershell
& C:/Users/shaur/circuitron/circuitron_venv/Scripts/Activate.ps1
```

All subsequent Python and pytest invocations must occur in the same activated terminal session.

Notes
- Pytest discovery is restricted to the official tests/ suite via pyproject.toml. Integration demos under temp_test_files/ and test_run_output/ are excluded by default.
- setup_environment() is strict by default and will not auto-load a .env file. If you need .env values for ad-hoc runs, call setup_environment(use_dotenv=True).

## Coding Style & Conventions

* **Language:** Python 3.11+
* **Linting:** [`ruff`](https://docs.astral.sh/ruff/) (`pyproject.toml` included)
* **Type Checking:** [`mypy --strict`](https://mypy.readthedocs.io/en/stable/)
* **Naming Conventions:**
  * Function and variable names: `snake_case`
  * Class names: `PascalCase`
* **Docstrings:**
  All public functions/classes require complete docstrings:
  * List all arguments and their types
  * Specify the return type
  * Provide a concise usage example

## Testing Protocols

* **Testing:**
  Every new Agents-SDK tool must have a unit test with **mocked LLM outputs**. Write unit tests, integration tests, and end-to-end tests as appropriate.
* **Coverage:**
  * Achieve and maintain **≥90% branch coverage** on backend utilities.
  * Add edge-case tests for every Agents-SDK tool and SKiDL helper.
* **Test Framework:**
  Use `pytest`.
* **Continuous Testing:**
  After every logical change, **run all tests quietly**:
  ```
  pytest -q
  ```
  Refuse to commit any code if tests fail or coverage decreases.

## Collaboration & Progress Tracking Protocol

**Before starting any new task:**
- Review the most recent and relevant progress notes in the `collab_progress` folder to understand the current state, recent changes, and open questions.

**After completing any significant change:**
- Follow the instructions in `collab_progress/PROTOCOL.md` to document your work.

**This protocol is mandatory for all AI coding assistants and must be followed for every codebase change.**

## Full-Code Ownership & Test-Driven Development (TDD) Mandate

> **You are the sole implementation agent for this repository.**
>
> * Treat the project as a green-field codebase:
>   Generate all source files, config, and docs needed to meet requirements.
> * Follow strict TDD:
>   \- Write a failing test (`pytest`) for any new behavior before writing production code.
>   \- Write minimal production code to pass the test.
>   \- Refactor for clarity after passing.
> * Keep coverage ≥90%; add edge/corner-case tests for every feature.