from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

ACCENT = "cyan"


def show_code(
    console: Console,
    code: str,
    language: str = "python",
    title: str = "Generated SKiDL Code",
) -> None:
    """Render ``code`` in a syntax highlighted panel."""
    syntax = Syntax(code, language, line_numbers=False)
    console.print(Panel(syntax, title=title, border_style=ACCENT))
