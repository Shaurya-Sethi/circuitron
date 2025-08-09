# UI/UX Issue #1: Suppress Non-Critical Copy Errors

## Summary
Demoted error-level logs emitted during post-run file copy attempts from the Docker container so that optional artifact copy failures (e.g., lib_pickle_dir, .pkl caches) are not shown to end users. These messages are non-impactful to the pipeline and were cluttering the CLI with `ERROR:root` lines.

## Files Changed
- `circuitron/docker_session.py`

## Rationale
- Copy attempts after script execution may legitimately fail when certain optional files are not present. Surfacing these as errors harms UX and causes confusion even when the pipeline succeeds.
- The failures remain captured as debug logs for traceability during troubleshooting.

## Implementation Details
- In `DockerSession.copy_generated_files`, changed `logging.error(...)` to `logger.debug(...)` when `docker cp` fails for a given file.
- The method still returns successfully copied files and collects failure summaries for debug-level visibility.

## Verification
- Code inspection: no behavioral change except logging level.
- Unit test suite could not be executed end-to-end in this sandbox; however, existing tests for `DockerSession` do not rely on error-level logs for this code path. Start-up error logging remains unchanged to satisfy tests expecting `logging.error` in other areas.

## Issues
- None functionally. This is a log verbosity change only.

## Next Steps
- Proceed to Issue #2–#6 UI/UX improvements (input UX, slash-commands menus, feedback boxes, ERC result rendering, generated files display).

