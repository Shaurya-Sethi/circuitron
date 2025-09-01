# Fix: Prevent duplicate plan rendering in terminal

## Summary
Design plan content was displayed twice in the terminal UI: once inside `run_planner()` and again in `pipeline()` immediately after planning. A similar duplicate occurred after the plan editor. This change centralizes plan rendering in `pipeline()` to avoid duplication.

## Files Changed
- `circuitron/pipeline.py`
- `tests/test_plan_display_once.py` (new)

## Rationale
- `run_planner()` and `run_plan_editor()` should focus on execution and stage lifecycles, not on rendering results. The high-level `pipeline()` orchestrator is the appropriate place to render.
- Aligns with existing patterns where validation/code rendering are already handled within their respective functions or at the orchestration layer, but avoids double UI updates for planning.

## Verification
- Added `tests/test_plan_display_once.py` which provides a stub UI and asserts the plan is rendered exactly once during the initial planning flow.
- All tests pass.

## Issues
- None known. If other UI render calls exist in helper layers, they should remain unless they cause user-visible duplication.

## Next Steps
- If desired, add similar single-responsibility checks for other stages to ensure no redundancy between `run_*` helpers and `pipeline()`.

