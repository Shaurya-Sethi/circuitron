# UI/UX: End-of-run Summary Stats (Time, Tokens, Cost)

Date: 2025-08-10
Author: automated agent

## Summary
- Adds a final "Run Summary" box to the Terminal UI on every exit path (success or early exit). Includes:
  - Time taken (HH:MM:SS.ss)
  - Token totals (input, output, total) aggregated from Logfire/OTel spans
  - Estimated cost (USD) based on local-only price table
  - Footer: "Circuitron powering down..."
- Preserves existing Logfire tracing UI/behavior during execution.

## Implementation Notes
- Telemetry: `circuitron/telemetry.py`
  - `TokenUsageAggregator` to aggregate tokens (overall + per model)
  - `TokenUsageSpanProcessor` attached in `config.setup_environment()`; extracts `gen_ai.usage.*` attributes (per context7 Logfire docs)
- Cost estimation: `circuitron/cost_estimator.py`
  - Loads optional `circuitron/_model_prices_local.py` (gitignored)
  - Computes cost per model as (tokens/1e6) * rate
- UI integration: `TerminalUI.run()` now resets aggregator and measures elapsed time; always renders summary panel in finally.
- CLI fallback: `pipeline.main()` prints a plaintext summary when UI is not active.
- .gitignore updated to exclude local pricing file.

## Tests
- `tests/test_cost_and_telemetry.py`
  - Aggregator math
  - Estimator with and without local prices

## References
- Logfire GenAI attributes via context7 MCP:
  - gen_ai.usage.input_tokens / output_tokens / total_tokens
  - gen_ai.request.model

## Follow-ups
- Optional: detailed per-model breakdown panel
- Optional: per-agent stage breakdown if runner exposes per-call spans in an accessible way
