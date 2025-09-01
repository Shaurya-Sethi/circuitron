import asyncio
import json
import io
import contextlib
import subprocess
from typing import Any, Coroutine, cast
from unittest.mock import patch

import circuitron.config as cfg
from agents.tool_context import ToolContext

cfg.setup_environment()


def _fake_exec_python_search(
    script: str, _timeout: int = 120
) -> subprocess.CompletedProcess[str]:
    buf = io.StringIO()

    def stub_search(query: str) -> None:
        print("Device.lib: R (Resistor)")

    with patch("skidl.search", stub_search):
        with contextlib.redirect_stdout(buf):
            exec(script, {})
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=buf.getvalue(), stderr=""
    )


def _fake_exec_python_footprints(
    script: str, _timeout: int = 120
) -> subprocess.CompletedProcess[str]:
    buf = io.StringIO()

    def stub_search_footprints(query: str) -> None:
        print("Package_SO.pretty: SOIC-8 (SOIC footprint)")

    with patch("skidl.search_footprints", stub_search_footprints):
        with contextlib.redirect_stdout(buf):
            exec(script, {})
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=buf.getvalue(), stderr=""
    )


def test_search_kicad_libraries_parses_stdout() -> None:
    from circuitron.tools import search_kicad_libraries

    with patch(
        "circuitron.tools.kicad_session.exec_python_with_env",
        side_effect=lambda script, timeout=120: _fake_exec_python_search(script, timeout),
    ):
        ctx = ToolContext(
            context=None, tool_call_id="t_fixed1", tool_name="search_kicad_libraries"
        )
        args = json.dumps({"query": "R"})
        result: str = asyncio.run(
            cast(
                Coroutine[Any, Any, str],
                search_kicad_libraries.on_invoke_tool(ctx, args),
            )
        )
        data = json.loads(result)
        assert data and data[0]["name"] == "R"


def test_search_kicad_footprints_parses_stdout() -> None:
    from circuitron.tools import search_kicad_footprints

    with patch(
        "circuitron.tools.kicad_session.exec_python_with_env",
        side_effect=lambda script, timeout=120: _fake_exec_python_footprints(script, timeout),
    ):
        ctx = ToolContext(
            context=None, tool_call_id="t_fixed2", tool_name="search_kicad_footprints"
        )
        args = json.dumps({"query": "SOIC"})
        result: str = asyncio.run(
            cast(
                Coroutine[Any, Any, str],
                search_kicad_footprints.on_invoke_tool(ctx, args),
            )
        )
        data = json.loads(result)
        assert data and data[0]["name"] == "SOIC-8"
