"""Command line interface for Circuitron."""

import asyncio
import signal
import sys
from types import FrameType

from .config import setup_environment, settings
from .models import CodeGenerationOutput
from circuitron.tools import kicad_session
from .mcp_manager import mcp_manager
from .network import check_internet_connection
from .exceptions import PipelineError
from circuitron.ui.app import TerminalUI


def _handle_termination(signum: int, _frame: FrameType | None) -> None:
    """Stop KiCad session and exit on SIGINT or SIGTERM.

    ``DockerSession`` also registers :func:`kicad_session.stop` with ``atexit``,
    so this handler is an eager cleanup while ``atexit`` remains a fallback.
    """
    # Show a friendly goodbye on Ctrl+C or termination
    try:
        from circuitron.ui.app import TerminalUI  # local import to avoid circular at module load
        ui = TerminalUI()
        ui.console.print("\nGoodbye! Thanks for using Circuitron.", style="yellow")
    except Exception:
        print("\nGoodbye! Thanks for using Circuitron.")
    kicad_session.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, _handle_termination)
signal.signal(signal.SIGTERM, _handle_termination)


async def run_circuitron(
    prompt: str,
    show_reasoning: bool = False,
    retries: int = 0,
    output_dir: str | None = None,
    ui: TerminalUI | None = None,
) -> CodeGenerationOutput | None:
    """Execute the Circuitron workflow using the full pipeline with retries."""

    from circuitron.pipeline import run_with_retry

    # Defer UI construction to avoid prompt_toolkit console issues in headless tests
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
            if ui is None:
                # Fall back to plain print to avoid instantiating TerminalUI in tests
                print(f"Fatal error: {exc}")
            else:
                ui.display_error(f"Fatal error: {exc}")
            return None
    except (KeyboardInterrupt, EOFError):
        if ui is None:
            print("\nGoodbye! Thanks for using Circuitron.")
        else:
            ui.console.print("\nGoodbye! Thanks for using Circuitron.", style="yellow")
        return None
    finally:
        await mcp_manager.cleanup()


def verify_containers(ui: TerminalUI | None = None) -> bool:
    """Ensure required Docker containers are running."""

    try:
        kicad_session.start()
    except Exception as exc:
        if ui is None:
            # Avoid creating a full TerminalUI in headless or test environments
            print(f"Failed to start KiCad container: {exc}")
        else:
            ui.display_error(f"Failed to start KiCad container: {exc}")
        return False
    return True


def main() -> None:
    """Main entry point for the Circuitron system."""
    from circuitron.pipeline import parse_args

    args = parse_args()
    setup_environment(getattr(args, "dev", False), use_dotenv=True)
    # Setup subcommand (knowledge base initialization) — isolated from pipeline
    if getattr(args, "command", None) == "setup":
        from circuitron.setup import run_setup
        ui = TerminalUI()
        ui.start_banner()
        try:
            # Do not start KiCad containers; this path only uses MCP tools
            _ = asyncio.run(
                run_setup(
                    getattr(args, "docs_url", "https://devbisme.github.io/skidl/"),
                    getattr(args, "repo_url", "https://github.com/devbisme/skidl"),
                    ui=ui,
                    timeout=getattr(args, "timeout", None),
                )
            )
        except (KeyboardInterrupt, EOFError):
            ui.console.print("\nGoodbye! Thanks for using Circuitron.", style="yellow")
        return
    ui = TerminalUI()
    if args.no_footprint_search:
        settings.footprint_search_enabled = False

    if not check_internet_connection():
        return

    if not verify_containers(ui=ui):
        return

    ui.start_banner()
    try:
        prompt = args.prompt or ui.prompt_user("What would you like me to design?")
    except (KeyboardInterrupt, EOFError):
        ui.console.print("\nGoodbye! Thanks for using Circuitron.", style="yellow")
        kicad_session.stop()
        return
    show_reasoning = args.reasoning
    retries = args.retries
    output_dir = args.output_dir
    keep_skidl = args.keep_skidl

    code_output: CodeGenerationOutput | None = None
    try:
        try:
            code_output = asyncio.run(
                ui.run(
                    prompt,
                    show_reasoning=show_reasoning,
                    retries=retries,
                    output_dir=output_dir,
                    keep_skidl=keep_skidl,
                )
            )
        except (KeyboardInterrupt, EOFError):
            ui.console.print("\nGoodbye! Thanks for using Circuitron.", style="yellow")
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
