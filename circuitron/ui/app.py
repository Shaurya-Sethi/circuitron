"""Terminal UI implementation using Rich and prompt_toolkit."""

from typing import Iterable
from rich.console import Console


from .themes import Theme, theme_manager
from .components.banner import Banner
from .components.prompt import Prompt
from .components.input_box import InputBox
from .components.code_panel import show_code
from .components.message_panel import MessagePanel
from .components.spinner import Spinner
from .components.status_bar import StatusBar
from .components import tables, panel
from .. import utils
from ..models import (
    PlanOutput,
    UserFeedback,
    CodeGenerationOutput,
    SelectedPart,
    PartSearchResult,
)


class TerminalUI:
    """Interactive terminal UI using Rich and prompt_toolkit."""

    def __init__(self, console: Console | None = None, theme: Theme | None = None) -> None:
        self.console = console or Console()
        self.theme = theme or theme_manager.get_theme()
        self.banner = Banner(self.console)
        self.spinner = Spinner(self.console, self.theme)
        self.status_bar = StatusBar(self.console, self.theme)
        self.prompt = Prompt(self.console, self.theme)
        self.input_box = InputBox(self.console, self.theme)

    def start_banner(self) -> None:
        """Render the Circuitron banner with gradient colors."""
        self.banner.show(self.theme)
        self.console.print("[bold]Type /help for commands[/bold]\n", style=self.theme.accent)

    def set_theme(self, name: str) -> None:
        """Switch to a new theme."""
        theme_manager.set_theme(name)
        self.theme = theme_manager.get_theme()
        self.spinner.theme = self.theme
        self.status_bar.theme = self.theme
        self.prompt.theme = self.theme
        self.input_box.theme = self.theme

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
                self.console.print("Available commands: /theme <name>, /help", style=self.theme.accent)
                continue
            if text.startswith("/theme"):
                parts = text.split()
                if len(parts) == 2 and parts[1] in theme_manager.available_themes():
                    self.set_theme(parts[1])
                    self.console.print(f"Theme switched to {parts[1]}", style=self.theme.accent)
                else:
                    self.console.print(
                        f"Available themes: {', '.join(theme_manager.available_themes())}",
                        style=self.theme.accent,
                    )
                continue
            return text

    def display_plan(self, plan: PlanOutput) -> None:
        """Pretty print the generated plan."""
        text = utils.format_plan_summary(plan)
        panel.show_panel(self.console, "Design Plan", text, self.theme)

    def collect_feedback(self, plan: PlanOutput) -> UserFeedback:
        return utils.collect_user_feedback(
            plan,
            input_func=self.prompt_user,
            console=self.console,
        )

    def display_files(self, files: Iterable[str]) -> None:
        links = "\n".join(f"[link=file://{p}]{p}[/]" for p in files)
        panel.show_panel(self.console, "Generated Files", links, self.theme)

    def display_found_parts(self, found: Iterable[PartSearchResult]) -> None:
        data = {res.query: res.components for res in found}
        tables.show_found_parts(self.console, data, self.theme)

    def display_selected_parts(self, parts: Iterable[SelectedPart]) -> None:
        tables.show_selected_parts(self.console, parts, self.theme)

    def display_info(self, message: str) -> None:
        MessagePanel.info(self.console, message, self.theme)

    def display_warning(self, message: str) -> None:
        MessagePanel.warning(self.console, message, self.theme)

    def display_error(self, message: str) -> None:
        MessagePanel.error(self.console, message, self.theme)

    def display_code(self, code: str, language: str = "python") -> None:
        show_code(
            self.console,
            code,
            self.theme,
            language,
            title="Generated SKiDL Code",
        )

    def display_validation_summary(self, summary: str) -> None:
        """Show code validation results in a panel."""
        panel.show_panel(self.console, "Validation", summary, self.theme)

    def display_generated_files_summary(self, files: Iterable[str]) -> None:
        links = "\n".join(f"[link=file://{p}]{p}[/]" for p in files)
        MessagePanel.info(self.console, links, self.theme)

    async def run(
        self,
        prompt: str,
        show_reasoning: bool = False,
        retries: int = 0,
        output_dir: str | None = None,
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
                ui=self,
            )
        finally:
            self.status_bar.stop()
            await mcp_manager.cleanup()
