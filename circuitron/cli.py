"""Command line interface for Circuitron."""

import asyncio
from .config import setup_environment
from .models import CodeGenerationOutput
from circuitron.tools import kicad_session
from .mcp_manager import mcp_manager
from .network import check_internet_connection
from .exceptions import PipelineError
from circuitron.ui.app import TerminalUI
from circuitron.ui.components import panel


async def run_circuitron(
    prompt: str,
    show_reasoning: bool = False,
    retries: int = 0,
    output_dir: str | None = None,
) -> CodeGenerationOutput | None:
    """Execute the Circuitron workflow using the full pipeline with retries."""

    from circuitron.pipeline import run_with_retry

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
            print(f"Fatal error: {exc}")
            return None
    finally:
        await mcp_manager.cleanup()


def verify_containers() -> bool:
    """Ensure required Docker containers are running."""

    try:
        kicad_session.start()
    except Exception as exc:
        print(f"Failed to start KiCad container: {exc}")
        return False
    return True


def main() -> None:
    """Main entry point for the Circuitron system."""
    from circuitron.pipeline import parse_args

    args = parse_args()
    setup_environment(dev=args.dev)

    if not check_internet_connection():
        return

    if not verify_containers():
        return

    ui = TerminalUI()
    ui.start_banner()
    prompt = args.prompt or ui.prompt_user("Prompt")
    show_reasoning = args.reasoning
    retries = args.retries
    output_dir = args.output_dir

    code_output: CodeGenerationOutput | None = None
    try:
        try:
            code_output = asyncio.run(
                ui.run(prompt, show_reasoning=show_reasoning, retries=retries, output_dir=output_dir)
            )
        except KeyboardInterrupt:
            print("\nExecution interrupted by user.")
        except Exception as exc:
            print(f"Error during execution: {exc}")
    finally:
        kicad_session.stop()

    if code_output:
        panel.show_panel(ui.console, "Generated SKiDL Code", code_output.complete_skidl_code, ui.theme)
        ui.console.print("\n📁 Generated files have been saved to the output directory.")
        ui.console.print("💡 Use --output-dir to specify a custom location.")
        ui.console.print("💡 Default location: ./circuitron_output")


if __name__ == "__main__":
    main()
