"""Interactive prompt component using ``prompt_toolkit``."""

from __future__ import annotations

from pathlib import Path

from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.history import FileHistory  # type: ignore
from prompt_toolkit.key_binding import KeyBindings  # type: ignore
from prompt_toolkit.formatted_text import HTML  # type: ignore
from rich.console import Console

from ..themes import Theme


class Prompt:
    """Collect user input with history and theming."""

    def __init__(self, console: Console, theme: Theme) -> None:
        self.console = console
        self.theme = theme
        self._session: PromptSession | None = None
        self._history_file = Path.home() / ".circuitron_history"
        self._bindings = KeyBindings()
        self._bindings.add("c-a")(lambda event: event.current_buffer.cursor_home())
        self._bindings.add("c-e")(lambda event: event.current_buffer.cursor_end())
        self._bindings.add("c-l")(lambda event: event.app.renderer.clear())

    def ask(self, message: str) -> str:
        """Return user input for ``message``."""
        prompt_text = HTML(f'<style fg="{self.theme.accent}">{message}:</style> ')
        # Lazily create the PromptSession to avoid failures on headless Windows tests
        if self._session is None:
            try:
                self._session = PromptSession(
                    history=FileHistory(str(self._history_file)),
                    key_bindings=self._bindings,
                )
            except Exception:
                self._session = None
        try:
            if self._session is None:
                raise RuntimeError("No interactive session available")
            return self._session.prompt(prompt_text)
        except Exception:
            return input(f"{message}: ")
