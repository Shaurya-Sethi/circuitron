from __future__ import annotations

from typing import Iterable

from rich.console import Console
from rich.text import Text

from circuitron.logo import LOGO_ART, apply_gradient
from .themes import ELECTRIC_THEME, Theme
from .components.progress import StageSpinner
from .. import utils
from ..models import PlanOutput


class TerminalUI:
    """Simple interactive terminal UI using Rich."""

    def __init__(self, console: Console | None = None, theme: Theme | None = None) -> None:
        self.console = console or Console()
        self.theme = theme or ELECTRIC_THEME
        self.spinner = StageSpinner(self.console)

    def start_banner(self) -> None:
        """Render the Circuitron banner with gradient colors."""
        logo_text = Text.from_ansi(LOGO_ART)
        gradient_logo = apply_gradient(logo_text, self.theme.gradient_colors)
        self.console.print(gradient_logo, justify="center")
        self.console.print()

    def start_stage(self, name: str) -> None:
        self.spinner.start(name)

    def finish_stage(self, name: str) -> None:
        self.spinner.stop(name)

    def display_plan(self, plan: PlanOutput) -> None:
        """Pretty print the generated plan."""
        utils.pretty_print_plan(plan)

    def collect_feedback(self, plan: PlanOutput) -> utils.UserFeedback:
        return utils.collect_user_feedback(plan)

    def display_files(self, files: Iterable[str]) -> None:
        self.console.print("\n=== GENERATED FILES ===")
        for path in files:
            self.console.print(f"[link=file://{path}]{path}[/]")

    async def run(
        self,
        prompt: str,
        show_reasoning: bool = False,
        retries: int = 0,
        output_dir: str | None = None,
    ) -> utils.CodeGenerationOutput | None:
        """Execute the Circuitron pipeline with UI feedback."""
        from ..pipeline import run_with_retry

        self.start_banner()
        return await run_with_retry(
            prompt,
            show_reasoning=show_reasoning,
            retries=retries,
            output_dir=output_dir,
            ui=self,
        )
