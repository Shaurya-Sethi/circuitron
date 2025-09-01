import asyncio
import json
import os
import subprocess
from typing import Any, Coroutine, cast
from unittest.mock import patch

from agents.tool_context import ToolContext
import circuitron.config as cfg


def test_search_kicad_libraries() -> None:
    cfg.setup_environment()
    from circuitron.tools import search_kicad_libraries

    fake_output = '[{"name": "LM324", "library": "linear", "footprint": "DIP-14", "description": "op amp"}]'
    completed = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=fake_output, stderr=""
    )
    with patch(
        "circuitron.tools.kicad_session.exec_python_with_env", return_value=completed
    ) as run_mock:
        ctx = ToolContext(
            context=None, tool_call_id="t1", tool_name="search_kicad_libraries"
        )
        args = json.dumps({"query": "opamp lm324"})
        result: str = asyncio.run(
            cast(
                Coroutine[Any, Any, str],
                search_kicad_libraries.on_invoke_tool(ctx, args),
            )
        )
        data = json.loads(result)
        assert data[0]["name"] == "LM324"
        run_mock.assert_called_once()


def test_search_kicad_libraries_timeout() -> None:
    cfg.setup_environment()
    from circuitron.tools import search_kicad_libraries

    with patch(
        "circuitron.tools.kicad_session.exec_python_with_env",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=30),
    ):
        ctx = ToolContext(
            context=None, tool_call_id="t2", tool_name="search_kicad_libraries"
        )
        args = json.dumps({"query": "123"})
        result: str = asyncio.run(
            cast(
                Coroutine[Any, Any, str],
                search_kicad_libraries.on_invoke_tool(ctx, args),
            )
        )
        assert "error" in result.lower()


def test_search_kicad_footprints() -> None:
    cfg.setup_environment()
    from circuitron.tools import search_kicad_footprints

    fake_output = '[{"name": "SOIC-8", "library": "Package_SO", "description": "soic"}]'
    completed = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=fake_output, stderr=""
    )
    with patch(
        "circuitron.tools.kicad_session.exec_python_with_env", return_value=completed
    ) as run_mock:
        ctx = ToolContext(
            context=None, tool_call_id="t3", tool_name="search_kicad_footprints"
        )
        args = json.dumps({"query": "SOIC-8"})
        result: str = asyncio.run(
            cast(
                Coroutine[Any, Any, str],
                search_kicad_footprints.on_invoke_tool(ctx, args),
            )
        )
        data = json.loads(result)
        assert data[0]["name"] == "SOIC-8"
        run_mock.assert_called_once()


def test_search_kicad_footprints_timeout() -> None:
    cfg.setup_environment()
    from circuitron.tools import search_kicad_footprints

    with patch(
        "circuitron.tools.kicad_session.exec_python_with_env",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=30),
    ):
        ctx = ToolContext(
            context=None, tool_call_id="t4", tool_name="search_kicad_footprints"
        )
        args = json.dumps({"query": "DIP"})
        result: str = asyncio.run(
            cast(
                Coroutine[Any, Any, str],
                search_kicad_footprints.on_invoke_tool(ctx, args),
            )
        )
        assert "error" in result.lower()


def test_extract_pin_details() -> None:
    cfg.setup_environment()
    from circuitron.tools import extract_pin_details

    fake_output = '[{"number": "1", "name": "VCC", "function": "POWER"}]'
    completed = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=fake_output, stderr=""
    )
    with patch(
        "circuitron.tools.kicad_session.exec_python_with_env", return_value=completed
    ) as run_mock:
        ctx = ToolContext(
            context=None, tool_call_id="t5", tool_name="extract_pin_details"
        )
        args = json.dumps({"library": "linear", "part_name": "lm386"})
        result: str = asyncio.run(
            cast(
                Coroutine[Any, Any, str], extract_pin_details.on_invoke_tool(ctx, args)
            )
        )
        data = json.loads(result)
        assert data[0]["name"] == "VCC"
        run_mock.assert_called_once()


def test_extract_pin_details_timeout() -> None:
    cfg.setup_environment()
    from circuitron.tools import extract_pin_details

    with patch(
        "circuitron.tools.kicad_session.exec_python_with_env",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=30),
    ):
        ctx = ToolContext(
            context=None, tool_call_id="t6", tool_name="extract_pin_details"
        )
        args = json.dumps({"library": "lin", "part_name": "bad"})
        result: str = asyncio.run(
            cast(
                Coroutine[Any, Any, str], extract_pin_details.on_invoke_tool(ctx, args)
            )
        )
        assert "error" in result.lower()


