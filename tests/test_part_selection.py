import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import circuitron.config as cfg

from circuitron.models import (
    PlanOutput,
    PartFinderOutput,
    PartSelectionOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    CodeValidationOutput,
    PlanEditDecision,
    PlanEditorOutput,
    UserFeedback,
)
cfg.setup_environment()


async def fake_pipeline_no_feedback() -> None:
    import circuitron.pipeline as pl
    plan = PlanOutput(component_search_queries=["R"])
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
    import circuitron.pipeline as pl
    plan = PlanOutput(component_search_queries=["R"])
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
