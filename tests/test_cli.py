import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import circuitron.cli as cli
from circuitron.models import CodeGenerationOutput
import pytest


def test_run_circuitron_invokes_pipeline() -> None:
    out = CodeGenerationOutput(complete_skidl_code="code")
    async def fake_pipeline(prompt: str, show_reasoning: bool = False, retries: int = 0) -> CodeGenerationOutput:
        assert prompt == "p"
        assert show_reasoning is True
        assert retries == 1
        return out

    with patch("circuitron.pipeline.run_with_retry", AsyncMock(side_effect=fake_pipeline)):
        result = asyncio.run(cli.run_circuitron("p", show_reasoning=True, retries=1))
    assert result is out


def test_cli_main_uses_args_and_prints(capsys: pytest.CaptureFixture[str]) -> None:
    out = CodeGenerationOutput(complete_skidl_code="abc")
    args = SimpleNamespace(prompt="p", reasoning=False, retries=0, dev=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.tools.kicad_session.start"), \
         patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)):
        cli.main()
    captured = capsys.readouterr().out
    assert "GENERATED SKiDL CODE" in captured
    assert "abc" in captured


def test_cli_main_prompts_for_input(monkeypatch: pytest.MonkeyPatch) -> None:
    out = CodeGenerationOutput(complete_skidl_code="xyz")
    args = SimpleNamespace(prompt=None, reasoning=True, retries=0, dev=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.tools.kicad_session.start"), \
         patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)) as run_mock:
        monkeypatch.setattr("builtins.input", lambda _: "hello")
        cli.main()
        run_mock.assert_awaited_with("hello", True, 0)


def test_module_main_called() -> None:
    import runpy
    with patch("circuitron.cli.main") as main_mock:
        runpy.run_module("circuitron", run_name="__main__")
        main_mock.assert_called_once()


def test_cli_main_stops_session() -> None:
    out = CodeGenerationOutput(complete_skidl_code="123")
    args = SimpleNamespace(prompt="p", reasoning=False, retries=0, dev=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.tools.kicad_session.start"), \
         patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)), \
         patch("circuitron.tools.kicad_session.stop") as stop_mock:
        cli.main()
        stop_mock.assert_called_once()

def test_cli_main_handles_keyboardinterrupt(capsys: pytest.CaptureFixture[str]) -> None:
    import circuitron.config as cfg
    cfg.setup_environment()
    args = SimpleNamespace(prompt="p", reasoning=False, retries=0, dev=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.tools.kicad_session.start"), \
         patch("circuitron.cli.run_circuitron", AsyncMock(side_effect=KeyboardInterrupt)), \
         patch("circuitron.tools.kicad_session.stop"):
        cli.main()
    captured = capsys.readouterr().out
    assert "interrupted" in captured.lower()


def test_cli_main_handles_exception(capsys: pytest.CaptureFixture[str]) -> None:
    args = SimpleNamespace(prompt="p", reasoning=False, retries=1, dev=False)
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.tools.kicad_session.start"), \
         patch("circuitron.cli.run_circuitron", AsyncMock(side_effect=RuntimeError("fail"))), \
         patch("circuitron.tools.kicad_session.stop"):
        cli.main()
    captured = capsys.readouterr().out
    assert "error" in captured.lower()


def test_verify_containers_success() -> None:
    with patch("circuitron.tools.kicad_session.start") as start_mock:
        assert cli.verify_containers() is True
        start_mock.assert_called_once()


def test_verify_containers_failure(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "circuitron.tools.kicad_session.start",
        side_effect=RuntimeError("bad"),
    ):
        assert cli.verify_containers() is False
    captured = capsys.readouterr().out
    assert "failed to start" in captured.lower()


def test_cli_main_no_prompt_on_container_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    args = SimpleNamespace(prompt=None, reasoning=False, retries=0, dev=False)
    out = CodeGenerationOutput(complete_skidl_code="")
    with patch("circuitron.cli.setup_environment"), \
         patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.tools.kicad_session.start", side_effect=RuntimeError("bad")), \
         patch("circuitron.cli.run_circuitron", AsyncMock(return_value=out)) as run_mock, \
         patch("circuitron.tools.kicad_session.stop"):
        monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(AssertionError("prompt called")))
        cli.main()
        run_mock.assert_not_called()


def test_cli_dev_mode_shows_run_items(capsys: pytest.CaptureFixture[str]) -> None:
    from circuitron import debug as dbg
    import circuitron.config as cfg
    from openai.types.responses.response_output_message import ResponseOutputMessage
    from openai.types.responses.response_output_text import ResponseOutputText
    from agents.items import MessageOutputItem
    run_result = SimpleNamespace(
        final_output=None,
        new_items=[
            MessageOutputItem(
                agent=SimpleNamespace(name="A"),
                raw_item=ResponseOutputMessage(
                    id="1",
                    content=[ResponseOutputText(annotations=[], text="hello", type="output_text")],
                    role="assistant",
                    status="completed",
                    type="message",
                ),
            )
        ],
    )

    async def fake_run(prompt: str, show_reasoning: bool = False, retries: int = 0) -> CodeGenerationOutput:
        await dbg.run_agent(SimpleNamespace(name="A"), "hi")
        return CodeGenerationOutput(complete_skidl_code="code")

    args = SimpleNamespace(prompt="p", reasoning=False, retries=0, dev=True)
    with patch("circuitron.pipeline.parse_args", return_value=args), \
         patch("circuitron.cli.setup_environment", side_effect=lambda dev: setattr(cfg.settings, "dev_mode", dev)), \
         patch("circuitron.debug.Runner.run", AsyncMock(return_value=run_result)), \
         patch("circuitron.cli.run_circuitron", AsyncMock(side_effect=fake_run)), \
         patch("circuitron.tools.kicad_session.start"), \
         patch("circuitron.tools.kicad_session.stop"), \
         patch("circuitron.debug.display_run_items", wraps=dbg.display_run_items) as disp_mock:
        cli.main()
        disp_mock.assert_called_once_with(run_result)
    captured = capsys.readouterr().out
    cfg.settings.dev_mode = False
    assert "hello" in captured
