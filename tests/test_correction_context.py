from circuitron.correction_context import CorrectionContext
from circuitron.models import CodeValidationOutput, ValidationIssue


def test_correction_context_basic() -> None:
    ctx = CorrectionContext(max_attempts=2)
    val = CodeValidationOutput(status="fail", summary="bad")
    ctx.add_validation_attempt(val, ["try1"])
    assert ctx.validation_attempts == 1
    assert ctx.should_continue_attempts()
    ctx.add_validation_attempt(val, ["try2"])
    assert not ctx.should_continue_attempts()


def test_context_formatting() -> None:
    ctx = CorrectionContext()
    val = CodeValidationOutput(
        status="fail",
        summary="bad",
        issues=[ValidationIssue(category="err", message="m", line=1)],
    )
    ctx.add_validation_attempt(val, [])
    text = ctx.get_context_for_next_attempt()
    assert "validation" in text and "err" in text


def test_erc_summary_and_issue_tracking() -> None:
    ctx = CorrectionContext()
    erc = {"erc_passed": False, "stdout": "ERC WARNING: w\nERC ERROR: e"}
    ctx.add_erc_attempt(erc, ["fix1"])
    summary = ctx.get_erc_summary_for_agent()
    assert "Attempt 1" in summary
    assert "WARNING: w" in summary
    assert ctx.erc_issue_types["WARNING"] == 1
