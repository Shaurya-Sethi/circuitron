# Phase 1: Headless Mode & Boundaries — 08-08-2025

## Summary
Implemented foundational headless support and decoupled backend from terminal UI per `backend_frontend_readiness.md` Phase 1.

Key outcomes:
- Introduced a ProgressSink interface with a NullProgressSink for non-interactive runs.
- Refactored the pipeline to use ProgressSink for all progress/logs and accept an injectable feedback provider.
- Removed blocking prompts from the core pipeline; headless default skips feedback unless provided.
- Made network checks pure (no UI side-effects).
- Kept CLI/Terminal UI working by adapting them to the new interfaces.

## Files changed / added
- Added: `circuitron/progress.py`
  - Defines `ProgressSink` protocol and `NullProgressSink` (no-op).
- Updated: `circuitron/pipeline.py`
  - All `run_*` functions accept `sink: ProgressSink | None` (default `NullProgressSink`).
  - `pipeline()` and `run_with_retry()` accept `sink` and `feedback_provider: Callable[[PlanOutput], UserFeedback] | None`.
  - Removed direct prints/UI; all output routed via sink.
  - Replaced interactive `collect_user_feedback` with `feedback_provider`.
- Updated: `circuitron/utils.py`
  - `validate_code_generation_results` now uses a sink for warnings (no prints).
- Updated: `circuitron/network.py`
  - `check_internet_connection()` is pure; no UI.
- Updated: `circuitron/ui/app.py`
  - `TerminalUI` implements `ProgressSink` and passes `sink=self` to `run_with_retry`.
- Updated: `circuitron/cli.py`
  - Passes `sink=ui` into `run_with_retry`; surfaces connectivity errors via UI.

## Rationale
- Headless/API readiness requires eliminating blocking prompts and direct terminal output.
- ProgressSink formalizes progress and messaging for easy adaptation to web streams (SSE/WebSocket) or logs.
- Feedback is injectable for future web UI to supply edits without blocking.

## Verification status
- Lint/syntax: Valid for changed files. Fixed a try/finally indentation issue in `pipeline.py` during refactor.
- Tests: All pytests pass

## Usage notes
- For headless/API usage, pass a custom `ProgressSink` implementation and an optional `feedback_provider` to `run_with_retry` / `pipeline`.
- CLI remains unchanged for users; it adapts to the ProgressSink automatically via `TerminalUI`.

## Next steps
- Add a Headless/Event sink that buffers/publishes structured events (for SSE/WebSockets).
- Begin Phase 2 (Container concurrency safety) per roadmap.
- Add unit tests for ProgressSink integration and headless feedback paths (mock agents).
