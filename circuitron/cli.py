"""Command line interface for Circuitron."""

import asyncio
from .config import setup_environment
from .models import CodeGenerationOutput
from circuitron.tools import kicad_session



async def run_circuitron(
    prompt: str,
    show_reasoning: bool = False,
    retries: int = 0,
) -> CodeGenerationOutput | None:
    """Execute the Circuitron workflow using the full pipeline with retries."""

    from circuitron.pipeline import run_with_retry

    return await run_with_retry(
        prompt,
        show_reasoning=show_reasoning,
        retries=retries,
    )


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

    if not verify_containers():
        return

    prompt = args.prompt or input("Prompt: ")
    show_reasoning = args.reasoning
    retries = args.retries

    code_output: CodeGenerationOutput | None = None
    try:
        try:
            code_output = asyncio.run(
                run_circuitron(prompt, show_reasoning, retries)
            )
        except KeyboardInterrupt:
            print("\nExecution interrupted by user.")
        except Exception as exc:
            print(f"Error during execution: {exc}")
    finally:
        kicad_session.stop()

    if code_output:
        print("\n=== GENERATED SKiDL CODE ===\n")
        print(code_output.complete_skidl_code)


if __name__ == "__main__":
    main()
