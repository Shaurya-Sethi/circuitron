import pytest

import circuitron.config as cfg


def test_setup_environment_requires_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PLANNING_MODEL", raising=False)
    monkeypatch.delenv("PLAN_EDIT_MODEL", raising=False)
    monkeypatch.delenv("PART_FINDER_MODEL", raising=False)
    monkeypatch.delenv("MCP_URL", raising=False)
    with pytest.raises(SystemExit) as exc:
        cfg.setup_environment()
    message = str(exc.value)
    for var in [
        "OPENAI_API_KEY",
        "PLANNING_MODEL",
        "PLAN_EDIT_MODEL",
        "PART_FINDER_MODEL",
        "MCP_URL",
    ]:
        assert var in message


def test_settings_updated_in_place(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("PLANNING_MODEL", "p1")
    monkeypatch.setenv("PLAN_EDIT_MODEL", "e1")
    monkeypatch.setenv("PART_FINDER_MODEL", "f1")
    monkeypatch.setenv("MCP_URL", "http://a")

    cfg.setup_environment()
    first_id = id(cfg.settings)
    import importlib
    tools = importlib.import_module("circuitron.tools")
    assert tools.settings is cfg.settings

    monkeypatch.setenv("PLANNING_MODEL", "p2")
    cfg.setup_environment()

    assert id(cfg.settings) == first_id
    assert cfg.settings.planning_model == "p2"
    assert tools.settings is cfg.settings

