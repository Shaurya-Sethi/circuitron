import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
import asyncio

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_design_endpoint():
    response = client.post("/design", json={"prompt": "test"})
    assert response.status_code == 200
    assert "plan" in response.json()
