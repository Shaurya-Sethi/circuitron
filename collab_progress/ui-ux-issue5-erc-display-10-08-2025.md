# UI/UX: Human-friendly ERC result display (Issue #5)

Summary
- Replaced raw JSON dump of ERC results with a readable, plain-English summary in the UI.
- Added a formatter that extracts counts and lists of errors/warnings from ERC stdout.
- Created a UI method to render the summary in a titled panel.

Files Changed
- circuitron/utils.py
  - Added `_parse_erc_stdout` helper.
  - Added `format_erc_result(erc_result)` to produce human-friendly text.
- circuitron/ui/app.py
  - Added `display_erc_result()` to show formatted ERC output.
- circuitron/pipeline.py
  - Switched ERC display to use `ui.display_erc_result()`; falls back to JSON only when UI not present.
- tests/test_erc_formatting.py
  - New tests covering pass/no-issues, pass-with-warnings, failure with both, stderr-only failures, and count fallback.
- circuitron/cli.py
  - Minor fix to `setup_environment` call signature to satisfy tests (no functional change to ERC display).

Rationale
- Dumping the raw ERC JSON is noisy and hard to scan. A concise summary with clear bullets improves UX.

Verification
- Ran `pytest -q` in the project venv: all tests passed.
- New tests assert the formatter output contains expected phrasing and bullet lists.

Issues
- None observed. Formatter relies on typical SKiDL/ERC phrasing; it falls back to message counts when summary lines are missing.

Next Steps
- Consider linking each error/warning to quick tips in the UI or docs.
- Optionally add color coding for errors vs warnings within the panel.
