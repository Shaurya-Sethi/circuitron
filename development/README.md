# Circuitron Development Module

This folder contains the modularized version of the Circuitron AI-driven PCB design system. The code has been organized into logical modules for better maintainability and extensibility.

## Module Structure

### `config.py`
- **Purpose**: Configuration and environment setup
- **Contents**: Environment variable loading, logging configuration, tracing setup
- **Usage**: Automatically initializes when imported

### `models.py`
- **Purpose**: Pydantic models for structured data
- **Contents**: 
  - `PlanOutput`: Complete output structure from the Planning Agent
  - `CalcResult`: Result structure for calculation tools
- **Usage**: Import models for type hints and validation

### `prompts.py`
- **Purpose**: Agent prompts and instructions
- **Contents**: 
  - `PLAN_PROMPT`: Instructions for the Planning Agent
- **Usage**: Centralized location for all agent prompts
- **Extensibility**: Add new prompts for additional agents here

### `tools.py`
- **Purpose**: Agent tools and utilities
- **Contents**: 
  - `execute_calculation`: Docker-based calculation execution tool
- **Usage**: Tools that agents can use during execution
- **Extensibility**: Add new tools for additional functionality

### `agents.py`
- **Purpose**: Agent definitions and configurations
- **Contents**: 
  - `create_planning_agent()`: Factory function for Planning Agent
  - `planner`: Configured Planning Agent instance
- **Usage**: Centralized agent management
- **Extensibility**: Add new agent factories and instances here

### `utils.py`
- **Purpose**: Utility functions and helpers
- **Contents**: 
  - `extract_reasoning_summary()`: Extract reasoning from agent results
  - `print_section()`: Consistent formatting for output sections
  - `pretty_print_plan()`: Format and display plan results
- **Usage**: Common utilities used across the system
- **Extensibility**: Add formatting and utility functions here

### `main.py`
- **Purpose**: Main entry point and orchestration
- **Contents**: 
  - `run_circuitron()`: Execute the agent pipeline
  - `main()`: Command-line interface and result handling
- **Usage**: Primary entry point for the system
- **Extensibility**: Modify to orchestrate multiple agents

## Usage

### Running the Development Version

```python
# From the circuitron root directory
python -m development.main "Design a voltage divider circuit"

# With optional flags
python -m development.main "Design an amplifier" --reasoning --debug
```

### Importing Components

```python
from development.agents import planner
from development.models import PlanOutput
from development.tools import execute_calculation
from development.utils import pretty_print_plan
```

## Extending the System

### Adding a New Agent

1. **Add prompt** in `prompts.py`:
   ```python
   NEW_AGENT_PROMPT = "Your instructions here..."
   ```

2. **Add output model** in `models.py`:
   ```python
   class NewAgentOutput(BaseModel):
       # Define output structure
   ```

3. **Create agent factory** in `agents.py`:
   ```python
   def create_new_agent() -> Agent:
       return Agent(
           name="New-Agent",
           instructions=NEW_AGENT_PROMPT,
           model="o4-mini",
           output_type=NewAgentOutput,
           tools=[...],
       )
   ```

4. **Update orchestration** in `main.py` to include the new agent in the pipeline.

### Adding New Tools

1. **Define tool** in `tools.py`:
   ```python
   @function_tool
   async def new_tool(param: str) -> ReturnType:
       # Tool implementation
   ```

2. **Add to agent tools** in `agents.py`:
   ```python
   tools=[execute_calculation, new_tool]
   ```

### Adding Utility Functions

Add new formatting, parsing, or helper functions in `utils.py` following the existing patterns.

## Benefits of This Structure

1. **Separation of Concerns**: Each module has a clear, focused responsibility
2. **Easy Testing**: Individual components can be tested in isolation
3. **Scalability**: New agents, tools, and utilities can be added easily
4. **Maintainability**: Code is organized logically and easy to navigate
5. **Reusability**: Components can be imported and reused across different contexts
6. **Type Safety**: Centralized models provide clear interfaces and validation

## Migration from Prototype

The modular structure maintains the exact same functionality as `prototype.py` but organizes it for better development practices. All imports, dependencies, and behavior remain identical.
