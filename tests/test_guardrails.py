import asyncio
from unittest.mock import AsyncMock

import pytest

import circuitron.debug as dbg
from circuitron.agents import get_planning_agent
from circuitron.guardrails import pcb_query_guardrail, PCBQueryOutput
from circuitron.exceptions import PipelineError
from agents.guardrail import GuardrailFunctionOutput


def test_non_pcb_prompt_triggers_guardrail(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    mock_guardrail = AsyncMock(
        return_value=GuardrailFunctionOutput(
            output_info=PCBQueryOutput(is_relevant=False, reasoning="no"),
            tripwire_triggered=True,
        )
    )
    monkeypatch.setattr(pcb_query_guardrail, "guardrail_function", mock_guardrail)

    with pytest.raises(PipelineError):
        asyncio.run(dbg.run_agent(get_planning_agent(), "Tell me a joke"))

    mock_guardrail.assert_awaited_once()
    out = capsys.readouterr().out
    assert "only assist" in out.lower()


def test_guardrail_network_failure(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    async def raise_network(*_a, **_k):
        import httpx

        raise httpx.RequestError("fail")

    monkeypatch.setattr(dbg.Runner, "run", raise_network)
    with pytest.raises(PipelineError):
        asyncio.run(dbg.run_agent(get_planning_agent(), "design"))
    out = capsys.readouterr().out
    assert "network error" in out.lower()
