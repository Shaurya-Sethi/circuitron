"""
Main entry point for the Circuitron development system.
Orchestrates the agent pipeline and handles command-line interface.
"""

import sys
import asyncio
from agents import Runner
from .config import setup_environment
from .agents import planner
from .utils import pretty_print_plan, extract_reasoning_summary


async def run_circuitron(prompt: str):
    """Run the Circuitron planning agent with the given prompt."""
    return await Runner.run(planner, prompt)


def main():
    """Main entry point for the Circuitron system."""
    # Parse command line arguments
    prompt = sys.argv[1] if len(sys.argv) > 1 else input("Prompt: ")
    show_reasoning = "--reasoning" in sys.argv or "-r" in sys.argv
    show_debug = "--debug" in sys.argv or "-d" in sys.argv
    
    # Run the planning agent
    result = asyncio.run(run_circuitron(prompt))

    # Always print the structured plan
    pretty_print_plan(result.final_output)

    # Optionally show calculation codes for debugging
    if show_debug and result.final_output.calculation_codes:
        print("\n=== Debug: Calculation Codes ===")
        for i, code in enumerate(result.final_output.calculation_codes):
            print(f"\nCalculation #{i+1} code:")
            print(code)

    # Optionally show reasoning summary
    if show_reasoning:
        print("\n=== Reasoning Summary ===\n")
        print(extract_reasoning_summary(result))


if __name__ == "__main__":
    main()
