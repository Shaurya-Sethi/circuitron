"""Simple persistent status bar.

Emits succinct one-line updates via ``console.log`` so messages appear above
any active Rich Progress spinner (single Live display).
"""

from __future__ import annotations

from dataclasses import dataclass
from rich.console import Console
from rich.text import Text

ACCENT = "cyan"


@dataclass
class Status:
    """Current pipeline status."""

    stage: str = "Idle"
    message: str = ""


class StatusBar:
    """Display current pipeline stage and message."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.status = Status()
        self.started = False
        self._last_rendered: tuple[str, str] | None = None

    def start(self) -> None:
        self.started = True
        self.update()

    def stop(self) -> None:
        if self.started:
            # End of session marker; avoid extra newline spam.
            self.started = False

    def update(self, stage: str | None = None, message: str | None = None) -> None:
        if stage is not None:
            self.status.stage = stage
        if message is not None:
            self.status.message = message
        if self.started:
            # Render as a regular print to avoid file:line decorations of log().
            # Progress redirect keeps this above the spinner line.
            stage_s = self.status.stage
            msg_s = self.status.message
            curr = (stage_s, msg_s)
            if self._last_rendered == curr:
                return
            self._last_rendered = curr
            content = f"{stage_s} - {msg_s}" if msg_s else f"{stage_s}"
            style = ACCENT if msg_s else "dim"
            self.console.print(Text(content, style=style))
