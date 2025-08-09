from __future__ import annotations

from rich.console import Console
from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.history import InMemoryHistory  # type: ignore
from prompt_toolkit.formatted_text import HTML  # type: ignore

from ..themes import Theme


class InputBox:
    """Prompt the user for input inside a styled panel."""

    def __init__(self, console: Console, theme: Theme) -> None:
        self.console = console
        self.theme = theme
        self._session: PromptSession | None = None

    def ask(self, message: str) -> str:
        """Return user input for ``message`` using prompt_toolkit."""
        prompt_text = HTML(f'<style fg="{self.theme.accent}">{message}</style> ')
        # Lazily construct PromptSession to avoid console detection at import time
        if self._session is None:
            try:
                self._session = PromptSession(history=InMemoryHistory())
            except Exception:
                self._session = None
        try:
            if self._session is None:
                raise RuntimeError("No interactive session available")
            return self._session.prompt(prompt_text)
        except Exception:
            return input(f"{message}: ")