def test_create_mcp_server() -> None:
    cfg.setup_environment()
    from circuitron.tools import create_mcp_server, MCPServerSse

    server = create_mcp_server()
    assert isinstance(server, MCPServerSse)
    assert server.name == "skidl_docs"
    assert server.params["url"] == cfg.settings.mcp_url + "/sse"
    assert "timeout" in server.params
    assert server.client_session_timeout_seconds == cfg.settings.network_timeout


def test_run_erc_success() -> None:
    cfg.setup_environment()
    from circuitron.tools import run_erc_tool

    completed = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="{}", stderr=""
    )
    with patch(
        "circuitron.tools.kicad_session.exec_erc_with_env", return_value=completed
    ) as run_mock:
        ctx = ToolContext(
            context=None, tool_call_id="t7", tool_name="run_erc"
        )
        args = json.dumps({"script_path": "/tmp/a.py"})
        result: str = asyncio.run(
            cast(Coroutine[Any, Any, str], run_erc_tool.on_invoke_tool(ctx, args))
        )
        assert "{}" in result
        run_mock.assert_called_once()


def test_run_erc_timeout() -> None:
    cfg.setup_environment()
    from circuitron.tools import run_erc_tool

    with patch(
        "circuitron.tools.kicad_session.exec_erc_with_env",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=60),
    ):
        ctx = ToolContext(
            context=None, tool_call_id="t8", tool_name="run_erc"
        )
        args = json.dumps({"script_path": "/tmp/a.py"})
        result: str = asyncio.run(
            cast(Coroutine[Any, Any, str], run_erc_tool.on_invoke_tool(ctx, args))
        )
        assert "success" in result


def test_kicad_session_start_once() -> None:
    cfg.setup_environment()
    from circuitron.tools import search_kicad_libraries, kicad_session

    kicad_session.started = False
    fake_proc = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="[]", stderr=""
    )

    def fake_start() -> None:
        kicad_session.started = True

    with (
        patch.object(kicad_session, "_run", return_value=fake_proc) as _run_mock,
        patch.object(kicad_session, "start", side_effect=fake_start) as start_mock,
    ):
        ctx = ToolContext(
            context=None, tool_call_id="t9", tool_name="search_kicad_libraries"
        )
        args = json.dumps({"query": "foo"})
        asyncio.run(
            cast(
                Coroutine[Any, Any, str],
                search_kicad_libraries.on_invoke_tool(ctx, args),
            )
        )
        asyncio.run(
            cast(
                Coroutine[Any, Any, str],
                search_kicad_libraries.on_invoke_tool(ctx, args),
            )
        )
        assert start_mock.call_count == 2
        assert _run_mock.call_count == 6
    kicad_session.started = False


def test_kicad_session_container_name_contains_pid() -> None:
    from circuitron.tools import kicad_session
    assert str(os.getpid()) in kicad_session.container_name


def test_execute_final_script() -> None:
    cfg.setup_environment()
    from circuitron.tools import execute_final_script_tool

    with (
        patch("circuitron.tools.DockerSession") as sess_cls,
        patch("circuitron.tools.prepare_output_dir", return_value="/tmp/out"),
        patch("circuitron.tools.write_temp_skidl_script", return_value="/tmp/s.py"),
        patch("circuitron.tools.os.listdir", return_value=["file.net"]),
    ):
        sess = sess_cls.return_value
        sess.exec_full_script_with_env.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        ctx = ToolContext(
            context=None, tool_call_id="tf", tool_name="execute_final_script"
        )
        args = json.dumps({"script_content": "code", "output_dir": "/tmp/out"})
        result: str = asyncio.run(
            cast(Coroutine[Any, Any, str], execute_final_script_tool.on_invoke_tool(ctx, args))
        )
        data = json.loads(result)
        assert data["success"] is True
        sess_cls.assert_called_once()
        sess.exec_full_script_with_env.assert_called_once()


def test_execute_final_script_windows_path() -> None:
    cfg.setup_environment()
    from circuitron.tools import execute_final_script_tool
    from circuitron.config import settings

    with (
        patch("circuitron.tools.DockerSession") as sess_cls,
        patch("circuitron.tools.prepare_output_dir", return_value="C:\\out"),
        patch("circuitron.tools.convert_windows_path_for_docker", return_value="/mnt/c/out"),
        patch("circuitron.tools.write_temp_skidl_script", return_value="C:\\s.py"),
        patch("circuitron.tools.os.listdir", return_value=["file.net"]),
    ):
        sess = sess_cls.return_value
        sess.exec_full_script_with_env.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        ctx = ToolContext(
            context=None, tool_call_id="tfw", tool_name="execute_final_script"
        )
        args = json.dumps({"script_content": "code", "output_dir": "C:\\out", "keep_skidl": False})
        result: str = asyncio.run(
            cast(Coroutine[Any, Any, str], execute_final_script_tool.on_invoke_tool(ctx, args))
        )
        data = json.loads(result)
        assert data["success"] is True
        sess_cls.assert_called_once_with(
            settings.kicad_image,
            f"circuitron-final-{os.getpid()}",
            volumes={"C:\\out": "/mnt/c/out"},
        )
        sess.exec_full_script_with_env.assert_called_once()


