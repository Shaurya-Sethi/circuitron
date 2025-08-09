from __future__ import annotations

from circuitron.utils import format_erc_result


def test_erc_pass_no_issues() -> None:
    text = format_erc_result({
        "success": True,
        "erc_passed": True,
        "stdout": "0 errors found during ERC\n0 warnings found during ERC",
        "stderr": "",
    })
    assert "passed" in text.lower()
    assert "no errors or warnings" in text.lower()


def test_erc_pass_with_warnings_lists_messages() -> None:
    text = format_erc_result({
        "success": True,
        "erc_passed": True,
        "stdout": "WARNING: net is floating\n1 warnings found during ERC\n0 errors found during ERC",
        "stderr": "",
    })
    assert "passed with 1 warning" in text.lower()
    assert "- WARNING: net is floating" in text


def test_erc_failed_with_errors_and_warnings() -> None:
    text = format_erc_result({
        "success": True,
        "erc_passed": False,
        "stdout": "ERROR: unconnected pin\nWARNING: label mismatch\n1 errors found during ERC\n1 warnings found during ERC",
        "stderr": "",
    })
    assert "completed with 1 error and 1 warning" in text.lower()
    assert "- ERROR: unconnected pin" in text
    assert "- WARNING: label mismatch" in text


def test_erc_run_failed_shows_stderr() -> None:
    text = format_erc_result({
        "success": False,
        "erc_passed": False,
        "stdout": "",
        "stderr": "Traceback: some error",
    })
    assert "did not run successfully" in text.lower()
    assert "traceback" in text.lower()


def test_erc_counts_fallback_when_no_summary_lines() -> None:
    text = format_erc_result({
        "success": True,
        "erc_passed": False,
        "stdout": "ERROR: E1\nWARNING: W1",
        "stderr": "",
    })
    assert "completed with 1 error and 1 warning" in text.lower()
