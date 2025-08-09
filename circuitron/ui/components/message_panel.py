from __future__ import annotations

from rich.console import Console
from rich.panel import Panel


ACCENT = "cyan"


class MessagePanel:
    """Helper class for info/warning/error panels."""

    @staticmethod
    def info(console: Console, text: str) -> None:
        console.print(Panel(text, border_style=ACCENT))

    @staticmethod
    def warning(console: Console, text: str) -> None:
        console.print(Panel(text, border_style="yellow"))

    @staticmethod
    def error(console: Console, text: str) -> None:
        console.print(Panel(text, border_style="red"))
