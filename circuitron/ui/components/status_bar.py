"""Simple persistent status bar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from rich.console import Console
from rich.live import Live
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
        self._live: Optional[Live] = None

    def start(self) -> None:
        self._live = Live(refresh_per_second=4, console=self.console)
        self._live.__enter__()
        self.update()

    def stop(self) -> None:
        if self._live:
            self._live.__exit__(None, None, None)
            self._live = None

    def update(self, stage: str | None = None, message: str | None = None) -> None:
        if stage is not None:
            self.status.stage = stage
        if message is not None:
            self.status.message = message
        if self._live:
            text = Text(f"{self.status.stage} - {self.status.message}", style=self.theme.accent)
            self._live.update(text)
