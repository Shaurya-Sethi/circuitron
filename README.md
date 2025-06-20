# Circuitron

Circuitron is an agentic PCB design accelerator that transforms natural language prompts into SKiDL code, KiCad schematics, and routed PCB layouts. It assists professional power-electronics engineers by automating routine steps while keeping humans in the loop for review and approval.

Part selection now leverages SKiDL's full search syntax: queries may contain multiple terms, quoted phrases, regular expressions, and OR pipes for precise component lookup.


See [overview.md](overview.md) for detailed project goals and structure.

## Setup

Install dependencies with `pip install -r requirements.txt` then copy
`.env.example` to `.env` and fill in the required values:

```
MISTRAL_API_KEY=<your API key>
MISTRAL_API_BASE=https://api.mistral.ai/v1  # or your custom endpoint
MODEL_PLAN=magistral-small-latest
MODEL_PART=mistral-small-latest
MODEL_CODE=devstral-small-latest
MODEL_TEMP=0.15
MCP_URL=http://localhost:8051/sse

# Optional tuning variables
MAX_TOOL_CALLS=5
TOKEN_MODEL=devstral-small-2505  # uses the Tekken tokenizer from mistral-common
MAX_CTX_TOK=40000
SAFETY_MARGIN=2000
```

When `TOKEN_MODEL` is set to `devstral-small-2505`, the Tekken tokenizer from
`mistral-common` is required. No fallback tokenizer is supported for this model
as noted in the [official Devstral tokenization guide](https://docs.mistral.ai/guides/tokenization/).

`MISTRAL_API_KEY`, `MODEL_PLAN`, `MODEL_PART`, `MODEL_CODE`, and `MCP_URL` must be provided. The others have sensible defaults.

## Usage

1. **Create your environment file** by copying `.env.example` to `.env` and
   filling in the required values.
2. **Install dependencies** with `pip install -r requirements.txt` and install
   the SVG export tool with `npm install -g netlistsvg@1.0.2`.
3. **Run the CLI** using:

   ```bash
   python -m src.main_cli
   ```
