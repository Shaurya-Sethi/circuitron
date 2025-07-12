"""Terminal UI implementation using Rich and prompt_toolkit."""

from typing import Iterable
from pathlib import Path

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
import sys

from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.history import FileHistory  # type: ignore

from circuitron.logo import LOGO_ART, apply_gradient
from .themes import Theme, theme_manager
from .components.progress import StageSpinner
from .. import utils
from ..models import PlanOutput


class TerminalUI:
    """Interactive terminal UI using Rich and prompt_toolkit."""

    def __init__(self, console: Console | None = None, theme: Theme | None = None) -> None:
        self.console = console or Console()
        self.theme = theme or theme_manager.get_theme()
        self.spinner = StageSpinner(self.console)
        history_file = Path.home() / ".circuitron_history"
        self.session: PromptSession = PromptSession(
            history=FileHistory(str(history_file))
        )

    def start_banner(self) -> None:
        """Render the Circuitron banner with gradient colors."""
        logo_text = Text.from_ansi(LOGO_ART)
        gradient_logo = apply_gradient(logo_text, self.theme.gradient_colors)
        self.console.print(gradient_logo, justify="center")
        self.console.print("[bold]Type /help for commands[/bold]\n")

    def set_theme(self, name: str) -> None:
        """Switch to a new theme."""
        theme_manager.set_theme(name)
        self.theme = theme_manager.get_theme()

    def start_stage(self, name: str) -> None:
        self.spinner.start(name)

    def finish_stage(self, name: str) -> None:
        self.spinner.stop(name)

    def prompt_user(self, message: str) -> str:
        """Prompt the user for input using prompt_toolkit."""
        while True:
            if not sys.stdin.isatty():
                text = input(f"{message}: ")
            else:
                text = self.session.prompt(f"{message}: ")
            if text.strip() == "/help":
                self.console.print("Available commands: /theme <name>, /help")
                continue
            if text.startswith("/theme"):
                parts = text.split()
                if len(parts) == 2 and parts[1] in theme_manager.available_themes():
                    self.set_theme(parts[1])
                    self.console.print(f"Theme switched to {parts[1]}")
                else:
                    self.console.print(f"Available themes: {', '.join(theme_manager.available_themes())}")
                continue
            return text

    def display_plan(self, plan: PlanOutput) -> None:
        """Pretty print the generated plan."""
        utils.pretty_print_plan(plan, console=self.console)

    def collect_feedback(self, plan: PlanOutput) -> utils.UserFeedback:
        return utils.collect_user_feedback(plan, input_func=self.prompt_user)

    def display_files(self, files: Iterable[str]) -> None:
        links = "\n".join(f"[link=file://{p}]{p}[/]" for p in files)
        self.console.print(Panel(Markdown(links), title="Generated Files", expand=False))

    async def run(
        self,
        prompt: str,
        show_reasoning: bool = False,
        retries: int = 0,
        output_dir: str | None = None,
    ) -> utils.CodeGenerationOutput | None:
        """Execute the Circuitron pipeline with UI feedback."""
        from ..pipeline import run_with_retry

        return await run_with_retry(
            prompt,
            show_reasoning=show_reasoning,
            retries=retries,
            output_dir=output_dir,
            ui=self,
        )