def test_execute_final_script_with_keep_skidl() -> None:
    """Test that execute_final_script calls keep_skidl_script when keep_skidl=True."""
    cfg.setup_environment()
    from circuitron.tools import execute_final_script_tool

    with (
        patch("circuitron.tools.DockerSession") as sess_cls,
        patch("circuitron.tools.prepare_output_dir", return_value="/tmp/out"),
        patch("circuitron.tools.write_temp_skidl_script", return_value="/tmp/s.py"),
        patch("circuitron.tools.keep_skidl_script") as keep_skidl_mock,
        patch("circuitron.tools.os.listdir", return_value=["file.net"]),
    ):
        sess = sess_cls.return_value
        sess.exec_full_script_with_env.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        
        script_content = "from skidl import *\nprint('test')"
        ctx = ToolContext(
            context=None, tool_call_id="tks", tool_name="execute_final_script"
        )
        args = json.dumps({
            "script_content": script_content, 
            "output_dir": "/tmp/out", 
            "keep_skidl": True
        })
        
        result: str = asyncio.run(
            cast(Coroutine[Any, Any, str], execute_final_script_tool.on_invoke_tool(ctx, args))
        )
        
        data = json.loads(result)
        assert data["success"] is True
        
        # Verify keep_skidl_script was called with correct parameters
        keep_skidl_mock.assert_called_once()
        call_args = keep_skidl_mock.call_args
        assert call_args[0][0] == "/tmp/out"  # output_dir argument
        # The wrapped script should contain the original content
        wrapped_script = call_args[0][1]
        assert script_content in wrapped_script
        assert "from skidl import *" in wrapped_script


def test_execute_final_script_without_keep_skidl() -> None:
    """Test that execute_final_script does not call keep_skidl_script when keep_skidl=False."""
    cfg.setup_environment()
    from circuitron.tools import execute_final_script_tool

    with (
        patch("circuitron.tools.DockerSession") as sess_cls,
        patch("circuitron.tools.prepare_output_dir", return_value="/tmp/out"),
        patch("circuitron.tools.write_temp_skidl_script", return_value="/tmp/s.py"),
        patch("circuitron.tools.keep_skidl_script") as keep_skidl_mock,
        patch("circuitron.tools.os.listdir", return_value=["file.net"]),
    ):
        sess = sess_cls.return_value
        sess.exec_full_script_with_env.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        
        ctx = ToolContext(
            context=None, tool_call_id="tnks", tool_name="execute_final_script"
        )
        args = json.dumps({
            "script_content": "from skidl import *", 
            "output_dir": "/tmp/out", 
            "keep_skidl": False
        })
        
        result: str = asyncio.run(
            cast(Coroutine[Any, Any, str], execute_final_script_tool.on_invoke_tool(ctx, args))
        )
        
        data = json.loads(result)
        assert data["success"] is True
        
        # Verify keep_skidl_script was NOT called
        keep_skidl_mock.assert_not_called()


def test_prepare_runtime_check_script() -> None:
    from circuitron.utils import prepare_runtime_check_script

    script = "from skidl import *\ngenerate_netlist()\nERC()\n"
    result = prepare_runtime_check_script(script)
    assert "# generate_netlist()" in result
    assert "# ERC()" in result


def test_run_runtime_check_success() -> None:
    cfg.setup_environment()
    from circuitron.tools import run_runtime_check

    output = '{"success": true, "error_details": "", "stdout": "ok", "stderr": ""}'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")
    with patch(
        "circuitron.tools.kicad_session.exec_erc_with_env", return_value=completed
    ) as run_mock:
        result = asyncio.run(run_runtime_check("/tmp/x.py"))
        data = json.loads(result)
        assert data["success"] is True
        run_mock.assert_called_once()


def test_run_runtime_check_failure() -> None:
    cfg.setup_environment()
    from circuitron.tools import run_runtime_check

    output = '{"success": false, "error_details": "boom", "stdout": "", "stderr": "err"}'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")
    with patch(
        "circuitron.tools.kicad_session.exec_erc_with_env", return_value=completed
    ):
        result = asyncio.run(run_runtime_check("/tmp/x.py"))
        data = json.loads(result)
        assert data["success"] is False
