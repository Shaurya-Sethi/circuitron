import pytest

import circuitron.config as cfg


def test_setup_environment_requires_vars(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MCP_URL", raising=False)
    with pytest.raises(SystemExit) as exc:
        cfg.setup_environment()
    assert "Missing required environment variables" in str(exc.value)

