from unittest.mock import MagicMock

import asyncio
import pytest
from rich.console import Console
from prompt_toolkit.formatted_text import HTML  # type: ignore

from circuitron.ui.components.input_box import InputBox


def test_input_box_ask_uses_html(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(
        "circuitron.ui.components.input_box.PromptSession", lambda *a, **k: session
    )
    ib = InputBox(Console())
    session.prompt.return_value = "done"
    result = ib.ask("hello")
    assert result == "done"
    args = session.prompt.call_args[0][0]
    assert isinstance(args, HTML)
    assert "hello" in str(args)


def test_input_box_ask_renders_box(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(
        "circuitron.ui.components.input_box.PromptSession", lambda *a, **k: session
    )
    ib = InputBox(Console())
    session.prompt.return_value = "ok"
    _ = ib.ask("Design?")
    # Ensure the composed HTML prompt includes our box borders and message
    html_arg = session.prompt.call_args[0][0]
    text = str(html_arg)
    assert "┌" in text
    assert "└" in text
    assert "Design?" in text


def test_input_box_escape(monkeypatch):
    ib = InputBox(Console())
    monkeypatch.setattr("builtins.input", lambda _p: "\x1b")
    async def run() -> None:
        with pytest.raises(EOFError):
            ib.ask("msg")
    asyncio.run(run())


def test_input_box_prompttoolkit_esc_bubbles(monkeypatch):
    # Simulate prompt_toolkit PromptSession being available and raising EOFError on Esc
    class FakeSession:
        def prompt(self, *a, **k):
            raise EOFError

    monkeypatch.setattr(
        "circuitron.ui.components.input_box.PromptSession",
        lambda *a, **k: FakeSession(),
    )
    ib = InputBox(Console())
    with pytest.raises(EOFError):
        ib.ask("msg")

