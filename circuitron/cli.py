"""Command line interface for Circuitron."""

import asyncio
from .config import setup_environment
from .models import CodeGenerationOutput



async def run_circuitron(
    prompt: str,
    show_reasoning: bool = False,
    debug: bool = False,
    retries: int = 0,
) -> CodeGenerationOutput | None:
    """Execute the Circuitron workflow using the full pipeline with retries."""

    from circuitron.pipeline import run_with_retry

    return await run_with_retry(
        prompt,
        show_reasoning=show_reasoning,
        debug=debug,
        retries=retries,
    )


def main() -> None:
    """Main entry point for the Circuitron system."""
    from circuitron.pipeline import parse_args
    from circuitron.tools import kicad_session

    args = parse_args()
    setup_environment(dev=args.dev)

    prompt = args.prompt or input("Prompt: ")
    show_reasoning = args.reasoning
    debug = args.debug
    retries = args.retries

    code_output: CodeGenerationOutput | None = None
    try:
        try:
            code_output = asyncio.run(
                run_circuitron(prompt, show_reasoning, debug, retries)
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
