"""Utility for themed panels."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..themes import Theme


def show_panel(console: Console, title: str, content: str, theme: Theme) -> None:
    """Render ``content`` markdown inside a styled panel."""
    panel = Panel(Markdown(content), title=title, border_style=theme.accent, expand=False)
    console.print(panel)
