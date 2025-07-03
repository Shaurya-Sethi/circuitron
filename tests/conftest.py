import os
import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("PLANNING_MODEL", "test-model")
os.environ.setdefault("PLAN_EDIT_MODEL", "test-model")
os.environ.setdefault("PART_FINDER_MODEL", "test-model")
os.environ.setdefault("MCP_URL", "http://localhost:8051")

@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("PLANNING_MODEL", "test-model")
    monkeypatch.setenv("PLAN_EDIT_MODEL", "test-model")
    monkeypatch.setenv("PART_FINDER_MODEL", "test-model")
    monkeypatch.setenv("MCP_URL", "http://localhost:8051")
    yield

