from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ..themes import Theme


def show_code(
    console: Console,
    code: str,
    theme: Theme,
    language: str = "python",
    title: str = "Generated SKiDL Code",
) -> None:
    """Render ``code`` in a syntax highlighted panel."""
    syntax = Syntax(code, language, line_numbers=False)
    console.print(Panel(syntax, title=title, border_style=theme.accent))
