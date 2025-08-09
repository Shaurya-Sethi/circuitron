"""Utility for simple panels."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

ACCENT = "cyan"


def show_panel(console: Console, title: str, content: str) -> None:
    """Render ``content`` markdown inside a styled panel."""
    panel = Panel(Markdown(content), title=title, border_style=ACCENT, expand=False)
    console.print(panel)
