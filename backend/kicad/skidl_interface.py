from __future__ import annotations

from skidl import ERC, Part, generate_netlist, generate_pcb, generate_schematic


class SkidlInterface:
    """Wrapper around SKiDL functions."""

    def search_part(self, query: str):
        """Search for a part using SKiDL."""
        return Part.search(query)

    def export_netlist(self, filename: str) -> None:
        generate_netlist(filename)

    def export_schematic(self, filename: str) -> None:
        generate_schematic(filename)

    def export_pcb(self, filename: str) -> None:
        generate_pcb(filename)

    def run_erc(self) -> int:
        """Run electrical rule check and return error count."""
        return ERC()
