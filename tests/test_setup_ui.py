from __future__ import annotations

from unittest.mock import MagicMock

from prompt_toolkit.document import Document  # type: ignore
from prompt_toolkit.completion import Completer  # type: ignore
from rich.console import Console

from circuitron.ui.components.input_box import InputBox


def _collect(completer: Completer, text: str) -> list[str]:
    doc = Document(text=text, cursor_position=len(text))
    return [c.text for c in completer.get_completions(doc, None)]


def test_input_box_completer_includes_setup(monkeypatch) -> None:
    # Patch PromptSession to capture prompt() kwargs
    session = MagicMock()
    monkeypatch.setattr(
        "circuitron.ui.components.input_box.PromptSession", lambda *a, **k: session
    )
    session.prompt.return_value = "ok"
    ib = InputBox(Console())
    _ = ib.ask("Design?")
    kwargs = session.prompt.call_args.kwargs
    completer = kwargs.get("completer")
    assert completer is not None
    texts = _collect(completer, "/")
    assert "/setup" in texts

