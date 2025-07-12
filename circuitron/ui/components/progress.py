from __future__ import annotations

from rich.console import Console
from rich.status import Status


class StageSpinner:
    """Display a spinner while a pipeline stage is running."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.status: Status | None = None

    def start(self, stage: str) -> None:
        """Begin a spinner for ``stage``."""
        self.status = self.console.status(f"[bold cyan]{stage}...", spinner="dots")
        self.status.start()

    def stop(self, stage: str) -> None:
        """Stop the spinner and mark ``stage`` complete."""
        if self.status:
            self.status.update(f"[green]{stage} complete")
            self.status.stop()
            self.status = None
