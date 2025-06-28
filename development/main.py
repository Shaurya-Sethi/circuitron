"""
Main entry point for the Circuitron development system.
Orchestrates the agent pipeline and handles command-line interface.
"""

import asyncio
from .config import setup_environment
from circuitron.pipeline import pipeline, parse_args
from .models import PartFinderOutput


async def run_circuitron(
    prompt: str, show_reasoning: bool = False, debug: bool = False
) -> PartFinderOutput:
    """Execute the Circuitron workflow using the full pipeline."""
    return await pipeline(prompt, show_reasoning=show_reasoning, debug=debug)


def main():
    """Main entry point for the Circuitron system."""
    args = parse_args()
    prompt = args.prompt or input("Prompt: ")
    show_reasoning = args.reasoning
    debug = args.debug
    
    # Execute pipeline
    part_output = asyncio.run(run_circuitron(prompt, show_reasoning, debug))
    if part_output:
        print("\nFOUND COMPONENTS JSON:\n")
        print(part_output.found_components_json)


if __name__ == "__main__":
    main()
