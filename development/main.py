"""
Main entry point for the Circuitron development system.
Orchestrates the agent pipeline and handles command-line interface.
"""

import sys
import asyncio
from .config import setup_environment
from circuitron.pipeline import pipeline
from .models import PartFinderOutput


async def run_circuitron(
    prompt: str, show_reasoning: bool = False, debug: bool = False
) -> PartFinderOutput:
    """Execute the Circuitron workflow using the full pipeline."""
    return await pipeline(prompt, show_reasoning=show_reasoning, debug=debug)


def main():
    """Main entry point for the Circuitron system."""
    # Parse command line arguments
    prompt = sys.argv[1] if len(sys.argv) > 1 else input("Prompt: ")
    show_reasoning = "--reasoning" in sys.argv or "-r" in sys.argv
    debug = "--debug" in sys.argv or "-d" in sys.argv
    
    # Execute pipeline
    part_output = asyncio.run(run_circuitron(prompt, show_reasoning, debug))
    if part_output:
        print("\nFOUND COMPONENTS JSON:\n")
        print(part_output.found_components_json)


if __name__ == "__main__":
    main()
