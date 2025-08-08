from __future__ import annotations

from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML
from typing import Any, cast

from ..themes import Theme


class InputBox:
    """Prompt the user for input inside a styled panel."""

    def __init__(self, console: Console, theme: Theme) -> None:
        self.console = console
        self.theme = theme
        self.session: PromptSession[Any] = PromptSession(history=InMemoryHistory())

    def ask(self, message: str) -> str:
        """Return user input for ``message`` using prompt_toolkit."""
        prompt_text = HTML(f'<style fg="{self.theme.accent}">{message}</style> ')
        try:
            return cast(str, self.session.prompt(prompt_text))
        except Exception:
            return input(f"{message}: ")
