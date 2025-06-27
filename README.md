# Circuitron

**🚧 Status: Active Prototyping Phase**

Circuitron is an agentic PCB design accelerator that transforms natural language prompts into SKiDL code, KiCad schematics, and routed PCB layouts. It assists professional power-electronics engineers by automating routine steps while keeping humans in the loop for review and approval.

## Current Development Status

**✅ Working Prototype:** `prototype.py` - Functional demo with planning agent, calculations, and basic SKiDL code generation  
**🔧 Development Branch:** `development/` - Modular architecture using OpenAI Agents SDK (in progress)  
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
- Enhanced UI/UX with session management
- PCB layout generation and auto-routing
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

`OPENAI_API_KEY`, `MODEL_PLAN`, `MODEL_PART`, `MODEL_CODE`, and `MCP_URL` must be provided. The others have sensible defaults.

## Tech Stack

- Python 3.10+
- [OpenAI Agents SDK](https://github.com/openai/openai-agents) (integration in progress)
- [SKiDL](https://github.com/xesscorp/skidl) for schematic generation
- [python-dotenv](https://github.com/theskumar/python-dotenv) for configuration
- [logfire](https://pydantic.dev/logfire) for observability and tracing

## Contributing

This project is in active development. The prototype demonstrates core functionality while the modular architecture is being built for production use.

See [AGENTS.md](AGENTS.md) for AI coding guidelines and [overview.md](overview.md) for detailed project architecture.

## Usage

### Run the Working Prototype:
```bash
python prototype.py
```

### Run the Development Version:
```bash
python main.py
```

### Try the Interactive Notebook:
```bash
jupyter notebook prototype.ipynb
```

## Project Structure

```
circuitron/
├── prototype.py            # Working prototype (main demo)
├── prototype.ipynb         # Jupyter notebook for interactive testing
├── main.py                 # Entry point for new architecture
├── development/            # Modular agent architecture (in progress)
│   ├── agents.py           # Agent definitions
│   ├── tools.py            # Tool implementations
│   ├── models.py           # Data models
│   └── utils.py            # Utility functions
├── openai-agents-sdk-docs.md  # Offline docs for LLM agents
├── lib_pickle_dir/         # Cached KiCad component libraries
└── tests/                  # Test suite

## License

MIT