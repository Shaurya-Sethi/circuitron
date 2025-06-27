# Circuitron

Circuitron is an agentic PCB design accelerator that transforms natural language prompts into SKiDL code, KiCad schematics, and routed PCB layouts. It assists professional power-electronics engineers by automating routine steps while keeping humans in the loop for review and approval.

Part selection now leverages SKiDL's full search syntax: queries may contain multiple terms, quoted phrases, regular expressions, and OR pipes for precise component lookup.

See [overview.md](overview.md) for detailed project goals and structure.

## Setup

Install dependencies with `pip install -r requirements.txt` then copy
`.env.example` to `.env` and fill in the required values:

```
OPENAI_API_KEY=<your OpenAI API key>
MODEL_PLAN=gpt-4o-mini
MODEL_PART=gpt-4o-mini
MODEL_CODE=gpt-4o
MODEL_TEMP=0.15
MCP_URL=http://localhost:8051

# Optional tuning variables
MAX_TOOL_CALLS=5
MAX_CTX_TOK=128000
SAFETY_MARGIN=4000
```

`OPENAI_API_KEY`, `MODEL_PLAN`, `MODEL_PART`, `MODEL_CODE`, and `MCP_URL` must be provided. The others have sensible defaults.

## Tech Stack

- Python 3.10+
- [OpenAI Agents SDK](https://github.com/openai/openai-agents)
- [SKiDL](https://github.com/xesscorp/skidl)
- [tiktoken](https://github.com/openai/tiktoken)
- [httpx](https://www.python-httpx.org/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

## Usage

Run the CLI:

```
python -m src.main_cli
```

## License

MIT
