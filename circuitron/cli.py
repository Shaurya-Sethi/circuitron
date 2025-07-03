"""Command line interface for Circuitron."""

import asyncio
from .config import setup_environment
from .models import CodeGenerationOutput



async def run_circuitron(
    prompt: str, show_reasoning: bool = False, debug: bool = False
) -> CodeGenerationOutput:
    """Execute the Circuitron workflow using the full pipeline."""
    from circuitron.pipeline import pipeline

    return await pipeline(prompt, show_reasoning=show_reasoning, debug=debug)


def main() -> None:
    """Main entry point for the Circuitron system."""
    setup_environment()
    from circuitron.pipeline import parse_args
    from circuitron.tools import kicad_session

    args = parse_args()
    prompt = args.prompt or input("Prompt: ")
    show_reasoning = args.reasoning
    debug = args.debug

    code_output: CodeGenerationOutput | None = None
    try:
        code_output = asyncio.run(run_circuitron(prompt, show_reasoning, debug))
    finally:
        kicad_session.stop()

    if code_output:
        print("\n=== GENERATED SKiDL CODE ===\n")
        print(code_output.complete_skidl_code)


if __name__ == "__main__":
    main()
