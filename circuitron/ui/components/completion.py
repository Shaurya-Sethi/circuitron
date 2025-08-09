"""Custom prompt_toolkit completers for Circuitron CLI.

These completers power the UX for slash-commands (e.g., "/model") and
contextual dropdowns (e.g., available model names) with arrow key navigation.
"""

from __future__ import annotations

from typing import Iterable, Iterator

from prompt_toolkit.completion import Completer, Completion  # type: ignore
from prompt_toolkit.document import Document  # type: ignore


class SlashCommandCompleter(Completer):
    """Context-aware completer for Circuitron slash-commands.

    - When input begins with '/', suggests known commands (e.g., /help, /model).
    - When input matches '/model' (with or without trailing space), suggests
      available model names.
    - Optionally suggests theme names for '/theme ' context.

    Args:
        commands: List of supported slash commands (e.g., ["/help", "/model"]).
        models: List of available model names to show for '/model'.
        themes: Optional list of theme names for '/theme'.
    """

    def __init__(
        self,
        commands: Iterable[str],
        models: Iterable[str],
        themes: Iterable[str] | None = None,
    ) -> None:
        self._commands = list(commands)
        self._models = list(models)
        self._themes = list(themes or [])

    def get_completions(self, document: Document, complete_event) -> Iterator[Completion]:  # type: ignore[override]
        text = document.text
        # Cursor-aware current word/prefix
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # Suggest top-level commands when starting with '/'
        if text.startswith("/") and (" " not in text or text.strip() == "/"):
            prefix = word_before_cursor or text
            for cmd in self._commands:
                if cmd.startswith(prefix):
                    yield Completion(
                        text=cmd,
                        start_position=-len(prefix),
                        display=cmd,
                        display_meta="Circuitron command",
                    )
            return

        # Contextual suggestions for '/model'
        if text.strip().startswith("/model"):
            # After '/model' and optional space, offer model names
            # Determine the token being typed (after last space)
            token = text.split(" ")[-1] if " " in text else ""
            prefix = token
            for name in self._models:
                if not prefix or name.startswith(prefix):
                    yield Completion(
                        text=name,
                        start_position=-len(prefix),
                        display=name,
                        display_meta="Model",
                    )
            return

        # Contextual suggestions for '/theme'
        if self._themes and text.strip().startswith("/theme"):
            token = text.split(" ")[-1] if " " in text else ""
            prefix = token
            for name in self._themes:
                if not prefix or name.startswith(prefix):
                    yield Completion(
                        text=name,
                        start_position=-len(prefix),
                        display=name,
                        display_meta="Theme",
                    )
            return

        # No suggestions for other contexts
        return iter(())


class ModelMenuCompleter(Completer):
    """Completer that shows available models in a dropdown when typing '/'.

    Also supports filtering as the user types letters (autocomplete).

    Example usage in a prompt:
        prompt: "Select model (type '/' to view options): "
        completer: ModelMenuCompleter(models)
    """

    def __init__(self, models: Iterable[str]) -> None:
        self._models = list(models)

    def get_completions(self, document: Document, complete_event) -> Iterator[Completion]:  # type: ignore[override]
        text = document.text
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # When starting with '/', emulate the command-menu UX to list models
        if text.startswith("/") or text == "":
            prefix = word_before_cursor or text
            # Strip any leading '/' from the filter prefix
            filter_prefix = (prefix or "").lstrip("/")
            for name in self._models:
                if not filter_prefix or name.startswith(filter_prefix):
                    yield Completion(
                        text=name,
                        start_position=-len(prefix),
                        display=name,
                        display_meta="Model",
                    )
            return

        # Otherwise, provide standard prefix filtering as the user types
        prefix = word_before_cursor or ""
        for name in self._models:
            if not prefix or name.startswith(prefix):
                yield Completion(
                    text=name,
                    start_position=-len(prefix),
                    display=name,
                    display_meta="Model",
                )
        return
