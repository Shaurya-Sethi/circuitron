import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("MCP_URL", "http://localhost:8051")

# Ensure the project root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("MCP_URL", "http://localhost:8051")
    yield

