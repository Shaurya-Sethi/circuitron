import asyncio
from types import SimpleNamespace

import pytest

import circuitron.debug as dbg


def test_run_agent_handles_network_error(capsys: pytest.CaptureFixture[str]) -> None:
    async def fake_run(*args, **kwargs):
        import httpx

        raise httpx.RequestError("fail")

    with pytest.raises(RuntimeError):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(dbg.Runner, "run", fake_run)
            asyncio.run(dbg.run_agent(SimpleNamespace(name="a"), "x"))
    out = capsys.readouterr().out
    assert "network error" in out.lower()
