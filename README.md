# Circuitron

```python

 ██████╗ ██╗██████╗  ██████╗██╗   ██╗██╗████████╗██████╗  ██████╗ ███╗   ██╗
██╔════╝ ██║██╔══██╗██╔════╝██║   ██║██║╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║
██║      ██║██████╔╝██║     ██║   ██║██║   ██║   ██████╔╝██║   ██║██╔██╗ ██║
██║      ██║██╔══██╗██║     ██║   ██║██║   ██║   ██╔══██╗██║   ██║██║╚██╗██║
╚██████╗ ██║██║  ██║╚██████╗╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝

```

Circuitron is an agent-driven PCB design accelerator that converts natural language requirements into SKiDL scripts, KiCad schematics, and PCB layout files. It integrates a multi-agent pipeline with retrieval augmented generation to provide clear reasoning and fully traceable design artifacts. The system is built for professional power-electronics engineers who want to streamline routine design steps while retaining full control over final deliverables.

## Features

- **Reasoning-driven workflow** – OpenAI Agents coordinate planning, part discovery, code generation, validation, and error correction with transparent chain-of-thought output.
- **Retrieval-Augmented Generation (RAG)** – A dedicated MCP (Model Context Protocol) server surfaces relevant SKiDL documentation and examples to the LLM for every design step.
- **Real part selection** – Queries KiCad libraries to ensure chosen components exist and match the design specification.
- **Automatic schematic and PCB generation** – Produces `.sch` and `.kicad_pcb` files alongside netlists for direct use in KiCad.
- **Iterative correction loop** – Agents validate generated code, apply fixes, and run ERC checks until a clean design is produced.
- **Containerized toolchain** – Uses Docker images for KiCad, the MCP server, and the Python execution environment to guarantee repeatable results.

## Architecture Overview

Circuitron orchestrates several specialized agents using the OpenAI Agents SDK. A planning agent first interprets the user prompt and proposes a stepwise design plan. That plan can be edited by the user before execution. Subsequent agents handle part discovery and selection, gather SKiDL documentation via the MCP server, generate code, validate it, and resolve any errors. Output files are produced in native KiCad formats so that engineers can review and finalize designs using their usual toolchain.
The pipeline uses dedicated agents for each design step:
1. **Planner** – break down the prompt into design tasks.
2. **Plan editor** – incorporate user feedback.
3. **Part finder** – search KiCad libraries for components.
4. **Part selector** – choose optimal parts.
5. **Documentation agent** – fetch SKiDL references via the MCP server.
6. **Code generator** – write SKiDL code based on the plan and documentation.
7. **Validator and corrector** – detect issues, use the knowledge graph, and fix problems.
8. **Runtime correction** – ensure the script executes correctly.
9. **ERC handler** – resolve electrical rule check warnings.
10. **Execution step** – output schematic, netlist, PCB file, and an SVG preview.


The MCP server provides RAG capabilities and knowledge graph lookups. It requires a Supabase database and a Neo4j instance for storing crawled documentation and relationships. Circuitron communicates with this server during every run to retrieve accurate SKiDL references and to perform hallucination checks.

## Prerequisites

Before installing Circuitron ensure the following tools and accounts are available:

