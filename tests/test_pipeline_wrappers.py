import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from typing import cast
import pytest

import circuitron.pipeline as pl
from circuitron.models import (
    PlanOutput,
    PlanEditDecision,
    PlanEditorOutput,
    UserFeedback,
    CodeCorrectionOutput,
    PartFinderOutput,
    PartSelectionOutput,
    DocumentationOutput,
    CodeGenerationOutput,
    CodeValidationOutput,
)


async def run_wrappers() -> None:
    with patch("circuitron.pipeline.run_erc", AsyncMock(return_value="{}")), \
         patch("circuitron.debug.Runner.run", AsyncMock()) as run_mock:
        run_mock.return_value = SimpleNamespace(final_output=PlanOutput())
        await pl.run_planner("p")
        assert run_mock.await_args is not None
        called_agent = run_mock.await_args.args[0]
        assert called_agent.name == "Circuitron-Planner"
        run_mock.assert_awaited()
        run_mock.reset_mock()

        run_mock.return_value = SimpleNamespace(final_output=PlanEditorOutput(decision=PlanEditDecision(reasoning="x"), updated_plan=PlanOutput()))
        await pl.run_plan_editor("p", PlanOutput(), UserFeedback())
        run_mock.reset_mock()

        run_mock.return_value = SimpleNamespace(final_output=PartFinderOutput(found_components={}))
        await pl.run_part_finder(PlanOutput(component_search_queries=["Q"]))
        run_mock.reset_mock()

        run_mock.return_value = SimpleNamespace(final_output=PartSelectionOutput())
        await pl.run_part_selector(PlanOutput(), PartFinderOutput(found_components={}))
        run_mock.reset_mock()

        run_mock.return_value = SimpleNamespace(final_output=DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok"))
        await pl.run_documentation(PlanOutput(), PartSelectionOutput())
        run_mock.reset_mock()

        run_mock.return_value = SimpleNamespace(final_output=CodeGenerationOutput(complete_skidl_code="code"))
        await pl.run_code_generation(PlanOutput(), PartSelectionOutput(), DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok"))
        run_mock.reset_mock()

        run_mock.return_value = SimpleNamespace(final_output=CodeValidationOutput(status="pass", summary="ok"))
        await pl.run_code_validation(
            CodeGenerationOutput(complete_skidl_code="code"),
            PartSelectionOutput(),
            DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok"),
        )
        run_mock.reset_mock()

        run_mock.return_value = SimpleNamespace(final_output=CodeCorrectionOutput(corrected_code="fixed", validation_notes=""))
        await pl.run_validation_correction(
            CodeGenerationOutput(complete_skidl_code="code"),
            CodeValidationOutput(status="fail", summary="bad"),
            PlanOutput(),
            PartSelectionOutput(),
            DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok"),
            pl.CorrectionContext(),
        )
        run_mock.reset_mock()

        run_mock.return_value = SimpleNamespace(
            final_output=pl.ERCHandlingOutput(
                final_code="fixed",
                erc_issues_identified=[],
                corrections_applied=[],
                erc_validation_status="pass",
                remaining_warnings=[],
                resolution_strategy="",
            )
        )
        await pl.run_erc_handling(
            CodeGenerationOutput(complete_skidl_code="code"),
            CodeValidationOutput(status="pass", summary="ok"),
            PlanOutput(),
            PartSelectionOutput(),
            DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok"),
            {},
            pl.CorrectionContext(),
        )


def test_wrapper_functions() -> None:
    asyncio.run(run_wrappers())


def test_pipeline_main(monkeypatch: pytest.MonkeyPatch) -> None:
    args = SimpleNamespace(prompt="p", reasoning=False, retries=1, dev=False, output_dir=None)
    monkeypatch.setattr(pl, "parse_args", lambda _=None: args)
    monkeypatch.setattr(pl, "run_with_retry", AsyncMock())
    monkeypatch.setattr(pl, "check_internet_connection", lambda: False)
    asyncio.run(pl.main())
    cast(AsyncMock, pl.run_with_retry).assert_not_awaited()

    # Now with connection available
    monkeypatch.setattr(pl, "check_internet_connection", lambda: True)
    asyncio.run(pl.main())
    cast(AsyncMock, pl.run_with_retry).assert_awaited_with(
        "p",
        show_reasoning=False,
        retries=1,
        output_dir=None,
    )
