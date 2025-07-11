"""Interactive onboarding for Circuitron configuration."""

from __future__ import annotations
from pathlib import Path

import click
from dotenv import dotenv_values, set_key


ENV_DIR = Path.home() / ".circuitron"
ENV_FILE = ENV_DIR / ".env"

# (prompt text, hide_input)
REQUIRED_VARS: list[tuple[str, str, bool]] = [
    ("OPENAI_API_KEY", "OpenAI API key", True),
    ("SUPABASE_URL", "Supabase URL", False),
    ("SUPABASE_SERVICE_KEY", "Supabase service key", True),
    ("NEO4J_URI", "Neo4j URI", False),
    ("NEO4J_USER", "Neo4j username", False),
    ("NEO4J_PASSWORD", "Neo4j password", True),
]

PRESET_VARS = {
    "HOST": "0.0.0.0",
    "PORT": "8051",
    "TRANSPORT": "sse",
    "MODEL_CHOICE": "gpt-4.1-nano",
    "USE_CONTEXTUAL_EMBEDDINGS": "true",
    "USE_HYBRID_SEARCH": "true",
    "USE_AGENTIC_RAG": "true",
    "USE_RERANKING": "true",
    "USE_KNOWLEDGE_GRAPH": "true",
    "LLM_MAX_CONCURRENCY": "2",
    "LLM_REQUEST_DELAY": "0.5",
    "MCP_URL": "http://localhost:8051",
    "KICAD_IMAGE": "ghcr.io/shaurya-sethi/circuitron-kicad:latest",
}


def run_onboarding() -> None:
    """Collect credentials interactively and save them to ``ENV_FILE``."""

    click.echo()
    click.secho("Circuitron setup", fg="cyan", bold=True)
    click.echo("Provide the following credentials. Press Enter to keep existing values.\n")

    ENV_DIR.mkdir(parents=True, exist_ok=True)
    existing = dotenv_values(dotenv_path=ENV_FILE)

    def ask(var: str, prompt: str, hide: bool) -> str:
        default = existing.get(var, "")
        return click.prompt(
            prompt,
            default=default,
            hide_input=hide,
            show_default=bool(default),
            type=str,
        )

    creds = {}
    for var, prompt, hide in REQUIRED_VARS:
        creds[var] = ask(var, prompt, hide)

    creds.update(PRESET_VARS)

    for key, val in creds.items():
        set_key(str(ENV_FILE), key, val)

    click.echo(f"\nConfiguration saved to {ENV_FILE}\n")

__all__ = ["run_onboarding", "ENV_FILE"]
