# Circuitron Backend Readiness for Frontend Integration

## Current State

- Entry Points: CLI starts via `circuitron/__main__.py` → `circuitron/cli.py:main()` which parses args in `pipeline.parse_args()`, sets up env (`config.setup_environment`), checks internet and KiCad Docker, prompts for a design, and runs `TerminalUI.run()` which calls `pipeline.run_with_retry()`/`pipeline.pipeline()`.
- Orchestration: `circuitron/pipeline.py` coordinates agents in ordered stages: planner → (optional) plan editor → part finder → part selection → docs → codegen → validation → correction loops → runtime check → ERC handling → final execution. Each stage has a small wrapper (`run_*`) that builds inputs, calls an agent (`agents.py`), and returns a Pydantic model from `models.py`.
- Models: All agent I/O and final code outputs are strongly typed `pydantic` models (e.g., `PlanOutput`, `PartFinderOutput`, `CodeGenerationOutput`), which is API-friendly.
- UI Coupling: Most pipeline functions accept `ui: TerminalUI | None` and only render when provided; otherwise they sometimes print to stdout. `utils.collect_user_feedback` prompts via `input()` when no UI is supplied, which blocks in headless contexts. `network.check_internet_connection()` imports `TerminalUI` and displays errors directly.
- Agents & SDK: Agents are created in `circuitron/agents.py` using the OpenAI Agents SDK (tools, MCP server, model settings). A single shared MCP server is managed by `mcp_manager` and is initialized/cleaned at run boundaries.
- Tooling/Execution: KiCad/SKiDL work runs in Docker via `DockerSession` (`tools.py`, `docker_session.py`). Helper tools include library/footprint search, pin extraction, ERC/runtime checks, and final script execution (`execute_final_script`). File outputs are copied from the container into `./circuitron_output` (or `--output-dir`) and returned as a JSON manifest.
- Async Model: Pipeline is `async` and uses `await asyncio.to_thread(subprocess.run, ...)` for Docker calls. This makes it suitable for integration in an async web server (e.g., FastAPI) but requires care for concurrency.

## Gaps & Opportunities

- Blocking Prompts: `utils.collect_user_feedback` prompts the user even when no UI is provided. For web/Electron APIs, a non-interactive path (skip or accept provided feedback) is needed to avoid blocking.
- UI in Utilities: `network.check_internet_connection()` directly uses `TerminalUI` to print errors. This should be decoupled (pure function that returns bool/raises), letting callers decide how to notify the user.
- Print Fallbacks: Several code paths print when `ui is None`. For API use, prefer structured events/logs rather than stdout prints.
- Concurrency & Containers: The global `kicad_session` container name is PID-based and helper methods copy to fixed paths like `/tmp/script.py`. Concurrent jobs in one process could race on shared container state and temp paths. `execute_final_script` also uses a PID-based container name for finalization. These should be made job-scoped (unique container name and temp paths) or orchestrated via a per-job session/pool.
- Progress/Streaming: Status updates are currently Terminal-only (spinner, panels). A structured event stream (progress, logs, artifacts) is needed for WebSockets/SSE.
- Job Lifecycle: No concept of “jobs” with IDs, statuses, retries, and artifacts accessible post-run. API-first integration benefits from a job manager to submit, monitor, and download results.
- Config Lifecycle: MCP server is initialized per run via UI/CLI. A web service should initialize MCP at app startup and cleanly shut down on exit.
- Error Semantics: Many errors are conveyed via printing; web APIs need consistent exceptions and error payloads.

## Roadmap

1) Headless Mode & Boundaries (Foundational)
- Pure checks: Refactor `network.check_internet_connection()` to return bool/raise, no UI calls.
- Non-interactive feedback: Add optional `feedback_provider: Callable | None` to `pipeline.pipeline()` (or `run_with_retry`) so headless runs can skip prompting or receive provided feedback. Default to skip when not supplied.
- Progress interface: Define a minimal `ProgressSink` protocol (start_stage, finish_stage, info/warn/error, display_plan/parts/docs/validation/files) implemented by `TerminalUI` and a `NullSink`. Use it instead of directly printing when `ui is None`.
- branch: `feat/headless-mode-progress-interface`

2) Container Safety for Concurrency
- Unique scoping: Update `DockerSession` call sites to accept a per-job container name and unique temp file paths (`/tmp/script-{job_id}.py`).
- Final execution: Ensure `execute_final_script` uses a per-job container (e.g., `circuitron-final-{job_id}`) and job-scoped volume mounts.
- Guard rails: Keep thread locks for `start()` and consider a lightweight queue if SKiDL/KiCad operations must be serialized.
- branch: `feat/container-concurrency-safety`

3) Job Orchestration Layer
- Job model: Add `jobs/manager.py` maintaining job records (id, prompt, options, status, timestamps, errors, artifacts, logs). In-memory first; file-backed or DB later.
- Event bus: Introduce `events.py` with a simple pub/sub sink (async generator) that `ProgressSink` implementations can write to. Persist a ring buffer per job for replay.
- Artifacts: Normalize the `execute_final_script` manifest into a first-class “artifacts” list on the job.
- branch: `feat/job-orchestration`

4) FastAPI Service (Web-first API)
- App lifecycle: Initialize MCP at startup and shut down on exit; pre-warm or pool KiCad containers if desired.
- Endpoints:
  - POST `/jobs` → submit a run (prompt, options like `keep_skidl`, `no_footprint_search`) → returns `{job_id}`.
  - GET `/jobs/{id}` → status and summary metadata.
  - GET `/jobs/{id}/events` → Server-Sent Events or WebSocket for progress/logs.
  - GET `/jobs/{id}/artifacts` → list artifacts with sizes/paths.
  - GET `/jobs/{id}/artifacts/{name}` → file download.
  - GET `/health` → service/MCP/KiCad checks.
- Execution: Run pipeline in a background `asyncio.Task` per job, passing a job-scoped `ProgressSink` that publishes events.
- branch: `feat/fastapi-service`

5) Frontend Integration (React/Next.js/Electron)
- Client patterns: Use WebSocket/SSE stream for live progress and a polling or event-driven artifacts list for downloads.
- UX affordances: Expose reasoning toggles, retries, options (`--keep-skidl`, `--no-footprint-search`), and show agent summaries and ERC results as structured panels.
- branch: `feat/frontend-integration`

6) Preserve CLI and Backward Compatibility
- Keep `TerminalUI` for interactive runs; have CLI share the same `ProgressSink` and job orchestration, or continue to call pipeline directly with `TerminalUI`.
- Ensure CLI paths still work without starting the web server.
- branch: `feat/cli-backward-compatibility`

7) Testing & Hardening
- Unit tests: Mock MCP/Docker; verify job lifecycle, event streaming, and endpoint contracts. Add tests to ensure no blocking prompts in headless mode.
- Concurrency tests: Launch multiple jobs; verify unique container names and no temp path collisions.
- Integration tests: End-to-end job submission → streamed progress → artifacts available.
- branch: `feat/testing-hardening`

Notes
- The current async pipeline, Pydantic outputs, and small `run_*` wrappers are already API-friendly. The primary work is decoupling interactivity and making execution job-scoped and concurrent-safe.
- When implementing, follow the OpenAI Agents SDK patterns used in `circuitron/agents.py` and the local knowledge base (`openai_agents_knowledge/`) for tool purity and streaming best practices. MCP lifecycle should be owned by the process, not per-request.

