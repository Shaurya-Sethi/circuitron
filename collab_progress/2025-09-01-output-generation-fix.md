Title: Fix final file generation path and preserve prior outputs
Date: 2025-09-01

Summary
- Investigated why no files appear after “Generating Files” stage and why previous outputs vanish.
- Root causes:
  - Final execution mounted the host output directory at a converted path and then copied from `/workspace/*` (which didn’t exist). Also the script didn’t run from the mounted dir, so artifacts were written elsewhere inside the container.
  - `prepare_output_dir()` cleared the output directory on every run, deleting earlier outputs.

Changes
- Do not delete previous outputs:
  - Updated `circuitron/utils.py:prepare_output_dir()` to only create the directory if missing and return its absolute path. Removed file-clearing logic and updated docstring.

- Ensure artifacts are generated and copied from the mounted folder:
  - Updated `circuitron/tools.py:execute_final_script()` to mount the host output directory at `/workspace` inside the container and change directory to `/workspace` at the start of the wrapper script. The copy step now pulls from `/workspace/*` to the host output directory.

Tests
- Added `tests/test_output_generation.py` with two tests:
  - `test_prepare_output_dir_preserves_existing_files` ensures no deletion of prior artifacts.
  - `test_execute_final_script_mounts_workspace_and_copies` monkeypatches `DockerSession` to verify the mount target (`/workspace`), wrapper `chdir`, and that files returned are under the host output dir.

Notes
- Could not run `pytest -q` inside this sandbox (pytest not available). Please run locally:
  1) Activate venv (PowerShell):
     `& C:/Users/shaur/circuitron/circuitron_venv/Scripts/Activate.ps1`
  2) `pytest -q`

Impact
- “Generated Files” should now populate correctly in the UI.
- Old artifacts in `circuitron_output/` are preserved across runs.

Follow-ups
- If name collisions between runs are undesirable, we can add an option to create timestamped subfolders under the chosen output dir (`--run-subdir` flag) while keeping the default behavior non-destructive.
