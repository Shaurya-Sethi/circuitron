import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import circuitron.pipeline as pl
from circuitron.models import PlanOutput, PartSelectionOutput, DocumentationOutput, CodeGenerationOutput
from circuitron.progress import NullProgressSink


class WarningSink(NullProgressSink):
    def __init__(self) -> None:
        super().__init__()
        self.warnings: list[str] = []

    def display_warning(self, message: str) -> None:
        self.warnings.append(message)


async def _run_codegen_with_warning() -> WarningSink:
    sink = WarningSink()
    with patch("circuitron.pipeline.run_agent", AsyncMock(return_value=SimpleNamespace(final_output=CodeGenerationOutput(complete_skidl_code="code")))), \
         patch("circuitron.pipeline.validate_code_generation_results", return_value=False):
        await pl.run_code_generation(
            PlanOutput(),
            PartSelectionOutput(),
            DocumentationOutput(research_queries=[], documentation_findings=[], implementation_readiness="ok"),
            sink=sink,
        )
    return sink


def test_run_code_generation_warns() -> None:
    sink = asyncio.run(_run_codegen_with_warning())
    assert any(
        "Basic code checks failed" in msg for msg in sink.warnings
    )
