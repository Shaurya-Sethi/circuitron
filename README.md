# Circuitron

Circuitron is an agentic PCB design accelerator that transforms natural language prompts into SKiDL code, KiCad schematics, and routed PCB layouts. It assists professional power-electronics engineers by automating routine steps while keeping humans in the loop for review and approval.

## Quick Start

1. Install [Poetry](https://python-poetry.org/).
2. Install dependencies and activate the virtual environment:
   ```bash
   poetry install
   poetry shell
   ```
3. Run the backend with hot reload:
   ```bash
   uvicorn backend.main:app --reload
   ```

See [overview.md](overview.md) for detailed project goals and structure.
