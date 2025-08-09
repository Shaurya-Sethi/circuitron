"""Terminal UI implementation using Rich and prompt_toolkit."""

from typing import Iterable
from rich.console import Console


from .components.banner import Banner
from .components.prompt import Prompt
from .components.input_box import InputBox
from .components.completion import ModelMenuCompleter
from .components.code_panel import show_code
from .components.message_panel import MessagePanel
from .components.spinner import Spinner
from .components.status_bar import StatusBar
from .components import tables, panel
from .. import utils
from ..config import settings
from ..models import (
    PlanOutput,
    UserFeedback,
    CodeGenerationOutput,
    SelectedPart,
    PartSearchResult,
)

ACCENT = "cyan"


class TerminalUI:
    """Interactive terminal UI using Rich and prompt_toolkit."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.banner = Banner(self.console)
        self.spinner = Spinner(self.console)
        self.status_bar = StatusBar(self.console)
        self.prompt = Prompt(self.console)
        self.input_box = InputBox(self.console)

    def start_banner(self) -> None:
        """Render the Circuitron banner with gradient colors."""
        self.banner.show()
        self.console.print("[bold]Type /help for commands[/bold]\n", style=ACCENT)

    def start_stage(self, name: str) -> None:
        self.status_bar.update(stage=name, message="")
        self.spinner.start(name)

    def finish_stage(self, name: str) -> None:
        self.spinner.stop(name)
        self.status_bar.update(stage="Idle", message="")

    def prompt_user(self, message: str) -> str:
        """Prompt the user for input using ``Prompt`` component."""
        while True:
            text = self.input_box.ask(message)
            if text.strip() == "/help":
                self.console.print(
                    "Available commands: /model, /help",
                    style=ACCENT,
                )
                continue
            if text.strip() == "/model":
                # Ask the user to choose a model and update all agent model fields
                model_options = list(getattr(settings, "available_models", ["o4-mini", "gpt-5-mini"]))
                completer = ModelMenuCompleter(model_options)
                choice = self.input_box.ask(
                    "Select model (type '/' to view options): ",
                    completer=completer,
                ).strip()
                # Allow user to type '/gpt-...' and press enter without selecting
                choice = choice.lstrip('/')
                if choice not in set(model_options):
                    self.console.print(
                        f"Invalid model. Choose one of: {', '.join(model_options)}.",
                        style=ACCENT,
                    )
                    continue
                settings.set_all_models(choice)
                self.console.print(
                    f"Active model set to {choice} for all agents.",
                    style=ACCENT,
                )
                continue
            return text

    def display_plan(self, plan: PlanOutput) -> None:
        """Pretty print the generated plan."""
        text = utils.format_plan_summary(plan)
        panel.show_panel(self.console, "Design Plan", text)

    def collect_feedback(self, plan: PlanOutput) -> UserFeedback:
        return utils.collect_user_feedback(
            plan,
            input_func=self.prompt_user,
            console=self.console,
        )

    def display_files(self, files: Iterable[str]) -> None:
        links = "\n".join(f"[link=file://{p}]{p}[/]" for p in files)
        panel.show_panel(self.console, "Generated Files", links)

    def display_found_parts(self, found: Iterable[PartSearchResult]) -> None:
        data = {res.query: res.components for res in found}
        tables.show_found_parts(self.console, data)

    def display_selected_parts(self, parts: Iterable[SelectedPart]) -> None:
        tables.show_selected_parts(self.console, parts)

    def display_info(self, message: str) -> None:
        MessagePanel.info(self.console, message)

    def display_warning(self, message: str) -> None:
        MessagePanel.warning(self.console, message)

    def display_error(self, message: str) -> None:
        MessagePanel.error(self.console, message)

    def display_code(self, code: str, language: str = "python") -> None:
        show_code(
            self.console,
            code,
            language,
            title="Generated SKiDL Code",
        )

    def display_validation_summary(self, summary: str) -> None:
        """Show code validation results in a panel."""
        panel.show_panel(self.console, "Validation", summary)

    def display_generated_files_summary(self, files: Iterable[str]) -> None:
        links = "\n".join(f"[link=file://{p}]{p}[/]" for p in files)
        MessagePanel.info(self.console, links)

    async def run(
        self,
        prompt: str,
        show_reasoning: bool = False,
        retries: int = 0,
        output_dir: str | None = None,
        keep_skidl: bool = False,
    ) -> CodeGenerationOutput | None:
        """Execute the Circuitron pipeline with UI feedback.

        This method now manages the MCP server connection lifecycle so that the
        pipeline has an initialized server before any agents run.
        """

        from ..pipeline import run_with_retry
        from ..mcp_manager import mcp_manager

        await mcp_manager.initialize()
        try:
            self.status_bar.start()
            return await run_with_retry(
                prompt,
                show_reasoning=show_reasoning,
                retries=retries,
                output_dir=output_dir,
                keep_skidl=keep_skidl,
                ui=self,
            )
        finally:
            self.status_bar.stop()
            await mcp_manager.cleanup()
