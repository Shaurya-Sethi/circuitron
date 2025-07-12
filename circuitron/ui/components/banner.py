"""Banner component for displaying the Circuitron logo with a gradient."""

from __future__ import annotations

from rich.console import Console
from rich.text import Text

from ... import logo
from ..themes import Theme


class Banner:
    """Render the Circuitron ASCII art banner."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def show(self, theme: Theme) -> None:
        """Display the banner using ``theme`` gradient colors."""
        text = Text.from_ansi(logo.LOGO_ART)
        gradient = logo.apply_gradient(text, theme.gradient_colors)
        self.console.print(gradient, justify="center")
