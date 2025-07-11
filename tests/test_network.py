import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

import circuitron.debug as dbg
import circuitron.guardrails as gr


def test_run_agent_handles_network_error(capsys: pytest.CaptureFixture[str]) -> None:
    async def fake_run(*args: Any, **kwargs: Any) -> None:
        import httpx

        raise httpx.RequestError("fail")

    with pytest.raises(RuntimeError):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(dbg.Runner, "run", fake_run)  # type: ignore[attr-defined]
            asyncio.run(dbg.run_agent(SimpleNamespace(name="a"), "x"))
    out = capsys.readouterr().out
    assert "network error" in out.lower()


def test_pcb_guardrail_handles_network_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fake_run(*args: Any, **kwargs: Any) -> None:
        import httpx

        raise httpx.RequestError("fail")

    ctx = SimpleNamespace(context=None)
    with pytest.raises(RuntimeError):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(dbg.Runner, "run", fake_run)  # type: ignore[attr-defined]
            asyncio.run(gr.pcb_query_guardrail.guardrail_function(ctx, None, "x"))  # type: ignore[arg-type]
    out = capsys.readouterr().out
    assert "network error" in out.lower()
