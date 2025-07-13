"""Theme definitions and manager for Circuitron's terminal UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import json
import os

import circuitron.logo as logo

@dataclass
class Theme:
    """Color theme definition."""

    name: str
    gradient_colors: List[str]
    accent: str = "cyan"
    background: str = "black"
    foreground: str = "white"
    error: str = "red"


class ThemeManager:
    """Manage available themes and the active selection."""

    CONFIG_FILE = Path.home() / ".circuitron"

    def __init__(self) -> None:
        self.themes: Dict[str, Theme] = {
            name: Theme(name=name, gradient_colors=colors, accent="cyan")
            for name, colors in logo.THEMES.items()
        }
        # Built-in additional themes
        self.themes.update(
            {
                "dark": Theme(
                    "dark",
                    ["#1E1E2E", "#89B4FA", "#CBA6F7"],
                    accent="#89B4FA",
                    background="#1E1E2E",
                    foreground="#CDD6F4",
                    error="#F38BA8",
                ),
                "light": Theme(
                    "light",
                    ["#FFFFFF", "#CCCCCC", "#666666"],
                    accent="#4682B4",
                    background="#FFFFFF",
                    foreground="#222222",
                    error="red",
                ),
            }
        )
        self.active_theme: Theme = self.themes["electric"]
        self._load_from_file()

    def _load_from_file(self) -> None:
        if not self.CONFIG_FILE.exists():
            return
        try:
            data = json.loads(self.CONFIG_FILE.read_text())
        except Exception:
            return
        theme_name = data.get("theme")
        if theme_name and theme_name in self.themes:
            self.active_theme = self.themes[theme_name]

    def _save_to_file(self) -> None:
        try:
            self.CONFIG_FILE.write_text(json.dumps({"theme": self.active_theme.name}))
        except Exception:
            pass

    def get_theme(self) -> Theme:
        if os.environ.get("NO_COLOR"):
            return Theme(
                "nocolor",
                ["white"],
                accent="white",
                background="black",
                foreground="white",
                error="white",
            )
        return self.active_theme

    def set_theme(self, name: str) -> None:
        if name not in self.themes:
            raise ValueError(f"Unknown theme: {name}")
        self.active_theme = self.themes[name]
        self._save_to_file()

    def available_themes(self) -> Iterable[str]:
        return self.themes.keys()


# Singleton theme manager used across the application
theme_manager = ThemeManager()

# Default electric theme used by the Terminal UI
ELECTRIC_THEME = theme_manager.get_theme()
