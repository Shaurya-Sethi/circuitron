from __future__ import annotations


class DesignAgent:
    """Orchestrates the design workflow."""

    async def plan(self, prompt: str) -> str:
        """Create a design plan."""
        return f"Plan for: {prompt}"

    async def generate_skidl(self, plan: str) -> str:
        """Generate SKiDL code from plan."""
        pass

    async def review(self, code: str) -> bool:
        """Review generated code."""
        pass

    async def export_files(self, code: str) -> dict[str, str]:
        """Produce design artefacts from SKiDL code."""
        pass
