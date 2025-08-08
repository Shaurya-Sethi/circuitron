import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import circuitron.pipeline as pl
from circuitron.models import (
    PlanOutput,
    PartSelectionOutput,
    DocumentationOutput,
    CodeGenerationOutput,
)


def test_run_code_generation_logs_warning() -> None:
    async def run() -> None:
        plan = PlanOutput()
        selection = PartSelectionOutput()
        docs = DocumentationOutput(
            research_queries=[], documentation_findings=[], implementation_readiness="ok"
        )
        code_out = CodeGenerationOutput(complete_skidl_code="code")
        sink = SimpleNamespace(warning=MagicMock())
        with patch("circuitron.pipeline.format_code_generation_input", return_value="x"), \
             patch("circuitron.debug.Runner.run", AsyncMock(return_value=SimpleNamespace(final_output=code_out))), \
             patch("circuitron.pipeline.pretty_print_generated_code"), \
             patch("circuitron.pipeline.validate_code_generation_results", return_value=False):
            await pl.run_code_generation(plan, selection, docs, sink=sink)
        sink.warning.assert_called_once()
    asyncio.run(run())
