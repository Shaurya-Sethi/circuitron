"""Interactive prompt component using ``prompt_toolkit``."""

from __future__ import annotations

from pathlib import Path

from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.history import FileHistory  # type: ignore
from prompt_toolkit.key_binding import KeyBindings  # type: ignore
from rich.console import Console

from ..themes import Theme


class Prompt:
    """Collect user input with history and theming."""

    def __init__(self, console: Console, theme: Theme) -> None:
        self.console = console
        self.theme = theme
        history_file = Path.home() / ".circuitron_history"
        bindings = KeyBindings()
        bindings.add("c-a")(lambda event: event.current_buffer.cursor_home())
        bindings.add("c-e")(lambda event: event.current_buffer.cursor_end())
        bindings.add("c-l")(lambda event: event.app.renderer.clear())
        self.session = PromptSession(history=FileHistory(str(history_file)), key_bindings=bindings)

    def ask(self, message: str) -> str:
        """Return user input for ``message``."""
        prompt_text = f"[{self.theme.accent}]{message}: [/bold]"
        return self.session.prompt(prompt_text)
