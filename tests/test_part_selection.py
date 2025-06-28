import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import circuitron.config as cfg
cfg.setup_environment()

from circuitron.models import (
    PlanOutput,
    PartFinderOutput,
    PartSelectionOutput,
    PlanEditDecision,
    PlanEditorOutput,
    UserFeedback,
)
import circuitron.pipeline as pl


async def fake_pipeline_no_feedback():
    plan = PlanOutput(component_search_queries=["R"])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback()):
        result = await pl.pipeline("test")
    assert result is select_out


async def fake_pipeline_edit_plan():
    plan = PlanOutput(component_search_queries=["R"])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    edited_plan = PlanOutput(component_search_queries=["C"])
    edit_output = PlanEditorOutput(
        decision=PlanEditDecision(action="edit_plan", reasoning="ok"),
        updated_plan=edited_plan,
    )
    part_out = PartFinderOutput(found_components_json="[]")
    select_out = PartSelectionOutput()
    with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
         patch.object(pl, "collect_user_feedback", return_value=UserFeedback(requested_edits=["x"])), \
         patch.object(pl, "run_plan_editor", AsyncMock(return_value=edit_output)), \
         patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
         patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)):
        result = await pl.pipeline("test")
    assert result is select_out


def test_pipeline_asyncio():
    asyncio.run(fake_pipeline_no_feedback())
    asyncio.run(fake_pipeline_edit_plan())

