from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from ..themes import Theme


class MessagePanel:
    """Helper class for info/warning/error panels."""

    @staticmethod
    def info(console: Console, text: str, theme: Theme) -> None:
        console.print(Panel(text, border_style=theme.accent))

    @staticmethod
    def warning(console: Console, text: str, theme: Theme) -> None:
        console.print(Panel(text, border_style="yellow"))

    @staticmethod
    def error(console: Console, text: str, theme: Theme) -> None:
        console.print(Panel(text, border_style="red"))
