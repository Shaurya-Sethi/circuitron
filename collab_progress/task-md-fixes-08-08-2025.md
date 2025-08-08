# Task.md-driven fixes — 08-08-2025

## Summary
Applied improvements from task.md across progress/pipeline/utils/network/UI/CLI to harden stage lifecycle, headless wiring, and typing. All tests pass.

## Files Changed
- circuitron/progress.py
  - Marked ProgressSink as @runtime_checkable; made NullProgressSink no-ops use `pass`.
- circuitron/pipeline.py
  - Wrapped start_stage/finish_stage with try/finally in all helpers.
  - Removed duplicate plan display from run_planner; display once in pipeline.
  - Act on codegen validation result and improved ERC JSON error readability.
  - Expanded docstrings to include sink and feedback_provider.
- circuitron/utils.py
  - Relaxed print_section typing to Iterable[str]; switched to built-in generics.
- circuitron/network.py
  - Limited __all__ to project utilities only (no httpx re-export).
- circuitron/ui/app.py
  - Wired collect_feedback into run (passed as feedback_provider); keeps sink=self.
- circuitron/cli.py
  - Passes sink=ui and feedback_provider=ui.collect_feedback to run_with_retry.
  - Backward-compatible fallback when test stub doesn't accept extra kwargs.
  - Removed unused ProgressSink import.

## Rationale
- Prevent spinners from hanging on exceptions via try/finally.
- Avoid duplicate plan output. Improve headless readiness and test robustness.
- Better type ergonomics and public API boundaries.

## Verification
- Ran full test suite: 132 passed.
- Manual code review for docstrings and param routing.

## Issues
- None observed.

## Next Steps
- Add unit tests around ProgressSink runtime-checkable behavior and stage lifecycle.
- Consider structured event sink for headless streaming.
