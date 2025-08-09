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


class _DummyUI:
    """Minimal UI stub to verify feedback collection path.

    Provides only the attributes and methods that pipeline() touches directly
    in this test. All methods are no-ops except collect_feedback, which sets
    a flag so we can assert it was used.
    """

    def __init__(self) -> None:
        self.console = Console(force_terminal=False)
        self.collect_called = 0

    # UI surface used in pipeline() - provide minimal no-op implementations
    def display_info(self, _msg: str) -> None:  # pragma: no cover - trivial
        pass

    def display_plan(self, *_a, **_k) -> None:  # pragma: no cover - trivial
        pass

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

    def collect_feedback(self, plan: PlanOutput) -> UserFeedback:
        self.collect_called += 1
        return UserFeedback()


def test_pipeline_uses_ui_collect_feedback() -> None:
    ui = _DummyUI()

    plan = PlanOutput(component_search_queries=["R"], calculation_codes=[])
    plan_result = SimpleNamespace(final_output=plan, new_items=[])
    part_out = PartFinderOutput()
    select_out = PartSelectionOutput()
    doc_out = DocumentationOutput(
        research_queries=[], documentation_findings=[], implementation_readiness="ok"
    )
    code_out = CodeGenerationOutput(complete_skidl_code="ok")
    val_pass_no_erc = (CodeValidationOutput(status="pass", summary="ok"), None)

    async def _run() -> CodeGenerationOutput:
        with patch.object(pl, "run_planner", AsyncMock(return_value=plan_result)), \
             patch.object(pl, "run_part_finder", AsyncMock(return_value=part_out)), \
             patch.object(pl, "run_part_selector", AsyncMock(return_value=select_out)), \
             patch.object(pl, "run_documentation", AsyncMock(return_value=doc_out)), \
            patch.object(pl, "run_code_generation", AsyncMock(return_value=code_out)), \
            patch.object(pl, "run_code_validation", AsyncMock(return_value=val_pass_no_erc)), \
            patch.object(pl, "collect_user_feedback", side_effect=AssertionError("collect_user_feedback should not be called when UI is provided")), \
            patch.object(pl, "execute_final_script", AsyncMock(return_value="{}")):
            return await pl.pipeline("test", ui=ui)

    result = asyncio.run(_run())
    assert isinstance(result, CodeGenerationOutput)
    assert ui.collect_called == 1

