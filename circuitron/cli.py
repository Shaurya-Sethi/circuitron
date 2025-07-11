"""Command line interface for Circuitron."""

import argparse
import asyncio
from .config import setup_environment
from .models import CodeGenerationOutput
from circuitron.tools import kicad_session
from .mcp_server import ensure_running as ensure_mcp
from .mcp_manager import mcp_manager
from .network import check_internet_connection
from .exceptions import PipelineError
from .onboarding import run_onboarding


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the Circuitron CLI."""
    parser = argparse.ArgumentParser(description="Circuitron CLI")
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="execute pipeline")
    run_parser.add_argument("prompt", nargs="?", help="Design prompt")
    run_parser.add_argument("-r", "--reasoning", action="store_true", help="show reasoning summary")
    run_parser.add_argument("--dev", action="store_true", help="enable tracing with logfire")
    run_parser.add_argument("-n", "--retries", type=int, default=0, help="number of retries")
    run_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="directory to save generated files (default: ./circuitron_output)",
    )

    sub.add_parser("config", help="update stored credentials")
    sub.add_parser("status", help="show service status")

    args = parser.parse_args(argv)
    if args.command is None:
        # default to run when no subcommand is provided
        args = parser.parse_args(["run"] + (argv or []))
    return args


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
        if not ensure_mcp():
            print("Failed to start MCP server container")
            return False
    except Exception as exc:
        print(f"Failed to start KiCad container: {exc}")
        return False
    return True


def main() -> None:
    """Main entry point for the Circuitron system."""

    args = parse_cli_args()

    if args.command == "config":
        run_onboarding()
        return

    if args.command == "status":
        setup_environment()
        ok = ensure_mcp()
        print(f"MCP server running: {ok}")
        return

    setup_environment(dev=args.dev)

    if not check_internet_connection():
        return

    if not verify_containers():
        return

    prompt = args.prompt or input("Prompt: ")
    show_reasoning = args.reasoning
    retries = args.retries
    output_dir = args.output_dir

    code_output: CodeGenerationOutput | None = None
    try:
        try:
            code_output = asyncio.run(run_circuitron(prompt, show_reasoning, retries, output_dir))
        except KeyboardInterrupt:
            print("\nExecution interrupted by user.")
        except Exception as exc:
            print(f"Error during execution: {exc}")
    finally:
        kicad_session.stop()

    if code_output:
        print("\n=== GENERATED SKiDL CODE ===\n")
        print(code_output.complete_skidl_code)
        print("\n" + "=" * 60)
        print("📁 Generated files have been saved to the output directory.")
        print("💡 Use --output-dir to specify a custom location.")
        print("💡 Default location: ./circuitron_output")


if __name__ == "__main__":
    main()