- **Python 3.10+** (the examples use Python 3.12)
- **Docker** with permission to run containers
- **OpenAI API access** – obtain an API key from [OpenAI account settings](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key)
- **Supabase account** – used by the MCP server for storing crawled pages
- **AuraDB (Neo4j) database** – free instances are available from [AuraDB](https://neo4j.com/cloud/platform/aura-graph-database/)

## Installation

Clone the repository and install the package in editable mode so the CLI and tests use the local sources:

```bash
pip install -e .  # or `pip install .`
```

This installs `openai-agents`, `python-dotenv`, and `skidl`. For tracing support during development, install the optional extras:

```bash
pip install -e .[dev]
```

A `requirements.txt` file matching the `pyproject.toml` dependencies is included for convenience.

## Setup

1. **Pull required Docker images**

   ```bash
   docker pull ghcr.io/shaurya-sethi/circuitron-kicad:latest
   docker pull ghcr.io/shaurya-sethi/circuitron-mcp:latest
   docker pull python:3.12-slim
   ```

2. **Create a `.env` file**

   Copy `.env.example` to `.env` and set at least `OPENAI_API_KEY`.
   This file lives in the project root and is loaded by the CLI.
   You may also override `MCP_URL` and `KICAD_IMAGE` here.

3. **Create `mcp.env` for the MCP server**

   Prepare a separate file (for example `mcp.env`) with these variables:

   ```
   TRANSPORT=sse
   HOST=0.0.0.0
   PORT=8051
   OPENAI_API_KEY=<your OpenAI API key>
   MODEL_CHOICE=gpt-4.1-nano
   USE_CONTEXTUAL_EMBEDDINGS=true
   USE_HYBRID_SEARCH=true
   USE_AGENTIC_RAG=true
   USE_RERANKING=true
   USE_KNOWLEDGE_GRAPH=true
   LLM_MAX_CONCURRENCY=2
   LLM_REQUEST_DELAY=0.5
   SUPABASE_URL=<your Supabase project URL>
   SUPABASE_SERVICE_KEY=<your Supabase service_role key>
   NEO4J_URI=<your AuraDB Neo4j URI>
   NEO4J_USER=<your Neo4j username>
   NEO4J_PASSWORD=<your Neo4j password>
   ```

4. **Run the MCP server**

   Start the MCP container with the variables from `mcp.env`:

   ```bash
   docker run --env-file mcp.env -p 8051:8051 ghcr.io/shaurya-sethi/circuitron-mcp:latest
   ```

   Only the MCP server requires this configuration step. The other images are used automatically by Circuitron.


5. **Prepare the MCP database**

   - Use your AuraDB connection details for the Neo4j variables in the `.env` file.
   - After creating the Supabase project and obtaining the URL and service key, open the **SQL Editor** in the Supabase dashboard and execute the schema found in `crawled_pages.sql`. This creates the tables needed by the MCP server.

6. **Populate the knowledge base**

   With the MCP server running, configure your coding agent (for example GitHub Copilot) to use the server:

   - Select **Configure Tools → Add More Tools… → Add MCP Server → HTTP** and enter the URL `http://localhost:8051/sse`.
   - Instruct the agent to crawl `https://devbisme.github.io/skidl/` to build the SKiDL documentation corpus.
   - Next, instruct it to parse the GitHub repository `https://github.com/devbisme/skidl` to populate the knowledge graph.

   After these steps the MCP server will be ready to answer documentation queries and perform hallucination detection for Circuitron runs.

## Usage

Once the MCP server is running and the Docker images are available, you can generate designs directly from the command line. The CLI verifies that the KiCad container starts successfully before processing a prompt.

```bash
circuitron "Design a voltage divider"
```

During development you can enable tracing and verbose agent output:

```bash
circuitron --dev "Design a voltage divider"
```

The `--output-dir` option saves all generated files to a specific location. By default results are written to `./circuitron_output`.
### Running Tests

```bash
pytest -q
```

All tests should pass after installation and setup.

## Configuration

Environment variables control most aspects of Circuitron. Required variables are loaded from `.env` when the CLI starts. The following optional overrides are available:

- `CALC_IMAGE` – Docker image used for executing Python calculations (defaults to `python:3.12-slim`).
- `KICAD_IMAGE` – KiCad container image (defaults to `ghcr.io/shaurya-sethi/circuitron-kicad:latest`).
- `MCP_URL` – Endpoint for the MCP server (`http://localhost:8051` by default).

Update these variables in your environment or in the `.env` file to customise behaviour.

## Troubleshooting

- **MCP server not reachable** – ensure the container was started with the correct `.env` file and that port 8051 is open.
- **KiCad container fails to start** – pull the image again with `docker pull ghcr.io/shaurya-sethi/circuitron-kicad:latest` and verify Docker is running.
- **Missing environment variables** – the CLI exits with an error if `OPENAI_API_KEY` or `MCP_URL` are not set. Check your `.env` configuration.

## Support and Contributing

Contributions are welcome. Please open issues or pull requests on the repository if you encounter problems or have suggestions. Refer to `AGENTS.md` for coding guidelines and `overview.md` for additional background on the architecture.

## License

This project is licensed under the MIT License.
