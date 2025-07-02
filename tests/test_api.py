from unittest.mock import AsyncMock, patch

from pathlib import Path
import sys
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.api import app
from circuitron.models import CodeGenerationOutput, UserFeedback


def test_run_endpoint_returns_result() -> None:
    out = CodeGenerationOutput(complete_skidl_code="code")

    async def fake_pipeline(
        prompt: str,
        show_reasoning: bool = False,
        debug: bool = False,
        *,
        user_feedback: UserFeedback | None = None,
        interactive: bool = True,
    ) -> CodeGenerationOutput:
        assert prompt == "p"
        assert show_reasoning is False
        assert debug is False
        assert interactive is False
        assert user_feedback is None
        return out

    with patch("circuitron.pipeline.pipeline", AsyncMock(side_effect=fake_pipeline)):
        client = TestClient(app)
        resp = client.post("/run", json={"prompt": "p"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "stdout" in data
    assert "stderr" in data
    assert data["result"]["complete_skidl_code"] == "code"
