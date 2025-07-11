import asyncio
from types import SimpleNamespace
from typing import Any
import socket

import pytest

import circuitron.debug as dbg
import circuitron.guardrails as gr
import circuitron.network as net
from circuitron.exceptions import PipelineError


def test_run_agent_handles_network_error(capsys: pytest.CaptureFixture[str]) -> None:
    async def fake_run(*args: Any, **kwargs: Any) -> None:
        import httpx

        raise httpx.RequestError("fail")

    with pytest.raises(PipelineError):
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
    with pytest.raises(PipelineError):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(dbg.Runner, "run", fake_run)  # type: ignore[attr-defined]
            asyncio.run(gr.pcb_query_guardrail.guardrail_function(ctx, None, "x"))  # type: ignore[arg-type]
    out = capsys.readouterr().out
    assert "network error" in out.lower()


def test_is_connected_handles_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        net.httpx,
        "head",
        lambda *_a, **_k: (_ for _ in ()).throw(net.httpx.RequestError("fail")),
    )
    assert net.is_connected() is False

    def raise_gai(*_a: Any, **_k: Any) -> None:
        raise socket.gaierror

    monkeypatch.setattr(net.httpx, "head", raise_gai)
    assert net.is_connected() is False

