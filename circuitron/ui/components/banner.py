"""Banner component for displaying the Circuitron logo with a gradient."""

from __future__ import annotations

from rich.console import Console
from rich.text import Text

from ... import logo


class Banner:
    """Render the Circuitron ASCII art banner."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def show(self) -> None:
        """Display the banner using the default gradient colors."""
        text = Text.from_ansi(logo.LOGO_ART)
        # Use a fixed, default gradient (previously the 'electric' theme)
        gradient = logo.apply_gradient(text, logo.THEMES.get("electric", ["#66CCFF", "#4682B4"]))
        self.console.print(gradient, justify="center")
