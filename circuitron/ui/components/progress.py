from __future__ import annotations

from rich.console import Console
from rich.status import Status
from time import perf_counter


class StageSpinner:
    """Display a spinner while a pipeline stage is running."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.status: Status | None = None
        self.start_time = 0.0

    def start(self, stage: str) -> None:
        """Begin a spinner for ``stage``."""
        self.start_time = perf_counter()
        self.status = self.console.status(f"[bold cyan]{stage}...", spinner="dots")
        self.status.start()

    def stop(self, stage: str) -> None:
        """Stop the spinner and mark ``stage`` complete."""
        if self.status:
            elapsed = perf_counter() - self.start_time
            self.status.update(f"[green]{stage} complete ({elapsed:.1f}s)")
            self.status.stop()
            self.status = None
