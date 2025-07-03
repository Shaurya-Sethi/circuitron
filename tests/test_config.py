import pytest

import circuitron.config as cfg


def test_setup_environment_requires_vars(monkeypatch):
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

