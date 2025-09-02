import builtins
from types import SimpleNamespace

import pytest


def test_verify_mcp_server_true_when_available(monkeypatch):
    from circuitron import network as net

    monkeypatch.setattr(net, "is_mcp_server_available", lambda *a, **k: True)
    # Should not need a UI; should return True directly
    assert net.verify_mcp_server() is True


def test_verify_mcp_server_false_when_down(monkeypatch):
    from circuitron import network as net

    messages = []

    class DummyUI:
        def display_error(self, msg: str) -> None:
            messages.append(msg)

    monkeypatch.setattr(net, "is_mcp_server_available", lambda *a, **k: False)
    monkeypatch.setattr(net, "detect_running_mcp_docker_container", lambda: False)
    ok = net.verify_mcp_server(ui=DummyUI())
    assert ok is False
    assert any("MCP server is not running" in m for m in messages)
    assert any("docker run" in m for m in messages)


def test_verify_mcp_server_warns_when_container_present(monkeypatch):
    from circuitron import network as net

    captured = SimpleNamespace(msg="")

    class DummyUI:
        def display_error(self, msg: str) -> None:
            captured.msg = msg

    monkeypatch.setattr(net, "is_mcp_server_available", lambda *a, **k: False)
    monkeypatch.setattr(net, "detect_running_mcp_docker_container", lambda: True)
    assert net.verify_mcp_server(ui=DummyUI()) is False
    assert "detected but not responding" in captured.msg
    assert "docker run" in captured.msg

