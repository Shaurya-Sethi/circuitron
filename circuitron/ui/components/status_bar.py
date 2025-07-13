"""Simple persistent status bar."""

from __future__ import annotations

from dataclasses import dataclass
from rich.console import Console
from rich.text import Text

from ..themes import Theme


@dataclass
class Status:
    """Current pipeline status."""

    stage: str = "Idle"
    message: str = ""


class StatusBar:
    """Display current pipeline stage and message."""

    def __init__(self, console: Console, theme: Theme) -> None:
        self.console = console
        self.theme = theme
        self.status = Status()
        self.started = False

    def start(self) -> None:
        self.started = True
        self.update()

    def stop(self) -> None:
        if self.started:
            self.console.print()
            self.started = False

    def update(self, stage: str | None = None, message: str | None = None) -> None:
        if stage is not None:
            self.status.stage = stage
        if message is not None:
            self.status.message = message
        if self.started:
            text = Text(f"{self.status.stage} - {self.status.message}", style=self.theme.accent)
            self.console.print(text)
