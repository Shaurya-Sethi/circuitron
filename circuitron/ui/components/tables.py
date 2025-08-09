"""Table rendering helpers."""

from __future__ import annotations

from typing import Iterable

from rich.console import Console
from rich.table import Table
from rich import box

from ...models import SelectedPart, FoundPart

ACCENT = "cyan"


def show_found_parts(console: Console, parts: dict[str, list[FoundPart]]) -> None:
    """Render a unified table of found components."""
    table = Table(title="Found Components", border_style=ACCENT, box=box.SIMPLE)
    table.add_column("Query", style=ACCENT)
    table.add_column("Name")
    table.add_column("Library")
    for query, plist in parts.items():
        for part in plist:
            table.add_row(query, part.name, part.library)
    console.print(table)


def show_selected_parts(console: Console, parts: Iterable[SelectedPart]) -> None:
    """Render table of selected components."""
    table = Table(
        title="Selected Components",
        border_style=ACCENT,
        box=box.SIMPLE,
        expand=False,
    )
    table.add_column("Name", style=ACCENT)
    table.add_column("Library")
    table.add_column("Footprint")
    for part in parts:
        table.add_row(part.name, part.library, part.footprint or "")
    console.print(table)
