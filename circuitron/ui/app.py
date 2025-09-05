"""Terminal UI implementation using Rich and prompt_toolkit."""

from typing import Any, Iterable, Mapping, Sequence
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
        # Hide file:line in log entries to keep the UI clean; keep timestamps.
        self.console = console or Console(log_path=False, log_time=True)
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
                    "Available commands:\n"
                    "  /model — switch the active LLM model for all agents\n"
                    "  /about — what Circuitron is and how it works\n"
                    "  /help — show this help",
                    style=ACCENT,
                )
                continue
            if text.strip() == "/about":
                about_md = (
                    "# Circuitron\n\n"
                    "Circuitron is an AI-powered PCB design accelerator that turns natural language\n"
                    "requirements into SKiDL scripts, KiCad schematics, and PCB layouts.\n\n"
                    "## How it works (high level)\n"
                    "1. Planning — A planning agent drafts a design plan.\n\n"
                    "2. Optional user edits — You can review and refine the plan.\n\n"
                    "3. Part search & selection — Agents find candidate parts and select the best fit.\n\n"
                    "4. Documentation context (RAG) — A documentation agent gathers relevant references.\n\n"
                    "5. Code generation — The system generates SKiDL and related scripts.\n\n"
                    "6. Validation & correction — A validator checks the code; a corrector fixes issues until valid.\n\n"
                    "7. Runtime check (Docker) — Scripts are executed in an isolated container; a runtime corrector\n"
                    "   iterates on failures.\n\n"
                    "8. ERC loop — Electrical Rule Checks run and are handled until clean or accepted.\n\n"
                    "9. Final output — KiCad files and artifacts are produced in the output folder.\n\n"
                    "Use /model to change the active model at any time. Press Ctrl+C to exit."
                )
                from .components import panel as panel_comp
                panel_comp.show_panel(self.console, "About Circuitron", about_md)
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
            files_val = files.get("files", [])
            files_iter = files_val if isinstance(files_val, Iterable) else []
            file_list = tuple(str(p) for p in files_iter if isinstance(p, str))

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
    ) -> CodeGenerationOutput | None:
        """Execute the Circuitron pipeline with UI feedback.

        This method now manages the MCP server connection lifecycle so that the
        pipeline has an initialized server before any agents run.
        """

        from ..pipeline import run_with_retry
        from ..mcp_manager import mcp_manager

        await mcp_manager.initialize()
        # Initialize summary timers and counters
        import time
        from ..telemetry import token_usage_aggregator
        token_usage_aggregator.reset()
        start_ts = time.perf_counter()
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
            # Compute and show end-of-run summary
            try:
                elapsed = time.perf_counter() - start_ts
                token_summary = token_usage_aggregator.get_summary()
                from ..cost_estimator import estimate_cost_usd, estimate_cost_usd_for_model

                total_cost, used_default, per_model = estimate_cost_usd(token_summary)
                # If per-model pricing failed (or was zero), fall back to the active model
                if total_cost == 0.0:
                    from ..config import settings as cfg
                    # Use code_generation_model as representative of main cost; user can change via /model
                    model_name = str(
                        getattr(cfg, "code_generation_model", None)
                        or getattr(cfg, "planning_model", "o4-mini")
                    )
                    total_cost2, used_default2 = estimate_cost_usd_for_model(token_summary, model_name)
                    # Prefer non-zero fallback
                    if total_cost2 > 0.0 or used_default:
                        total_cost, used_default = total_cost2, used_default2
                self.display_summary_stats(elapsed, token_summary, total_cost, used_default)
            except Exception:
                # Never break shutdown flow if summary fails
                pass

    def display_summary_stats(
        self,
        elapsed_seconds: float,
        token_summary: Mapping[str, Any],
        total_cost_usd: float,
        used_default_prices: bool,
    ) -> None:
        """Render a compact summary panel with time, tokens, and cost."""
        from .components import panel as panel_comp

        overall = token_summary.get("overall", {})
        i = int(overall.get("input", 0))
        o = int(overall.get("output", 0))
        t = int(overall.get("total", i + o))

        # Format time hh:mm:ss.mmm
        hours = int(elapsed_seconds // 3600)
        minutes = int((elapsed_seconds % 3600) // 60)
        seconds = elapsed_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"

        lines = [
            f"Time taken: {time_str}",
            f"Tokens: in={i:,} out={o:,} total={t:,}",
            f"Estimated cost: ${total_cost_usd:.4f}",
        ]
        if used_default_prices:
            lines.append("(Note: Missing local pricing for some/all models; cost may be 0)")

        lines.append("")
        lines.append("[dim]Circuitron powering down...[/dim]")
        text = "\n".join(lines)
        panel_comp.show_panel(self.console, "Run Summary", text, render="markup")
