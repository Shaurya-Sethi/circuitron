import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import circuitron.cli as cli
from circuitron.models import CodeGenerationOutput


def test_run_circuitron_invokes_pipeline():
    out = CodeGenerationOutput(complete_skidl_code="code")
    async def fake_pipeline(prompt: str, show_reasoning: bool = False, debug: bool = False):
        assert prompt == "p"
        assert show_reasoning is True
        assert debug is False
        return out

    with patch("circuitron.pipeline.pipeline", AsyncMock(side_effect=fake_pipeline)):
        result = asyncio.run(cli.run_circuitron("p", show_reasoning=True))
    assert result is out


def test_cli_main_uses_args_and_prints(capsys):
    out = CodeGenerationOutput(complete_skidl_code="abc")
    args = SimpleNamespace(prompt="p", reasoning=False, debug=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
        patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)):
        cli.main()
    captured = capsys.readouterr().out
    assert "GENERATED SKiDL CODE" in captured
    assert "abc" in captured


def test_cli_main_prompts_for_input(monkeypatch):
    out = CodeGenerationOutput(complete_skidl_code="xyz")
    args = SimpleNamespace(prompt=None, reasoning=True, debug=True)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)) as run_mock:
        monkeypatch.setattr("builtins.input", lambda _: "hello")
        cli.main()
        run_mock.assert_awaited_with("hello", True, True)


def test_module_main_called():
    import runpy
    with patch("circuitron.cli.main") as main_mock:
        runpy.run_module("circuitron", run_name="__main__")
        main_mock.assert_called_once()


def test_cli_main_stops_session():
    out = CodeGenerationOutput(complete_skidl_code="123")
    args = SimpleNamespace(prompt="p", reasoning=False, debug=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)), \
         patch("circuitron.tools.kicad_session.stop") as stop_mock:
        cli.main()
        stop_mock.assert_called_once()

def test_cli_main_handles_keyboardinterrupt(capsys):
    import circuitron.config as cfg
    cfg.setup_environment()
    args = SimpleNamespace(prompt="p", reasoning=False, debug=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.cli.run_circuitron", AsyncMock(side_effect=KeyboardInterrupt)), \
         patch("circuitron.tools.kicad_session.stop"):
        cli.main()
    captured = capsys.readouterr().out
    assert "interrupted" in captured.lower()
