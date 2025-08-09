from __future__ import annotations

from unittest.mock import MagicMock

from prompt_toolkit.document import Document  # type: ignore
from prompt_toolkit.completion import Completer  # type: ignore
from rich.console import Console

from circuitron.ui.components.completion import SlashCommandCompleter
from circuitron.ui.components.input_box import InputBox
from circuitron.ui.themes import Theme


def collect(completer: Completer, text: str) -> list[str]:
    doc = Document(text=text, cursor_position=len(text))
    return [c.text for c in completer.get_completions(doc, None)]


def test_slash_completer_suggests_commands():
    comp = SlashCommandCompleter(["/help", "/theme", "/model"], ["o4-mini", "gpt-5-mini"]) \
        # type: ignore[call-arg]
    assert set(collect(comp, "/")) >= {"/help", "/theme", "/model"}
    # Partial command prefix narrows suggestions
    assert set(collect(comp, "/mo")) == {"/model"}


def test_slash_completer_model_context():
    comp = SlashCommandCompleter(["/help", "/theme", "/model"], ["o4-mini", "gpt-5-mini"]) \
        # type: ignore[call-arg]
    assert set(collect(comp, "/model ")) == {"o4-mini", "gpt-5-mini"}
    assert set(collect(comp, "/model g")) == {"gpt-5-mini"}


def test_input_box_passes_completer(monkeypatch):
    # Patch PromptSession to capture prompt() kwargs
    session = MagicMock()
    monkeypatch.setattr(
        "circuitron.ui.components.input_box.PromptSession", lambda *a, **k: session
    )
    ib = InputBox(Console(), Theme(name="t", gradient_colors=[], accent="green"))
    session.prompt.return_value = "ok"
    _ = ib.ask("Design?")

    # Ensure completer is provided and behaves for '/'
    kwargs = session.prompt.call_args.kwargs
    completer = kwargs.get("completer")
    assert completer is not None
    # It should propose commands when typing '/'
    texts = collect(completer, "/")
    assert "/model" in texts and "/help" in texts

