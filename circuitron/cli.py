"""Command line interface for Circuitron."""

import asyncio
from .config import setup_environment, settings
from .models import CodeGenerationOutput
from circuitron.tools import kicad_session
from .mcp_manager import mcp_manager
from .network import check_internet_connection
from .exceptions import PipelineError
from circuitron.ui.app import TerminalUI
from .progress import ProgressSink


async def run_circuitron(
    prompt: str,
    show_reasoning: bool = False,
    retries: int = 0,
    output_dir: str | None = None,
    ui: TerminalUI | None = None,
) -> CodeGenerationOutput | None:
    """Execute the Circuitron workflow using the full pipeline with retries."""

    from circuitron.pipeline import run_with_retry

    ui = ui or TerminalUI()
    await mcp_manager.initialize()
    try:
        try:
            return await run_with_retry(
                prompt,
                show_reasoning=show_reasoning,
                retries=retries,
                output_dir=output_dir,
            )
        except PipelineError as exc:
            ui.display_error(f"Fatal error: {exc}")
            return None
    finally:
        await mcp_manager.cleanup()


def verify_containers(ui: TerminalUI | None = None) -> bool:
    """Ensure required Docker containers are running."""

    try:
        kicad_session.start()
        return True
    except Exception as exc:
        (ui or TerminalUI()).display_error(f"Failed to start KiCad container: {exc}")
        return False


def main() -> None:
    """Main entry point for the Circuitron system."""
    from circuitron.pipeline import parse_args

    args = parse_args()
    setup_environment(dev=args.dev)
    ui = TerminalUI()
    if args.no_footprint_search:
        settings.footprint_search_enabled = False

    if not check_internet_connection():
        ui.display_error("No internet connection detected. Please connect and try again.")
        return

    if not verify_containers(ui=ui):
        return

    ui.start_banner()
    prompt = args.prompt or ui.prompt_user("What would you like me to design?")
    show_reasoning = args.reasoning
    retries = args.retries
    output_dir = args.output_dir
    keep_skidl = args.keep_skidl

    code_output: CodeGenerationOutput | None = None
    try:
        try:
            code_output = asyncio.run(
                ui.run(prompt, show_reasoning=show_reasoning, retries=retries, output_dir=output_dir, keep_skidl=keep_skidl)
            )
        except KeyboardInterrupt:
            ui.console.print("\nExecution interrupted by user.", style="red")
        except Exception as exc:
            ui.console.print(f"Error during execution: {exc}", style="red")
    finally:
        kicad_session.stop()

    if code_output:
        ui.display_code(code_output.complete_skidl_code)
        ui.display_info("\nGenerated files have been saved to the output directory.")
        ui.display_info("Use --output-dir to specify a custom location.")
        ui.display_info("Default location: ./circuitron_output")


if __name__ == "__main__":
    main()
