"""Table rendering helpers."""

from __future__ import annotations

from typing import Iterable
import os

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


def _human_size(num_bytes: int) -> str:
    """Return a human-friendly size string for bytes."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{int(num_bytes)} B"


def _file_type_label(path: str) -> str:
    """Map file extension to a friendly type label with a subtle icon."""
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    mapping = {
        ".kicad_sch": "🧩 Schematic",
        ".kicad_pcb": "🧱 PCB",
        ".sch": "🧩 Schematic",
        ".pcb": "🧱 PCB",
        ".net": "🔗 Netlist",
        ".xml": "🗂️ XML",
        ".csv": "📊 CSV",
        ".pdf": "📄 PDF",
        ".zip": "🗜️ ZIP",
        ".py": "🐍 Python",
        ".log": "📝 Log",
        ".txt": "📄 Text",
    }
    return mapping.get(ext, (ext[1:].upper() + " File") if ext else "File")


def show_generated_files(console: Console, file_paths: Iterable[str]) -> None:
    """Render a compact table of generated files with size and open links."""
    paths = list(file_paths)
    table = Table(title="Generated Files", border_style=ACCENT, box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style=ACCENT, no_wrap=True)
    table.add_column("Name", overflow="fold")
    table.add_column("Type", no_wrap=True)
    table.add_column("Size", justify="right", no_wrap=True)
    table.add_column("Open", no_wrap=True)

    for idx, p in enumerate(paths, start=1):
        name = os.path.basename(p)
        exists = os.path.exists(p)
        size = _human_size(os.path.getsize(p)) if exists and os.path.isfile(p) else "—"
        ftype = _file_type_label(p)
        name_link = f"[link=file://{p}]{name}[/]" if exists else name
        open_link = f"[link=file://{p}]Open[/]" if exists else "—"
        table.add_row(str(idx), name_link, ftype, size, open_link)

    console.print(table)
