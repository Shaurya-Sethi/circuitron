import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("MCP_URL", "http://localhost:8051")
os.environ.setdefault("SUPABASE_URL", "http://supabase")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "svc")
os.environ.setdefault("NEO4J_URI", "bolt://neo4j")
os.environ.setdefault("NEO4J_USER", "neo")
os.environ.setdefault("NEO4J_PASSWORD", "pass")
os.environ.setdefault("CIRCUITRON_AUTO_ONBOARD", "0")
os.environ.setdefault("CIRCUITRON_ENV_FILE", "/tmp/circuitron_test.env")

# Ensure the project root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MCP_URL", "http://localhost:8051")
    monkeypatch.setenv("SUPABASE_URL", "http://supabase")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "svc")
    monkeypatch.setenv("NEO4J_URI", "bolt://neo4j")
    monkeypatch.setenv("NEO4J_USER", "neo")
    monkeypatch.setenv("NEO4J_PASSWORD", "pass")
    monkeypatch.setenv("CIRCUITRON_AUTO_ONBOARD", "0")
    monkeypatch.setenv("CIRCUITRON_ENV_FILE", "/tmp/circuitron_test.env")
    yield

