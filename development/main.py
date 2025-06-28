"""
Main entry point for the Circuitron development system.
Orchestrates the agent pipeline and handles command-line interface.
"""

import sys
import asyncio
from agents import Runner
from .config import setup_environment
from .agents import planner
from .models import PartFinderOutput


async def run_circuitron(prompt: str) -> PartFinderOutput | None:
    """Execute the Circuitron workflow via agent handoffs."""
    result = await Runner.run(planner, prompt)
    return result.final_output_as(PartFinderOutput)


def main():
    """Main entry point for the Circuitron system."""
    # Parse command line arguments
    prompt = sys.argv[1] if len(sys.argv) > 1 else input("Prompt: ")
    _ = "--reasoning" in sys.argv or "-r" in sys.argv
    _ = "--debug" in sys.argv or "-d" in sys.argv
    
    # Execute pipeline
    part_output = asyncio.run(run_circuitron(prompt))
    if part_output:
        print("\nFOUND COMPONENTS JSON:\n")
        print(part_output.found_components_json)


if __name__ == "__main__":
    main()
