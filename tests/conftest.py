import os
import sys
from pathlib import Path
from typing import Iterator

import pytest
from circuitron.docker_session import cleanup_stale_containers

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


@pytest.fixture(scope="session", autouse=True)
def _clean_circuitron_containers_session() -> Iterator[None]:
    """Clean up Circuitron containers before and after the test session.

    This prevents leaked containers from previous failed runs and ensures
    any containers created during tests are removed on exit.
    """
    # Pre-test cleanup
    cleanup_stale_containers("circuitron-kicad-")
    cleanup_stale_containers("circuitron-final-")
    try:
        yield
    finally:
        # Post-test cleanup
        cleanup_stale_containers("circuitron-kicad-")
        cleanup_stale_containers("circuitron-final-")

