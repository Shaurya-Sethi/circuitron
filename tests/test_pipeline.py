import asyncio
from types import SimpleNamespace
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
)
import circuitron.config as cfg
cfg.setup_environment()


async def fake_pipeline_no_feedback():
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


async def fake_pipeline_edit_plan():
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


def test_pipeline_asyncio():
    asyncio.run(fake_pipeline_no_feedback())
    asyncio.run(fake_pipeline_edit_plan())


def test_parse_args():
    from circuitron import pipeline as pl
    args = pl.parse_args(["prompt", "-r", "-d"])
    assert args.prompt == "prompt"
    assert args.reasoning is True
    assert args.debug is True


def test_run_code_validation_calls_erc():
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
    assert erc["erc_passed"] is True


def test_run_code_validation_no_erc_on_fail():
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


async def fake_pipeline_with_correction():
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


def test_pipeline_correction_flow():
    asyncio.run(fake_pipeline_with_correction())


