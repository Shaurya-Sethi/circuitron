Summary: Ensure spinner coverage for all stages, including plan revision and final file generation

Changes made
- Pipeline: Pass `ui` into `run_plan_editor` so the "Editing" spinner appears during plan revision after feedback.
- Pipeline: Pass `ui` into `run_erc_handling` in the no-feedback branch to show the "ERC Handling" spinner during ERC correction loops.
- Pipeline: Wrap `execute_final_script(...)` in a new UI stage named "Generating Files" (start/finish) so users see a spinner while KiCad files are produced.

Files modified
- circuitron/pipeline.py

Rationale
- Users reported no spinner during plan revision. Root cause was missing `ui` propagation in the call to `run_plan_editor` in one branch of the pipeline.
- ERC handling spinner was inconsistent across branches; added `ui` to the no-feedback path.
- Final generation step previously displayed outputs only after completion; spinner improves perceived responsiveness.

Testing notes
- Local environment did not have Python/pytest available in this session to run the test suite.
- The changes are isolated to argument wiring and new stage wrappers and should be low risk.
- Recommended: run `pytest -q` in the project venv on the target machine to confirm no regressions.

Next ideas
- Consider a unified Progress/Stage manager to collect timing metrics per stage and render a summary table.
- Add explicit stage coverage tests by stubbing UI and asserting start/finish calls for each pipeline phase.
