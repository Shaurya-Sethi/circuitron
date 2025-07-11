import subprocess

import circuitron.mcp_server as srv


def test_ensure_running_starts_container(monkeypatch):
    state = {"running": False}
    commands: list[list[str]] = []

    def fake_is_running(_url: str) -> bool:
        return state["running"]

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        if "run" in cmd:
            state["running"] = True
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(srv, "is_running", fake_is_running)
    monkeypatch.setattr(srv, "_run", fake_run)
    monkeypatch.setattr(srv.time, "sleep", lambda *_: None)
    monkeypatch.setattr(srv.atexit, "register", lambda *_a, **_k: None)
    monkeypatch.setenv("PORT", "9999")
    assert srv.ensure_running() is True
    run_cmd = commands[-1]
    idx = run_cmd.index("-p")
    assert run_cmd[idx + 1] == "8051:8051"
    assert "PORT=9999" in run_cmd


def test_start_respects_attempt_env(monkeypatch):
    attempts = {"count": 0}

    def fake_is_running(_url: str) -> bool:
        attempts["count"] += 1
        # become healthy on the fourth check
        return attempts["count"] >= 4

    monkeypatch.setattr(srv, "is_running", fake_is_running)
    monkeypatch.setattr(
        srv, "_run", lambda *_a, **_k: subprocess.CompletedProcess([], 0, "", "")
    )
    monkeypatch.setattr(srv, "_container_status", lambda: None)
    monkeypatch.setattr(srv, "_remove_container", lambda: None)
    monkeypatch.setattr(srv.time, "sleep", lambda *_: None)
    monkeypatch.setattr(srv.atexit, "register", lambda *_a, **_k: None)
    monkeypatch.setenv("MCP_START_MAX_ATTEMPTS", "5")

    assert srv.start() is True
    # one initial check plus three loop iterations
    assert attempts["count"] == 4
