Title: UI Generated Files — show only current-session artifacts
Date: 2025-09-01

Summary
- Fixed the UI bug where the “Generated Files” table showed artifacts from prior runs (e.g., old LED files alongside new boost_converter outputs).
- Now, only files created or modified during the current final-execution session are returned to the UI and displayed.

Files Changed
- circuitron/tools.py: execute_final_script()
  - Snapshot existing files in the output directory (names + SHA-256 hash) before running.
  - After copying potential artifacts from the container, diff the directory and return only new/changed files.
  - Removed leftover references to a deleted variable and ensured consistent JSON responses across branches.
- tests/test_output_generation.py
  - Added test_execute_final_script_filters_preexisting_files to verify prior artifacts are not reported back.

Rationale
- Preserving older results on disk is useful, but the UI should display only the current run’s artifacts to avoid confusion.
- Hash-based comparison ensures we include files that are regenerated with the same filename but different content.

Verification
- Unit tests updated/added:
  - Existing test for mount + copy remains valid.
  - New test asserts preexisting files are filtered out and only new outputs are listed.
- Local environment note: The sandbox lacks pytest; please run in the project venv:
  - PowerShell: `& C:/Users/shaur/circuitron/circuitron_venv/Scripts/Activate.ps1`
  - `pytest -q`

Issues
- Hashing reads file contents; for very large artifacts this has a minor cost. Acceptable for current artifact sizes. If needed, we can switch to (size, mtime) heuristics.

Next Steps
- Optional: Add a CLI flag to group each run into a timestamped subfolder under the output dir and automatically focus the UI on that folder’s contents.

