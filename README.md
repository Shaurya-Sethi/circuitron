# Circuitron

**🚧 Status: Active Prototyping Phase**

Circuitron is an agentic PCB design accelerator that transforms natural language prompts into SKiDL code, KiCad schematics, and routed PCB layouts. It assists professional power-electronics engineers by automating routine steps while keeping humans in the loop for review and approval.

## Current Development Status

**✅ Working Prototype:** `examples/prototype.py` - Functional demo with planning agent, calculations, and basic SKiDL code generation
**🔧 Modular Package:** `circuitron/` - Standard Python package using OpenAI Agents SDK
**📚 Documentation:** Complete offline OpenAI Agents SDK docs available for LLM agents without internet access

### What's Working Now:
- Natural language to design plan conversion
- Calculation engine with executable Python code
- Basic SKiDL component search and selection
- Chain-of-thought reasoning with user approval loops
- RAG-powered component lookup with KiCad library integration

### In Development:
- Full OpenAI Agents SDK integration
- Modular agent architecture
- Code validation with knowledge-graph-based hallucination checks
- Automated code correction loop to resolve validation and ERC issues
- Enhanced UI/UX with session management
 - PCB layout generation (auto-routing via the DeepPCB API will be added in the future)
- Production-ready deployment structure

Part selection now leverages SKiDL's full search syntax: queries may contain multiple terms, quoted phrases, regular expressions, and OR pipes for precise component lookup.

See [overview.md](overview.md) for detailed project goals and structure.

## Quick Start (Prototype)

### Prerequisites
- Python 3.10+
- KiCad installed (for component libraries)
- OpenAI API access

### Setup

Install dependencies with `pip install -r requirements.txt` then copy
`.env.example` to `.env` and fill in the required values:

```
OPENAI_API_KEY=<your OpenAI API key>
LOGFIRE_TOKEN=<your token here>
MCP_URL=http://localhost:8051

```

Required variables:
`OPENAI_API_KEY`, `PLANNING_MODEL`, `PLAN_EDIT_MODEL`, `PART_FINDER_MODEL`, and `MCP_URL`.
Optional overrides:
`CALC_IMAGE` and `KICAD_IMAGE` for custom Docker images.

To enable hallucination checks, set `USE_KNOWLEDGE_GRAPH=true` and ensure the
knowledge graph database is populated. The MCP README describes how to add a
repository, for example:
```
python knowledge_graphs/ai_hallucination_detector.py add https://github.com/pydantic/pydantic-ai.git
```

## Tech Stack

- Python 3.10+
- [OpenAI Agents SDK](https://github.com/openai/openai-agents) (integration in progress)
- [SKiDL](https://github.com/xesscorp/skidl) for schematic generation
- [python-dotenv](https://github.com/theskumar/python-dotenv) for configuration
- [logfire](https://pydantic.dev/logfire) for observability and tracing

## Contributing

This project is in active development. The prototype demonstrates core functionality while the modular architecture is being built for production use.

See [AGENTS.md](AGENTS.md) for AI coding guidelines and [overview.md](overview.md) for detailed project architecture.

Before submitting a pull request, run the linter locally. CI executes `ruff` to
enforce style:

```bash
ruff check .
```

## Usage

### Run the Working Prototype:
```bash
python examples/prototype.py
```

### Run the Package CLI:
```bash
python -m circuitron "Design a voltage divider"
```

After installation:
```bash
circuitron "Design a voltage divider"
```

### Run the Node.js TUI

First build the TypeScript sources:

```bash
npm run build
node packages/cli/dist/index.js
```

After installing globally you can run:

```bash
circuitron-cli
```

The TUI attempts to connect to `http://localhost:8000` on start. Set
`CIRCUITRON_BACKEND_URL` to point at a different server.
Set `CIRCUITRON_THEME` to `dark`, `light`, or `sunset` to change the color
scheme.
Use `CIRCUITRON_BANNER_THEME` to choose the ASCII banner gradient. Available
options are `electric` (default), `solarizedDark`, and `sunset`.

See `assets/ascii_banner.png` for a preview of the banner style.

### Run the Backend API (Docker)

Start the FastAPI server using uvicorn inside the provided Docker container:

```bash
docker build -t circuitron-backend .
docker run -p 8000:8000 circuitron-backend uvicorn backend.api:app --host 0.0.0.0
```

The CLI communicates with the server at `http://localhost:8000` by default. Set
`CIRCUITRON_API_URL` to change this location.

### Try the Interactive Notebook:
```bash
jupyter notebook examples/prototype.ipynb
```

## Project Structure

```
examples/
├── prototype.py            # Working prototype (main demo)
├── prototype.ipynb         # Jupyter notebook for interactive testing
circuitron/
├── cli.py                  # CLI entry point
├── __main__.py             # Allows `python -m circuitron`
├── agents.py               # Agent definitions
├── models.py               # Data models
├── tools.py                # Tool implementations
├── prompts.py              # Prompt texts
├── utils.py                # Utility functions
├── config.py               # Environment setup
├── settings.py             # Configuration dataclass
├── pipeline.py             # Orchestration logic
├── openai-agents-sdk-docs.md  # Offline docs for LLM agents
├── lib_pickle_dir/         # Cached KiCad component libraries
└── tests/                  # Test suite

## License

MIT
