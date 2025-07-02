import argparse
import time
from typing import cast

from rich.color import Color
from rich.console import Console
from rich.style import Style
from rich.text import Text

LOGO_ART = """
 ██████╗ ██╗██████╗  ██████╗██╗   ██╗██╗████████╗██████╗  ██████╗ ███╗   ██╗
██╔════╝ ██║██╔══██╗██╔════╝██║   ██║██║╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║
██║      ██║██████╔╝██║     ██║   ██║██║   ██║   ██████╔╝██║   ██║██╔██╗ ██║
██║      ██║██╔══██╗██║     ██║   ██║██║   ██║   ██╔══██╗██║   ██║██║╚██╗██║
╚██████╗ ██║██║  ██║╚██████╗╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
"""

THEMES = {
    "fire": ["#FFD700", "#FF8C00", "#FF4500", "#DC143C"],
    "electric": ["#FFFF66", "#CCFF66", "#66FFCC", "#66CCFF", "#4682B4"],
    "solarized_dark": ["#002B36", "#586E75", "#839496", "#93A1A1", "#EEE8D5"],
    "sunset": ["#FF7E5F", "#FEB47B"],
    "pastel": ["#FFB3B3", "#FFD1A3", "#FBFFA3", "#A3FFCD", "#A3D1FF"]
}

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converts a hex color string to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return cast(tuple[int, int, int], tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)))

def interpolate_color(
    start_rgb: tuple[int, int, int],
    end_rgb: tuple[int, int, int],
    factor: float,
) -> tuple[int, int, int]:
    """Linearly interpolate between two RGB colors."""
    return cast(
        tuple[int, int, int],
        tuple(
            int(start + (end - start) * factor)
            for start, end in zip(start_rgb, end_rgb)
        ),
    )

def apply_gradient(text: Text, colors: list[str]) -> Text:
    """Apply a horizontal gradient to a ``Text`` object."""
    if not colors:
        return text

    if len(colors) == 1:
        return Text(text.plain, style=Style(color=Color.from_rgb(*hex_to_rgb(colors[0]))))

    rgb_colors = [hex_to_rgb(c) for c in colors]
    
    lines = text.plain.splitlines()
    if not lines:
        return Text("")

    max_len = max(len(line) for line in lines)
    if max_len == 0:
        return Text("")

    new_text = Text()
    for line in lines:
        for i, char in enumerate(line):
            if char.isspace():
                new_text.append(char)
                continue
            
            position_factor = i / max_len
            color_segment = (len(rgb_colors) - 1) * position_factor
            start_index = min(int(color_segment), len(rgb_colors) - 2)
            end_index = start_index + 1
            
            segment_factor = color_segment - start_index
            
            start_rgb = rgb_colors[start_index]
            end_rgb = rgb_colors[end_index]
            
            r, g, b = interpolate_color(start_rgb, end_rgb, segment_factor)
            style = Style(color=Color.from_rgb(r, g, b))
            new_text.append(char, style=style)
        new_text.append("\n")
    return new_text

def main() -> None:
    """Display the CIRCUITRON banner with an optional color theme."""
    parser = argparse.ArgumentParser(description="Display the CIRCUITRON banner with various color themes.")
    parser.add_argument("--theme", type=str, choices=THEMES.keys(), help="Specify the color theme to use.")
    args = parser.parse_args()

    console = Console()
    logo_text = Text.from_ansi(LOGO_ART)

    if args.theme:
        console.print(f"\nDisplaying CIRCUITRON banner with '{args.theme}' theme...\n")
        gradient_colors = THEMES[args.theme]
        gradient_logo = apply_gradient(logo_text, gradient_colors)
        console.print(gradient_logo, justify="center")
    else:
        console.print("\nDisplaying CIRCUITRON banner with all available themes...\n")
        for theme_name, gradient_colors in THEMES.items():
            console.print(f"--- Theme: {theme_name} ---", style="bold yellow")
            gradient_logo = apply_gradient(logo_text, gradient_colors)
            console.print(gradient_logo, justify="center")
            console.print()

    console.print("\nTo use this in your application, you can adapt this script.", style="italic cyan")
    console.print("You can easily change the ASCII art or the gradient colors in the script.", style="italic cyan")
    console.print("Requires the 'rich' library: [bold]pip install rich[/bold]", style="cyan")
    console.print(f"To see a specific theme, run: [bold]python {__file__} --theme <theme_name>[/bold]", style="cyan")
    console.print(f"Available themes: {', '.join(THEMES.keys())}", style="cyan")


if __name__ == "__main__":
    main()
