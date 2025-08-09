from __future__ import annotations

from rich.console import Console
from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.history import InMemoryHistory  # type: ignore
from prompt_toolkit.formatted_text import HTML  # type: ignore
from prompt_toolkit.shortcuts import CompleteStyle  # type: ignore
from prompt_toolkit.key_binding import KeyBindings  # type: ignore

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
        visually "inside" an input box. Falls back to a basic ``input()``
        when a prompt session cannot be initialized (e.g., headless tests).

        Pressing ``Esc`` exits the application with a goodbye message.

        Example (simplified):
        ┌─ What would you like me to design? (press Esc to exit)
        │
        └─ ❯ [cursor here]
        """
        message = f"{message} (press Esc to exit)"
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

        # Prefer prompt_toolkit whenever available (even inside an event loop).
        # If it fails for any reason other than an intentional EOF exit, fall back to input().
        if self._session is not None:
            try:
                # Attach a context-aware completer for slash-commands and models,
                # unless a custom completer is provided by the caller.
                if completer is None:
                    completer = SlashCommandCompleter(
                        commands=["/help", "/model"],
                        models=self._available_models,
                    )
                bindings = KeyBindings()
                bindings.add("escape")(lambda event: event.app.exit(exception=EOFError()))
                return self._session.prompt(
                    prompt_text,
                    completer=completer,
                    complete_while_typing=True,
                    reserve_space_for_menu=6,
                    complete_style=CompleteStyle.COLUMN,
                    key_bindings=bindings,
                )
            except EOFError:
                # Bubble up so the caller can exit gracefully.
                raise
            except Exception:
                # Fall through to boxed input() fallback below
                pass

        # Boxed fallback using standard input in async or headless environments
        try:
            self.console.print(f"[bold {accent}]┌─[/] [bold {accent}]{message}[/]")
            self.console.print(f"[bold {accent}]│[/] ")
            text = input("└─ ❯ ")
            if text == "\x1b":
                raise EOFError
            return text
        except Exception:
            # Final guard: minimal prompt
            text = input(f"{message}: ")
            if text == "\x1b":
                raise EOFError
            return text
