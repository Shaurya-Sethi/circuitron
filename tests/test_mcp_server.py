import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import circuitron.mcp_server as srv


def test_ensure_running_starts_container(monkeypatch):
    state = {"running": False}

    def fake_is_running(_url: str) -> bool:
        return state["running"]

    def fake_run(cmd, **kwargs):
        if "run" in cmd:
            state["running"] = True
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(srv, "is_running", fake_is_running)
    monkeypatch.setattr(srv, "_run", fake_run)
    monkeypatch.setattr(srv.time, "sleep", lambda *_: None)
    monkeypatch.setattr(srv.atexit, "register", lambda *_a, **_k: None)
    assert srv.ensure_running() is True
