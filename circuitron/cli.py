"""Command line interface for Circuitron."""

import asyncio
import httpx
from .config import setup_environment, settings
from .models import CodeGenerationOutput, UserFeedback


async def run_circuitron(
    prompt: str,
    show_reasoning: bool = False,
    debug: bool = False,
    user_feedback: UserFeedback | None = None,
) -> CodeGenerationOutput:
    """Send the prompt to the backend API and return the generated code."""

    payload: dict[str, object] = {
        "prompt": prompt,
        "reasoning": show_reasoning,
        "debug": debug,
    }
    if user_feedback is not None:
        payload["user_feedback"] = user_feedback.model_dump()

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.api_url}/run", json=payload)
        resp.raise_for_status()
        data = resp.json()

    if stdout := data.get("stdout"):
        print(stdout)
    if stderr := data.get("stderr"):
        print(stderr)

    return CodeGenerationOutput.model_validate(data["result"])


def main() -> None:
    """Main entry point for the Circuitron system."""
    setup_environment()
    from circuitron.pipeline import parse_args

    args = parse_args()
    prompt = args.prompt or input("Prompt: ")
    show_reasoning = args.reasoning
    debug = args.debug
    
    # Execute pipeline
    code_output = asyncio.run(run_circuitron(prompt, show_reasoning, debug))
    if code_output:
        print("\n=== GENERATED SKiDL CODE ===\n")
        print(code_output.complete_skidl_code)


if __name__ == "__main__":
    main()
