from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.history import InMemoryHistory  # type: ignore

from ..themes import Theme


class InputBox:
    """Prompt the user for input inside a styled panel."""

    def __init__(self, console: Console, theme: Theme) -> None:
        self.console = console
        self.theme = theme
        self.session = PromptSession(history=InMemoryHistory())

    def ask(self, message: str) -> str:
        panel = Panel(Markdown(message), border_style=self.theme.accent, expand=False)
        self.console.print(panel)
        try:
            return self.session.prompt("")
        except Exception:
            return input("{0} ".format(message))
