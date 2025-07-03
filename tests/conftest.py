import os
import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("MCP_URL", "http://localhost:8051")

@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MCP_URL", "http://localhost:8051")
    yield

