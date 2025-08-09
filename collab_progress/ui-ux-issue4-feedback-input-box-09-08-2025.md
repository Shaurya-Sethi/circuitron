Title: UI/UX — Feedback stage uses boxed input (Issue #4)
Date: 2025-08-09

Summary
- Fixed the feedback collection path so the user answers open questions, edits, and additional requirements inside the new boxed input UI rather than typing beside raw labels.
- Root cause: pipeline bypassed the UI’s `collect_feedback` and called the plain `utils.collect_user_feedback` directly.
- Fixed a runtime warning from prompt_toolkit by avoiding synchronous PromptSession.prompt under an active asyncio event loop; we now render a boxed Rich fallback and use input() in that context.

Changes
- `circuitron/pipeline.py`: Delegate to `ui.collect_feedback(plan)` when a UI is provided; fall back to `utils.collect_user_feedback` in non-UI contexts.
- `tests/test_feedback_ui.py` (new): Verifies that when a UI is supplied, `UI.collect_feedback` is called and the plain function is not.
- `circuitron/ui/components/input_box.py`: Detect running event loop and switch to a Rich-rendered boxed input() fallback to prevent `Application.run_async was never awaited` warnings during async pipeline stages.

Rationale
- Ensures a consistent, polished UX: the same boxed input component is used across all prompts, including the iterative Edit #n and Additional requirement #n stages.

Verification
- Added a unit test that stubs the pipeline phases and asserts `UI.collect_feedback` is invoked (and `collect_user_feedback` is not) when a UI is passed to `pipeline()`.
- Sandbox cannot run pytest here; please run `pytest -q` locally in the activated venv.

Known Issues / Notes
- Some panel calls in the pipeline reference a `theme` argument that the current panel helper does not accept. These code paths are patched out in tests; consider aligning signatures in a follow-up.

Next Steps
- Optional: Provide a multiline variant in `InputBox` for longer edits and requirements, terminating on a blank line.
