import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
import pytest

from backend.agent.orchestrator import DesignAgent


@pytest.mark.asyncio
async def test_plan_returns_string():
    agent = DesignAgent()
    result = await agent.plan("test")
    assert isinstance(result, str)

