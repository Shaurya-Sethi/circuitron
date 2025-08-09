"""Utility for simple panels.

Provides a small helper to render content inside a Rich Panel. By default,
content is interpreted as Markdown. For strings containing Rich markup tags
like ``[bold green]...[/]``, pass ``render="markup"`` to correctly style the
text instead of printing the literal tags.
"""

from __future__ import annotations

from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel

ACCENT = "cyan"


def show_panel(console: Console, title: str, content: str, *, render: str = "markdown") -> None:
    """Render content inside a styled panel.

    Args:
        console: Rich console to print to.
        title: Panel title.
        content: String content to render.
        render: Rendering mode. One of:
            - "markdown" (default): interpret content as Markdown
            - "markup": interpret content as Rich markup via Text.from_markup
            - "plain": render content as plain text with no special parsing
    """
    if render == "markup":
        body = Text.from_markup(content)
    elif render == "plain":
        body = Text(content)
    else:  # markdown
        body = Markdown(content)

    panel = Panel(body, title=title, border_style=ACCENT, expand=False)
    console.print(panel)
