"""Static stage header (no live spinner) to avoid log interleaving.

We intentionally avoid Rich Live/Progress here. Instead, we print a compact
header when a stage begins and a single completion line when it ends.
This guarantees any streaming logs (including logfire traces) appear directly
below the header in strict order without rendering conflicts.
"""

from __future__ import annotations

from time import perf_counter

from rich.console import Console

ACCENT = "cyan"


class Spinner:
    """Print a static header for a stage; no animated/live rendering."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.start_time = 0.0
        self.current_stage: str | None = None

    def start(self, stage: str) -> None:
        """Print a stage header. Safe to call repeatedly; updates when changed."""
        if stage == self.current_stage:
            return
        self.current_stage = stage
        self.start_time = perf_counter()
        # A simple header that visually separates stages
        self.console.rule(f"[{ACCENT}]{stage}[/]")

    def stop(self, stage: str) -> None:
        if not self.current_stage:
            return
        elapsed = perf_counter() - self.start_time
        # Print a one-line completion summary.
        self.console.print(f"[green]{stage} complete ({elapsed:.1f}s)")
        self.current_stage = None

    def update(self, message: str | None = None) -> None:
        """No-op for compatibility; spinner is static by design."""
        _ = message
