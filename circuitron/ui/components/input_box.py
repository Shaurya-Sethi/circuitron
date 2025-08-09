from __future__ import annotations

from rich.console import Console
import asyncio
from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.history import InMemoryHistory  # type: ignore
from prompt_toolkit.formatted_text import HTML  # type: ignore
from prompt_toolkit.shortcuts import CompleteStyle  # type: ignore

from .completion import SlashCommandCompleter
from ...config import settings


ACCENT = "cyan"


class InputBox:
    """Prompt the user for input inside a styled panel."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self._session: PromptSession | None = None
        # Supported models for completion are sourced from settings.
        self._available_models: list[str] = list(getattr(settings, "available_models", ["o4-mini", "gpt-5-mini"]))

    def ask(self, message: str, completer=None) -> str:
        """Return user input for ``message`` using prompt_toolkit.

        Renders a simple, three-line boxed prompt so the user types
        visually "inside" an input box. Falls back to a basic input()
        when a prompt session cannot be initialized (e.g., headless tests).

        Example (simplified):
        ┌─ What would you like me to design?
        │
        └─ ❯ [cursor here]
        """
        accent = ACCENT
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

        # When running inside an active asyncio event loop (e.g., during
        # the async pipeline), avoid prompt_toolkit's synchronous prompt to
        # prevent 'run_async was never awaited' warnings. Render a simple
        # boxed prompt with Rich and read input() synchronously.
        in_async_loop = True
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            in_async_loop = False

        if self._session is not None and not in_async_loop:
            try:
                # Attach a context-aware completer for slash-commands and models,
                # unless a custom completer is provided by the caller.
                if completer is None:
                    completer = SlashCommandCompleter(
                        commands=["/help", "/model"],
                        models=self._available_models,
                    )
                return self._session.prompt(
                    prompt_text,
                    completer=completer,
                    complete_while_typing=True,
                    reserve_space_for_menu=6,
                    complete_style=CompleteStyle.COLUMN,
                )
            except Exception:
                # Fall through to boxed input() fallback below
                pass

        # Boxed fallback using standard input in async or headless environments
        try:
            self.console.print(f"[bold {accent}]┌─[/] [bold {accent}]{message}[/]")
            self.console.print(f"[bold {accent}]│[/] ")
            return input("└─ ❯ ")
        except Exception:
            # Final guard: minimal prompt
            return input(f"{message}: ")
