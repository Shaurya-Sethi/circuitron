import os
import pytest

import circuitron.config as cfg


def test_setup_environment_triggers_onboarding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    called = False

    def fake_onboard() -> None:
        nonlocal called
        called = True
        os.environ.update(
            {
                "OPENAI_API_KEY": "k",
                "SUPABASE_URL": "u",
                "SUPABASE_SERVICE_KEY": "s",
                "NEO4J_URI": "n",
                "NEO4J_USER": "u",
                "NEO4J_PASSWORD": "p",
                "MCP_URL": "http://m",
            }
        )

    monkeypatch.setattr(cfg, "run_onboarding", fake_onboard)
    monkeypatch.setenv("CIRCUITRON_AUTO_ONBOARD", "1")
    cfg.setup_environment()
    assert called


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

