import asyncio
import json
import subprocess
from unittest.mock import patch

from agents.run_context import RunContextWrapper
from development.tools import search_kicad_libraries


def test_search_kicad_libraries():
    fake_output = '[{"name": "LM324", "library": "linear", "footprint": "DIP-14", "description": "op amp"}]'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=fake_output, stderr="")
    with patch("development.tools.subprocess.run", return_value=completed) as run_mock:
        ctx = RunContextWrapper(context=None)
        args = json.dumps({"query": "opamp lm324"})
        result = asyncio.run(search_kicad_libraries.on_invoke_tool(ctx, args))
        data = json.loads(result)
        assert data[0]["name"] == "LM324"
        run_mock.assert_called_once()


def test_search_kicad_libraries_timeout():
    with patch(
        "development.tools.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=30),
    ):
        ctx = RunContextWrapper(context=None)
        args = json.dumps({"query": "123"})
        result = asyncio.run(search_kicad_libraries.on_invoke_tool(ctx, args))
        assert "error" in result.lower()
