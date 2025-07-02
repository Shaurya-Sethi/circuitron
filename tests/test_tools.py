import asyncio
import json
import subprocess
from unittest.mock import patch

from agents.tool_context import ToolContext
import circuitron.config as cfg


def test_search_kicad_libraries():
    cfg.setup_environment()
    from circuitron.tools import search_kicad_libraries
    fake_output = '[{"name": "LM324", "library": "linear", "footprint": "DIP-14", "description": "op amp"}]'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=fake_output, stderr="")
    with patch("circuitron.tools.subprocess.run", return_value=completed) as run_mock:
        ctx = ToolContext(context=None, tool_call_id="t1")
        args = json.dumps({"query": "opamp lm324"})
        result = asyncio.run(search_kicad_libraries.on_invoke_tool(ctx, args))
        data = json.loads(result)
        assert data[0]["name"] == "LM324"
        run_mock.assert_called_once()


def test_search_kicad_libraries_timeout():
    cfg.setup_environment()
    from circuitron.tools import search_kicad_libraries
    with patch(
        "circuitron.tools.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=30),
    ):
        ctx = ToolContext(context=None, tool_call_id="t2")
        args = json.dumps({"query": "123"})
        result = asyncio.run(search_kicad_libraries.on_invoke_tool(ctx, args))
        assert "error" in result.lower()


def test_search_kicad_footprints():
    cfg.setup_environment()
    from circuitron.tools import search_kicad_footprints
    fake_output = '[{"name": "SOIC-8", "library": "Package_SO", "description": "soic"}]'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=fake_output, stderr="")
    with patch("circuitron.tools.subprocess.run", return_value=completed) as run_mock:
        ctx = ToolContext(context=None, tool_call_id="t3")
        args = json.dumps({"query": "SOIC-8"})
        result = asyncio.run(search_kicad_footprints.on_invoke_tool(ctx, args))
        data = json.loads(result)
        assert data[0]["name"] == "SOIC-8"
        run_mock.assert_called_once()


def test_search_kicad_footprints_timeout():
    cfg.setup_environment()
    from circuitron.tools import search_kicad_footprints
    with patch(
        "circuitron.tools.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=30),
    ):
        ctx = ToolContext(context=None, tool_call_id="t4")
        args = json.dumps({"query": "DIP"})
        result = asyncio.run(search_kicad_footprints.on_invoke_tool(ctx, args))
        assert "error" in result.lower()


def test_extract_pin_details():
    cfg.setup_environment()
    from circuitron.tools import extract_pin_details
    fake_output = '[{"number": "1", "name": "VCC", "function": "POWER"}]'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=fake_output, stderr="")
    with patch("circuitron.tools.subprocess.run", return_value=completed) as run_mock:
        ctx = ToolContext(context=None, tool_call_id="t5")
        args = json.dumps({"library": "linear", "part_name": "lm386"})
        result = asyncio.run(extract_pin_details.on_invoke_tool(ctx, args))
        data = json.loads(result)
        assert data[0]["name"] == "VCC"
        run_mock.assert_called_once()


def test_extract_pin_details_timeout():
    cfg.setup_environment()
    from circuitron.tools import extract_pin_details
    with patch(
        "circuitron.tools.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=30),
    ):
        ctx = ToolContext(context=None, tool_call_id="t6")
        args = json.dumps({"library": "lin", "part_name": "bad"})
        result = asyncio.run(extract_pin_details.on_invoke_tool(ctx, args))
        assert "error" in result.lower()


def test_create_mcp_documentation_tools():
    cfg.setup_environment()
    from circuitron.tools import create_mcp_documentation_tools

    dummy_tool = object()
    with patch("circuitron.tools.create_mcp_tool", return_value=dummy_tool) as helper:
        tools = create_mcp_documentation_tools()
        helper.assert_called_once_with("skidl_docs")
        assert tools == [dummy_tool]


def test_create_mcp_validation_tools():
    cfg.setup_environment()
    from circuitron.tools import create_mcp_validation_tools

    dummy_tool = object()
    with patch("circuitron.tools.create_mcp_tool", return_value=dummy_tool) as helper:
        tools = create_mcp_validation_tools()
        helper.assert_called_once_with("skidl_validation")
        assert tools == [dummy_tool]


def test_run_erc_success():
    cfg.setup_environment()
    from circuitron.tools import run_erc

    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")
    with patch("circuitron.tools.subprocess.run", return_value=completed) as run_mock:
        ctx = ToolContext(context=None, tool_call_id="t7")
        args = json.dumps({"script_path": "/tmp/a.py"})
        result = asyncio.run(run_erc.on_invoke_tool(ctx, args))
        assert "{}" in result
        run_mock.assert_called_once()


def test_run_erc_timeout():
    cfg.setup_environment()
    from circuitron.tools import run_erc

    with patch(
        "circuitron.tools.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=60),
    ):
        ctx = ToolContext(context=None, tool_call_id="t8")
        args = json.dumps({"script_path": "/tmp/a.py"})
        result = asyncio.run(run_erc.on_invoke_tool(ctx, args))
        assert "success" in result

