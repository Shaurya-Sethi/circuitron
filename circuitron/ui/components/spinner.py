"""Enhanced spinner with elapsed time."""

from __future__ import annotations

from time import perf_counter

from rich.console import Console
from rich.status import Status

from ..themes import Theme


class Spinner:
    """Display a spinner while a stage runs."""

    def __init__(self, console: Console, theme: Theme) -> None:
        self.console = console
        self.theme = theme
        self.status: Status | None = None
        self.start_time = 0.0

    def start(self, stage: str) -> None:
        self.start_time = perf_counter()
        self.status = self.console.status(f"[{self.theme.accent}]{stage}...", spinner="dots")
        self.status.start()

    def stop(self, stage: str) -> None:
        if not self.status:
            return
        elapsed = perf_counter() - self.start_time
        self.status.update(f"[green]{stage} complete ({elapsed:.1f}s)")
        self.status.stop()
        self.status = None
