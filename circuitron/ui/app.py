"""Terminal UI implementation using Rich and prompt_toolkit."""

from typing import Iterable, Sequence
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
from rich.markup import escape
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
        self.console.print(
            "[bold]Type /help for commands. Press Ctrl+C any time to exit.[/bold]\n",
            style=ACCENT,
        )

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

    def display_files(self, files: Iterable[str] | dict[str, object]) -> None:
        """Show generated files in a compact table with a status summary.

        Accepts either a list of file paths or the full result dict from
        ``execute_final_script`` which may include success, stdout/stderr and files.
        """
        file_list: Sequence[str]
        header_lines: list[str] = []
        if isinstance(files, dict):
            success = bool(files.get("success", False))
            stdout = str(files.get("stdout", "")).strip()
            stderr = str(files.get("stderr", "")).strip()
            file_list = tuple(str(p) for p in files.get("files", []) if isinstance(p, str))

            status = "Success" if success else "Completed with issues"
            status_style = "green" if success else "yellow"
            header_lines.append(f"[bold {status_style}]{status}[/]")
            if stdout:
                safe_stdout = escape(stdout[:400])
                header_lines.append(f"[dim]stdout:[/] {safe_stdout}" + ("…" if len(stdout) > 400 else ""))
            if stderr:
                # Show only the first line or two to keep it tidy
                first_lines = " ".join(stderr.splitlines()[:2])
                safe_first = escape(first_lines)
                header_lines.append(f"[dim]notes:[/] {safe_first}")
        else:
            file_list = list(files)

        # Show summary header if we have any
        if header_lines:
            # Use markup mode so tags like [bold green] render as styles
            panel.show_panel(self.console, "Output Summary", "\n".join(header_lines), render="markup")

        # Render files table
        tables.show_generated_files(self.console, file_list)

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
        """Quick inline summary: count and first few file links."""
        files_list = list(files)
        n = len(files_list)
        preview = files_list[:3]
        links = ", ".join(f"[link=file://{p}]{p}[/]" for p in preview)
        extra = f" and {n-3} more" if n > 3 else ""
        MessagePanel.info(self.console, f"Saved {n} file(s): {links}{extra}")

    def display_erc_result(self, erc_result: dict[str, object]) -> None:
        """Render ERC outcome in plain English rather than raw JSON."""
        summary = utils.format_erc_result(erc_result)
        panel.show_panel(self.console, "ERC Result", summary)

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
