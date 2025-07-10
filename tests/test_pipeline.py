import asyncio
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest

from circuitron.models import (
    PlanOutput,
    PlanEditDecision,
    PlanEditorOutput,
    UserFeedback,
    PartFinderOutput,
    PartSelectionOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    CodeValidationOutput,
    CodeCorrectionOutput,
)
from circuitron.correction_context import CorrectionContext
import circuitron.config as cfg
cfg.setup_environment()


async def fake_pipeline_no_feedback() -> None:
    from circuitron import pipeline as pl
    plan = PlanOutput(component_search_queries=["R"], calculation_codes=[])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    code_out = CodeGenerationOutput(complete_skidl_code="")
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(return_value=(CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": True}))), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()), \
         patch.object(pl, "execute_final_script", AsyncMock(return_value="{}")):
        result = await pl.pipeline("test")
    assert result is code_out


async def fake_pipeline_edit_plan() -> None:
    from circuitron import pipeline as pl
    plan = PlanOutput(component_search_queries=["R"], calculation_codes=[])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    edited_plan = PlanOutput(component_search_queries=["C"])
    edit_output = PlanEditorOutput(
        decision=PlanEditDecision(reasoning="ok"),
        updated_plan=edited_plan,
    )
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    code_out = CodeGenerationOutput(complete_skidl_code="")
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback(requested_edits=["x"])), \
         patch.object(pl, "run_plan_editor", AsyncMock(return_value=edit_output)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(return_value=(CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": True}))), \
         patch.object(pl, "execute_final_script", AsyncMock(return_value="{}")):
        result = await pl.pipeline("test")
    assert result is code_out


def test_pipeline_asyncio() -> None:
    asyncio.run(fake_pipeline_no_feedback())
    asyncio.run(fake_pipeline_edit_plan())


def test_parse_args() -> None:
    from circuitron import pipeline as pl
    args = pl.parse_args(["prompt", "-r", "--dev", "-n", "2"])
    assert args.prompt == "prompt"
    assert args.reasoning is True
    assert not hasattr(args, "debug")
    assert args.dev is True
    assert args.retries == 2


def test_run_code_validation_calls_erc() -> None:
    import circuitron.pipeline as pl
    code_out = CodeGenerationOutput(complete_skidl_code="from skidl import *")
    selection = PartSelectionOutput()
    docs = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    val_out = CodeValidationOutput(status="pass", summary="ok")
    with patch("circuitron.debug.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=val_out))):
        with patch("circuitron.pipeline.run_erc", AsyncMock(return_value='{"erc_passed": true}')) as erc_mock, \
             patch("circuitron.pipeline.write_temp_skidl_script", return_value="/tmp/x.py"), \
             patch("circuitron.pipeline.prepare_erc_only_script", return_value="erc"):
            result = asyncio.run(pl.run_code_validation(code_out, selection, docs))
            erc_mock.assert_called_once()
    validation, erc = result
    assert validation.status == "pass"
    assert erc is not None
    assert erc["erc_passed"] is True


def test_run_code_validation_no_erc_on_fail() -> None:
    import circuitron.pipeline as pl
    code_out = CodeGenerationOutput(complete_skidl_code="from skidl import *")
    selection = PartSelectionOutput()
    docs = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    val_out = CodeValidationOutput(status="fail", summary="bad")
    with patch("circuitron.debug.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=val_out))):
        with patch("circuitron.pipeline.run_erc", AsyncMock()) as erc_mock, \
             patch("circuitron.pipeline.write_temp_skidl_script", return_value="/tmp/x.py"), \
             patch("circuitron.pipeline.prepare_erc_only_script", return_value="erc"):
            result = asyncio.run(pl.run_code_validation(code_out, selection, docs))
            erc_mock.assert_not_called()
    validation, erc = result
    assert validation.status == "fail"
    assert erc is None


def test_run_code_validation_skip_erc_flag() -> None:
    import circuitron.pipeline as pl

    code_out = CodeGenerationOutput(complete_skidl_code="from skidl import *")
    selection = PartSelectionOutput()
    docs = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    val_out = CodeValidationOutput(status="pass", summary="ok")

    with patch("circuitron.debug.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=val_out))):
        with patch("circuitron.pipeline.run_erc", AsyncMock()) as erc_mock, \
             patch("circuitron.pipeline.write_temp_skidl_script", return_value="/tmp/x.py"), \
             patch("circuitron.pipeline.prepare_erc_only_script", return_value="erc"):
            result = asyncio.run(pl.run_code_validation(code_out, selection, docs, run_erc_flag=False))
            erc_mock.assert_not_called()
    validation, erc = result
    assert validation.status == "pass"
    assert erc is None


async def fake_pipeline_with_correction() -> None:
    from circuitron import pipeline as pl
    plan = PlanOutput()
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    code_out = CodeGenerationOutput(complete_skidl_code="init")
    corrected = CodeGenerationOutput(complete_skidl_code="fixed")
    val_fail = (CodeValidationOutput(status="fail", summary="bad"), None)
    val_pass = (CodeValidationOutput(status="pass", summary="ok"), None)
    val_warn = (
        CodeValidationOutput(status="pass", summary="ok"),
        {
            "erc_passed": False,
            "stdout": "ERROR: e\n1 errors found during ERC\n1 warnings found during ERC",
        },
    )
    val_ok = (
        CodeValidationOutput(status="pass", summary="ok"),
        {"erc_passed": True, "stdout": "0 errors found during ERC\n0 warnings found during ERC"},
    )
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(
             pl,
             "run_code_validation",
             AsyncMock(side_effect=[val_fail, val_pass, val_warn, val_ok]),
         ), \
         patch.object(
             pl,
             "run_validation_correction",
             AsyncMock(return_value=corrected),
         ), \
         patch.object(
             pl,
             "run_erc_handling",
             AsyncMock(return_value=(corrected, pl.ERCHandlingOutput(
                 final_code="fixed",
                 erc_issues_identified=[],
                 corrections_applied=[],
                 erc_validation_status="pass",
                 remaining_warnings=[],
                 resolution_strategy="",
             ))),
         ), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()), \
         patch.object(pl, "execute_final_script", AsyncMock(return_value="{}")):
        result = await pl.pipeline("test")
    assert result.complete_skidl_code == "fixed"


def test_pipeline_correction_flow() -> None:
    asyncio.run(fake_pipeline_with_correction())



async def fake_pipeline_debug_show() -> None:
    from circuitron import pipeline as pl
    plan = PlanOutput(component_search_queries=["R"], calculation_codes=["print(1)"])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    code_out = CodeGenerationOutput(complete_skidl_code="")
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(return_value=(CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": True}))), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()), \
         patch.object(pl, "execute_final_script", AsyncMock(return_value="{}")):
        pl.settings.dev_mode = True
        result = await pl.pipeline("test", show_reasoning=True)
        pl.settings.dev_mode = False
    assert result is code_out


def test_pipeline_debug_show_flow() -> None:
    asyncio.run(fake_pipeline_debug_show())

async def fake_pipeline_edit_plan_with_correction() -> None:
    from circuitron import pipeline as pl
    plan = PlanOutput(component_search_queries=["R"])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    edited_plan = PlanOutput(component_search_queries=["C"])
    edit_output = PlanEditorOutput(
        decision=PlanEditDecision(reasoning="ok"),
        updated_plan=edited_plan,
    )
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    code_out = CodeGenerationOutput(complete_skidl_code="init")
    corrected = CodeGenerationOutput(complete_skidl_code="fixed")
    val_fail = (CodeValidationOutput(status="fail", summary="bad"), None)
    val_pass = (CodeValidationOutput(status="pass", summary="ok"), None)
    val_ok = (
        CodeValidationOutput(status="pass", summary="ok"),
        {"erc_passed": True, "stdout": "0 errors found during ERC\n0 warnings found during ERC"},
    )
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback(requested_edits=["x"])), \
         patch.object(pl, "run_plan_editor", AsyncMock(return_value=edit_output)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(side_effect=[val_fail, val_pass, val_ok])), \
         patch.object(pl, "run_validation_correction", AsyncMock(return_value=corrected)), \
         patch.object(
             pl,
             "run_erc_handling",
             AsyncMock(return_value=(corrected, pl.ERCHandlingOutput(
                 final_code="fixed",
                 erc_issues_identified=[],
                 corrections_applied=[],
                 erc_validation_status="pass",
                 remaining_warnings=[],
                 resolution_strategy="",
             ))),
         ), \
         patch.object(pl, "execute_final_script", AsyncMock(return_value="{}")):
        result = await pl.pipeline("test")
    assert result.complete_skidl_code == "fixed"



def test_pipeline_edit_plan_with_correction() -> None:
    asyncio.run(fake_pipeline_edit_plan_with_correction())


def test_run_code_validation_cleanup(tmp_path: Path) -> None:
    import circuitron.pipeline as pl

    code_out = CodeGenerationOutput(complete_skidl_code="from skidl import *")
    selection = PartSelectionOutput()
    docs = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    val_out = CodeValidationOutput(status="pass", summary="ok")

    script_path = tmp_path / "temp.py"

    def fake_write_temp(code: str) -> str:
        script_path.write_text(code)
        return str(script_path)

    with patch("circuitron.pipeline.write_temp_skidl_script", side_effect=fake_write_temp), \
         patch("circuitron.pipeline.prepare_erc_only_script", return_value="erc"), \
         patch("circuitron.debug.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=val_out))), \
         patch("circuitron.pipeline.run_erc", AsyncMock(return_value='{"erc_passed": true}')):
        asyncio.run(pl.run_code_validation(code_out, selection, docs))

    assert not script_path.exists()


def test_run_code_correction_cleanup(tmp_path: Path) -> None:
    import circuitron.pipeline as pl

    code_out = CodeGenerationOutput(complete_skidl_code="from skidl import *")
    validation = CodeValidationOutput(status="fail", summary="bad")
    correction_out = CodeCorrectionOutput(corrected_code="fixed", validation_notes="")

    with patch("circuitron.pipeline.write_temp_skidl_script") as write_mock:
        with patch("circuitron.debug.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=correction_out))):
            asyncio.run(
                pl.run_code_correction(
                    code_out,
                    validation,
                    PlanOutput(),
                    PartSelectionOutput(),
                    DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok"),
                )
            )
        write_mock.assert_not_called()


async def fake_run_with_retry_success() -> None:
    from circuitron import pipeline as pl

    async def maybe_fail(prompt: str, show_reasoning: bool = False) -> CodeGenerationOutput:
        if not hasattr(maybe_fail, "called"):
            setattr(maybe_fail, "called", True)
            raise RuntimeError("boom")
        return CodeGenerationOutput(complete_skidl_code="ok")

    with patch.object(pl, "pipeline", AsyncMock(side_effect=maybe_fail)):
        result = await pl.run_with_retry("p", retries=1)
        assert isinstance(result, CodeGenerationOutput)


async def fake_run_with_retry_fail() -> None:
    from circuitron import pipeline as pl

    async def always_fail(prompt: str, show_reasoning: bool = False) -> CodeGenerationOutput:
        raise RuntimeError("x")

    with patch.object(pl, "pipeline", AsyncMock(side_effect=always_fail)):
        result = await pl.run_with_retry("p", retries=1)
        assert result is None


def test_run_with_retry_behaviour() -> None:
    asyncio.run(fake_run_with_retry_success())
    asyncio.run(fake_run_with_retry_fail())


async def fake_pipeline_validation_error() -> None:
    from circuitron import pipeline as pl

    plan = PlanOutput(component_search_queries=["R"])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    code_out = CodeGenerationOutput(complete_skidl_code="bad")
    val_fail = (CodeValidationOutput(status="fail", summary="bad"), None)

    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(return_value=val_fail)), \
         patch.object(pl, "run_validation_correction", AsyncMock(return_value=code_out)), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()):
        with pytest.raises(pl.PipelineError):
            await pl.pipeline("test")


def test_pipeline_validation_failure() -> None:
    asyncio.run(fake_pipeline_validation_error())


async def fake_pipeline_erc_error() -> None:
    from circuitron import pipeline as pl

    plan = PlanOutput(component_search_queries=["R"])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    code_out = CodeGenerationOutput(complete_skidl_code="code")
    val_pass = (CodeValidationOutput(status="pass", summary="ok"), None)
    erc_fail: tuple[CodeValidationOutput, dict[str, object]] = (
        CodeValidationOutput(status="pass", summary="ok"),
        {"erc_passed": False},
    )

    async def fake_validate(*args: object, **_kwargs: object) -> tuple[CodeValidationOutput, dict[str, object] | None]:
        if not hasattr(fake_validate, "called"):
            setattr(fake_validate, "called", True)
            return val_pass
        return erc_fail

    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(side_effect=fake_validate)), \
         patch.object(
             pl,
             "run_erc_handling",
             AsyncMock(return_value=(code_out, pl.ERCHandlingOutput(
                 final_code="code",
                 erc_issues_identified=[],
                 corrections_applied=[],
                 erc_validation_status="fail",
                 remaining_warnings=[],
                 resolution_strategy="",
             ))),
         ), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()):
        with pytest.raises(pl.PipelineError):
            await pl.pipeline("test")


def test_pipeline_erc_failure() -> None:
    asyncio.run(fake_pipeline_erc_error())


async def fake_pipeline_debug_failure(capsys: pytest.CaptureFixture[str]) -> str:
    from circuitron import pipeline as pl

    plan = PlanOutput(component_search_queries=["R"])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    code_out = CodeGenerationOutput(complete_skidl_code="bad")
    val_fail = (CodeValidationOutput(status="fail", summary="bad"), None)

    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(return_value=val_fail)), \
         patch.object(pl, "run_validation_correction", AsyncMock(return_value=code_out)), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()):
        pl.settings.dev_mode = True
        with pytest.raises(pl.PipelineError):
            await pl.pipeline("test")
        pl.settings.dev_mode = False
    return capsys.readouterr().out


def test_pipeline_error_shows_code_in_dev_mode(capsys: pytest.CaptureFixture[str]) -> None:
    out = asyncio.run(fake_pipeline_debug_failure(capsys))
    assert "GENERATED SKiDL CODE" in out

async def fake_pipeline_warning_approval(capsys: pytest.CaptureFixture[str]) -> tuple[CodeGenerationOutput, CorrectionContext | None, int, int, str]:
    from circuitron import pipeline as pl

    class CaptureContext(CorrectionContext):
        instance: "CaptureContext | None" = None

        def __init__(self) -> None:
            super().__init__()
            CaptureContext.instance = self

    plan = PlanOutput()
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    code_out = CodeGenerationOutput(complete_skidl_code="code")

    erc_warn = {
        "erc_passed": True,
        "stdout": "WARNING: w\n0 errors found during ERC\n1 warnings found during ERC",
    }

    val_pass = (CodeValidationOutput(status="pass", summary="ok"), None)
    val_warn = (CodeValidationOutput(status="pass", summary="ok"), erc_warn)

    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
        patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
        patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
        patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
        patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
        patch.object(pl, "run_code_validation", AsyncMock(side_effect=[val_pass, val_warn, val_warn])) as val_mock, \
        patch.object(
            pl,
            "run_erc_handling",
            AsyncMock(return_value=(
                code_out,
                pl.ERCHandlingOutput(
                    final_code="code",
                    erc_issues_identified=[],
                    corrections_applied=["ack"],
                    erc_validation_status="warnings_only",
                    remaining_warnings=["WARNING: w"],
                    resolution_strategy="accept warnings",
                ),
            )),
        ) as erc_mock, \
        patch.object(pl, "collect_user_feedback", return_value=UserFeedback()), \
        patch.object(pl, "execute_final_script", AsyncMock(return_value="{}")), \
        patch.object(pl, "CorrectionContext", CaptureContext):
        result = await pl.pipeline("test")
        context = CaptureContext.instance
    out = capsys.readouterr().out
    return result, context, val_mock.await_count, erc_mock.await_count, out


def test_erc_warning_approval_breaks_loop(capsys: pytest.CaptureFixture[str]) -> None:
    result, ctx, val_calls, erc_calls, out = asyncio.run(
        fake_pipeline_warning_approval(capsys)
    )
    assert result.complete_skidl_code == "code"
    assert erc_calls == 1
    assert val_calls == 3
    assert "Agent approved warnings as acceptable" in out
    assert ctx is not None
    assert ctx.erc_issues_history[-1]["warnings"]

