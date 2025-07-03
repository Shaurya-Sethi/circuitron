import pytest

import circuitron.config as cfg


def test_setup_environment_requires_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MCP_URL", raising=False)
    with pytest.raises(SystemExit) as exc:
        cfg.setup_environment()
    message = str(exc.value)
    for var in ["OPENAI_API_KEY", "MCP_URL"]:
        assert var in message


def test_settings_updated_in_place(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("MCP_URL", "http://a")

    cfg.setup_environment()
    first_id = id(cfg.settings)
    import importlib
    tools = importlib.import_module("circuitron.tools")
    assert tools.settings is cfg.settings

    monkeypatch.setenv("MCP_URL", "http://b")
    cfg.setup_environment()

    assert id(cfg.settings) == first_id
    assert cfg.settings.mcp_url == "http://b"
    assert tools.settings is cfg.settings

