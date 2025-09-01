from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from rich.console import Console

import circuitron.pipeline as pl
from circuitron.models import (
    PlanOutput,
    UserFeedback,
    PartFinderOutput,
    PartSelectionOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    CodeValidationOutput,
)


class _CountPlanUI:
    """Minimal UI to count plan renderings during the pipeline."""

    def __init__(self) -> None:
        self.console = Console(force_terminal=False)
        self.plan_renders = 0

    # Methods used by pipeline
    def display_info(self, _msg: str) -> None:  # pragma: no cover - trivial
        pass

    def display_plan(self, *_a, **_k) -> None:
        self.plan_renders += 1

    def display_found_parts(self, *_a, **_k) -> None:  # pragma: no cover - trivial
        pass

    def display_selected_parts(self, *_a, **_k) -> None:  # pragma: no cover - trivial
        pass

    def display_validation_summary(self, *_a, **_k) -> None:  # pragma: no cover - trivial
        pass

    def display_files(self, *_a, **_k) -> None:  # pragma: no cover - trivial
        pass

    def start_stage(self, *_a, **_k) -> None:  # pragma: no cover - trivial
        pass

    def finish_stage(self, *_a, **_k) -> None:  # pragma: no cover - trivial
        pass

    def collect_feedback(self, _plan: PlanOutput) -> UserFeedback:
        # No edits -> follow no-feedback path
        return UserFeedback()


def test_initial_plan_displayed_once() -> None:
    ui = _CountPlanUI()

    plan = PlanOutput(component_search_queries=["R"], calculation_codes=[])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput()
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    code_out = CodeGenerationOutput(complete_skidl_code="from skidl import *\n")
    val_pass = (CodeValidationOutput(status="pass", summary="ok"), {"erc_passed": True})

    async def _run() -> pl.CodeGenerationOutput:
        with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
             patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
             patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
             patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
             patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
             patch.object(pl, "run_code_validation", AsyncMock(side_effect=[val_pass, val_pass, val_pass])), \
             patch.object(pl, "execute_final_script", AsyncMock(return_value="{}")):
            return await pl.pipeline("buck converter", ui=ui)

    result = asyncio.run(_run())
    assert isinstance(result, CodeGenerationOutput)
    # Should render exactly once after planning
    assert ui.plan_renders == 1

