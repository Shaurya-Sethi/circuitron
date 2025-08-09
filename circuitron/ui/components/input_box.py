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
        """Return user input for ``message`` using prompt_toolkit.

        Renders a simple, three-line boxed prompt so the user types
        visually "inside" an input box. Falls back to a basic input()
        when a prompt session cannot be initialized (e.g., headless tests).

        Example (simplified):
        ┌─ What would you like me to design?
        │
        └─ ❯ [cursor here]
        """
        accent = self.theme.accent
        # Compose a minimal multi-line box using Unicode borders.
        top = f'<style fg="{accent}">┌─</style> <style fg="{accent}">{message}</style>'
        mid = f'<style fg="{accent}">│</style> '
        bottom = f'<style fg="{accent}">└─ ❯ </style>'
        prompt_text = HTML("\n".join([top, mid, bottom]))
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
