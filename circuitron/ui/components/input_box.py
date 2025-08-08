from __future__ import annotations

from rich.console import Console
from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.history import InMemoryHistory  # type: ignore
from prompt_toolkit.formatted_text import HTML  # type: ignore
from typing import cast

from ..themes import Theme


class InputBox:
    """Prompt the user for input inside a styled panel."""

    def __init__(self, console: Console, theme: Theme) -> None:
        self.console = console
        self.theme = theme
        # Avoid hard dependency on a real Windows console in tests/CI.
        try:
            self.session: PromptSession | None = PromptSession(history=InMemoryHistory())
        except Exception:
            self.session = None

    def ask(self, message: str) -> str:
        """Return user input for ``message`` using prompt_toolkit."""
        prompt_text = HTML(f'<style fg="{self.theme.accent}">{message}</style> ')
        if self.session is not None:
            try:
                return cast(str, self.session.prompt(prompt_text))
            except Exception:
                pass
        return input(f"{message}: ")
