from unittest.mock import MagicMock

import pytest
from rich.console import Console
from prompt_toolkit.formatted_text import HTML  # type: ignore

from circuitron.ui.components.input_box import InputBox
from circuitron.ui.themes import Theme


def test_input_box_ask_uses_html(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    monkeypatch.setattr(
        "circuitron.ui.components.input_box.PromptSession", lambda *a, **k: session
    )
    ib = InputBox(Console(), Theme(name="t", gradient_colors=[], accent="green"))
    session.prompt.return_value = "done"
    result = ib.ask("hello")
    assert result == "done"
    args = session.prompt.call_args[0][0]
    assert isinstance(args, HTML)
    assert "hello" in str(args)

