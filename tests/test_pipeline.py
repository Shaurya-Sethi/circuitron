import asyncio
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

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
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()):
        result = await pl.pipeline("test")
    assert result is code_out


async def fake_pipeline_edit_plan() -> None:
    from circuitron import pipeline as pl
    plan = PlanOutput(component_search_queries=["R"], calculation_codes=[])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    edited_plan = PlanOutput(component_search_queries=["C"])
    edit_output = PlanEditorOutput(
        decision=PlanEditDecision(action="edit_plan", reasoning="ok"),
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
         patch.object(pl, "run_code_validation", AsyncMock(return_value=(CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": True}))):
        result = await pl.pipeline("test")
    assert result is code_out


def test_pipeline_asyncio() -> None:
    asyncio.run(fake_pipeline_no_feedback())
    asyncio.run(fake_pipeline_edit_plan())


def test_parse_args() -> None:
    from circuitron import pipeline as pl
    args = pl.parse_args(["prompt", "-r", "-d", "-n", "2"])
    assert args.prompt == "prompt"
    assert args.reasoning is True
    assert args.debug is True
    assert args.retries == 2


def test_run_code_validation_calls_erc() -> None:
    import circuitron.pipeline as pl
    code_out = CodeGenerationOutput(complete_skidl_code="from skidl import *")
    selection = PartSelectionOutput()
    docs = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    val_out = CodeValidationOutput(status="pass", summary="ok")
    with patch("circuitron.pipeline.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=val_out))):
        with patch("circuitron.pipeline.run_erc", AsyncMock(return_value='{"erc_passed": true}')) as erc_mock, \
             patch("circuitron.pipeline.write_temp_skidl_script", return_value="/tmp/x.py"):
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
    with patch("circuitron.pipeline.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=val_out))):
        with patch("circuitron.pipeline.run_erc", AsyncMock()) as erc_mock, \
             patch("circuitron.pipeline.write_temp_skidl_script", return_value="/tmp/x.py"):
            result = asyncio.run(pl.run_code_validation(code_out, selection, docs))
            erc_mock.assert_not_called()
    validation, erc = result
    assert validation.status == "fail"
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
    val_warn = (CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": False})
    val_ok = (CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": True})
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(side_effect=[val_fail, val_warn, val_ok])), \
         patch.object(pl, "run_code_correction", AsyncMock(return_value=corrected)), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()):
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
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()):
        result = await pl.pipeline("test", show_reasoning=True, debug=True)
    assert result is code_out


def test_pipeline_debug_show_flow() -> None:
    asyncio.run(fake_pipeline_debug_show())

async def fake_pipeline_edit_plan_with_correction() -> None:
    from circuitron import pipeline as pl
    plan = PlanOutput(component_search_queries=["R"])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    edited_plan = PlanOutput(component_search_queries=["C"])
    edit_output = PlanEditorOutput(
        decision=PlanEditDecision(action="edit_plan", reasoning="ok"),
        updated_plan=edited_plan,
    )
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    code_out = CodeGenerationOutput(complete_skidl_code="init")
    corrected = CodeGenerationOutput(complete_skidl_code="fixed")
    val_fail = (CodeValidationOutput(status="fail", summary="bad"), None)
    val_ok = (CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": True})
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback(requested_edits=["x"])), \
         patch.object(pl, "run_plan_editor", AsyncMock(return_value=edit_output)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(side_effect=[val_fail, val_ok])), \
         patch.object(pl, "run_code_correction", AsyncMock(return_value=corrected)):
        result = await pl.pipeline("test")
    assert result.complete_skidl_code == "fixed"


def test_pipeline_edit_plan_with_correction() -> None:
    asyncio.run(fake_pipeline_edit_plan_with_correction())

async def fake_pipeline_regen_with_correction() -> None:
    from circuitron import pipeline as pl
    plan = PlanOutput()
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    regen_plan = PlanOutput()
    regen_result = SimpleNamespace(final_output=regen_plan, new_items=[])
    edit_output = PlanEditorOutput(
        decision=PlanEditDecision(action="regenerate_plan", reasoning="r"),
        reconstructed_prompt="again",
    )
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok")
    code_out = CodeGenerationOutput(complete_skidl_code="init")
    corrected = CodeGenerationOutput(complete_skidl_code="fixed")
    val_fail = (CodeValidationOutput(status="fail", summary="bad"), None)
    val_ok = (CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": True})
    with patch.object(pl, "run_planner", AsyncMock(side_effect=[plan_result, regen_result])), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback(requested_edits=["x"])), \
         patch.object(pl, "run_plan_editor", AsyncMock(return_value=edit_output)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
         patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
         patch.object(pl, "run_code_validation", AsyncMock(side_effect=[val_fail, val_ok])), \
         patch.object(pl, "run_code_correction", AsyncMock(return_value=corrected)):
        result = await pl.pipeline("test")
    assert result.complete_skidl_code == "fixed"


def test_pipeline_regen_with_correction() -> None:
    asyncio.run(fake_pipeline_regen_with_correction())


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

    with patch("circuitron.pipeline.write_temp_skidl_script", side_effect=fake_write_temp):
        with patch("circuitron.pipeline.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=val_out))):
            with patch("circuitron.pipeline.run_erc", AsyncMock(return_value='{"erc_passed": true}')):
                asyncio.run(pl.run_code_validation(code_out, selection, docs))

    assert not script_path.exists()


def test_run_code_correction_cleanup(tmp_path: Path) -> None:
    import circuitron.pipeline as pl

    code_out = CodeGenerationOutput(complete_skidl_code="from skidl import *")
    validation = CodeValidationOutput(status="fail", summary="bad")
    correction_out = CodeCorrectionOutput(corrected_code="fixed", validation_notes="")

    script_path = tmp_path / "temp.py"

    def fake_write_temp(code: str) -> str:
        script_path.write_text(code)
        return str(script_path)

    with patch("circuitron.pipeline.write_temp_skidl_script", side_effect=fake_write_temp):
        with patch("circuitron.pipeline.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=correction_out))):
            asyncio.run(pl.run_code_correction(code_out, validation))

    assert not script_path.exists()


async def fake_run_with_retry_success() -> None:
    from circuitron import pipeline as pl

    async def maybe_fail(prompt: str, show_reasoning: bool = False, debug: bool = False) -> CodeGenerationOutput:
        if not hasattr(maybe_fail, "called"):
            setattr(maybe_fail, "called", True)
            raise RuntimeError("boom")
        return CodeGenerationOutput(complete_skidl_code="ok")

    with patch.object(pl, "pipeline", AsyncMock(side_effect=maybe_fail)):
        result = await pl.run_with_retry("p", retries=1)
        assert isinstance(result, CodeGenerationOutput)


async def fake_run_with_retry_fail() -> None:
    from circuitron import pipeline as pl

    async def always_fail(prompt: str, show_reasoning: bool = False, debug: bool = False) -> CodeGenerationOutput:
        raise RuntimeError("x")

    with patch.object(pl, "pipeline", AsyncMock(side_effect=always_fail)):
        result = await pl.run_with_retry("p", retries=1)
        assert result is None


def test_run_with_retry_behaviour() -> None:
    asyncio.run(fake_run_with_retry_success())
    asyncio.run(fake_run_with_retry_fail())
