"""Table rendering helpers."""

from __future__ import annotations

from typing import Iterable

from rich.console import Console
from rich.table import Table

from ..themes import Theme
from ...models import SelectedPart, FoundPart


def show_found_parts(console: Console, parts: dict[str, list[FoundPart]], theme: Theme) -> None:
    """Render table of found components."""
    for query, plist in parts.items():
        table = Table(title=f"Results for {query}", border_style=theme.accent)
        table.add_column("Name")
        table.add_column("Library")
        for part in plist:
            table.add_row(part.name, part.library)
        console.print(table)


def show_selected_parts(console: Console, parts: Iterable[SelectedPart], theme: Theme) -> None:
    """Render table of selected components."""
    table = Table(title="Selected Components", border_style=theme.accent)
    table.add_column("Name")
    table.add_column("Library")
    table.add_column("Footprint")
    for part in parts:
        table.add_row(part.name, part.library, part.footprint or "")
    console.print(table)
