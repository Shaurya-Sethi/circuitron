from dataclasses import dataclass
from typing import List

import circuitron.logo as logo

@dataclass
class Theme:
    """Simple color theme with gradient colors."""

    name: str
    gradient_colors: List[str]
    accent: str = "cyan"


def get_theme(name: str) -> Theme:
    """Return a theme by name."""
    colors = logo.THEMES.get(name)
    if not colors:
        raise ValueError(f"Unknown theme: {name}")
    return Theme(name=name, gradient_colors=colors)


# Default electric theme used by the Terminal UI
ELECTRIC_THEME = get_theme("electric")
