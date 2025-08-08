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

## Documentation & Knowledge Sources

**CRITICAL: ALWAYS consult the official, up-to-date online documentation for any library, framework, or programming language you are working with before implementing or changing anything related to it.**  
Your **primary source** for technical reference should be the official documentation available on the internet.

When using any API, class, method, or tool:
1. Look up the relevant section in the official documentation.
2. Verify syntax, arguments, return types, and intended behavior.
3. Follow usage patterns recommended in the official examples.
4. If uncertain, re-check the official docs or ask the user for clarification — never guess or hallucinate API usage.

### OpenAI Agents SDK — Special Considerations

Circuitron uses a **new and in-development library**: **OpenAI Agents SDK**.  
We are working with **version `0.1.0`**, and the local documentation included in this repository matches this exact version.  
Online documentation may refer to newer versions with API changes — when conflicts arise between the online docs and the local knowledge base, always **prioritize the local version** to ensure compatibility.

### Fallback to Local Documentation (when to use it)

If you cannot access online documentation (e.g., due to network restrictions, rate limits, or downtime) or need to confirm the exact behavior for version `0.1.0`, use the **local OpenAI Agents SDK Knowledge Base** included in the repository:

  **Location:** `openai_agents_knowledge/` directory in project root
  **Key Files:**
  - `openai_agents_knowledge_base.md` - Complete consolidated knowledge base (44,400+ lines)
  - `file_catalog.md` - Detailed catalog of all 361 source files
  - `code_analysis.md` - Python code structure and module analysis
  - `README.md` - Usage guide for the knowledge base
  
  **Usage Instructions:**
  - **For implementation patterns:** Reference `/examples/` section for 73+ practical usage examples
  - **For core functionality:** Study `/src/agents/` section for main SDK implementation
  - **For testing approaches:** Examine `/tests/` section for comprehensive test patterns
  - **For specific features:** Use file catalog to locate relevant source files
  - **For architecture understanding:** Consult code analysis for module relationships

## Development Patterns

### Agent Creation Pattern
Agents are created in `circuitron/agents.py` as pure functions. They are configured with a prompt, model, output type, and tools.

```python
# From circuitron/agents.py
def create_planning_agent() -> Agent:
    """Create and configure the Planning Agent."""
    model_settings = ModelSettings(tool_choice="required")
    return Agent(
        name="Circuitron-Planner",
        instructions=PLAN_PROMPT,
        model=settings.planning_model,
        output_type=PlanOutput,
        tools=[execute_calculation],
        model_settings=model_settings,
    )
```

### Tool Definition Pattern
All agent tools are defined in `circuitron/tools.py` using the `@function_tool` decorator.

```python
# From circuitron/tools.py
@function_tool
async def search_kicad_libraries(query: str, max_results: int = 50) -> str:
    """Search KiCad libraries using ``skidl.search``."""
    # ... implementation using DockerSession ...
```

### Docker Integration
- All external tool execution (KiCad, calculations) occurs in isolated Docker containers.
- Use the `DockerSession` class from `circuitron/docker_session.py` for persistent containers (like the one for KiCad).
- For Windows paths, always use the `convert_windows_path_for_docker()` utility from `circuitron/utils.py`.

### Error Handling & Correction

- The pipeline is designed to be resilient. Correction loops are managed in `circuitron/pipeline.py`.
- The `CorrectionContext` class (`circuitron/correction_context.py`) tracks validation failures and correction attempts to prevent infinite loops. When modifying correction logic, ensure this context is updated correctly.

## Critical Dependencies & Setup

### Required Services
The following services **must be running** for Circuitron to function:
1.  **Docker Daemon**
2.  **Circuitron MCP Server**: Provides RAG and validation. Start it with:
    ```bash
    docker run --env-file mcp.env -p 8051:8051 ghcr.io/shaurya-sethi/circuitron-mcp:latest
    ```

### Virtual Environment Activation (Windows/PowerShell)
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
- Follow the instructions in `collab_progress/track_progress.md` to document your work.

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