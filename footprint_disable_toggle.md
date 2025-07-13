# Plan: Toggleable Footprint Search

## Objective

To implement a command-line interface (CLI) flag that allows for the temporary disabling of the footprint search functionality in the partfinder agent. This will provide a workaround for a bug where the agent hallucinates footprint names, leading to execution errors.

## Problem

The partfinder agent is currently tasked with finding electronic components and their corresponding KiCad footprints. However, the agent is struggling to correctly identify footprints, often hallucinating names. This results in the generation of invalid code that cannot be executed, hindering the primary functionality of the application.

## Proposed Solution

The proposed solution is to introduce a `--no-footprint-search` CLI flag. When this flag is used, the application will:

1.  Exclude the `search_kicad_footprints` tool from the list of tools available to the partfinder agent.
2.  Utilize a modified prompt for the agent that omits any instructions related to footprint searching.
3.  Rely on the default behavior of the `PartFinderOutput` model, which will produce an empty list for `found_footprints` when no footprints are found, ensuring the pipeline does not crash.

This approach will effectively restore the application to a previously functional state where netlists and SVGs can be generated, albeit without automated footprint association.

## Detailed Implementation Steps

### 1. `circuitron/config.py`: Centralized State Management

A new boolean attribute will be added to the `Settings` class to manage the state of the footprint search functionality.

```python
# In circuitron/config.py

class Settings:
    # ... existing attributes
    footprint_search_enabled: bool = True
```

### 2. `circuitron/cli.py`: Adding the CLI Flag

A new CLI option, `--no-footprint-search`, will be added. When this flag is present, it will update the `footprint_search_enabled` attribute in the global `Settings` object to `False`.

```python
# In circuitron/cli.py

import click
from .config import settings

# ... existing code

@click.option(
    '--no-footprint-search',
    is_flag=True,
    help="Disable the agent's footprint search functionality."
)
def main(no_footprint_search, ...):
    if no_footprint_search:
        settings.footprint_search_enabled = False
    # ... rest of the main function
```

### 3. `circuitron/prompts.py`: Creating a New Prompt

A new prompt, `PARTFINDER_PROMPT_NO_FOOTPRINT`, will be created by copying the existing `PARTFINDER_PROMPT` and removing the instruction for the agent to find footprints.

```python
# In circuitron/prompts.py

PARTFINDER_PROMPT = """
# ... existing prompt ...
"""

PARTFINDER_PROMPT_NO_FOOTPRINT = """
# ... existing prompt, but with the footprint instruction removed ...
"""
```

### 4. `circuitron/agents.py`: Conditionally Modifying the Agent

The `create_partfinder_agent` function will be updated to accept the `footprint_search_enabled` flag. Based on this flag, it will select the appropriate prompt and conditionally include the `search_kicad_footprints` tool.

```python
# In circuitron/agents.py

from . import prompts
from .tools import search_kicad_libraries, search_kicad_footprints
from .config import settings

def create_partfinder_agent(footprint_search_enabled: bool = True):
    tools = [search_kicad_libraries]
    prompt = prompts.PARTFINDER_PROMPT

    if footprint_search_enabled:
        tools.append(search_kicad_footprints)
    else:
        prompt = prompts.PARTFINDER_PROMPT_NO_FOOTPRINT

    # ... rest of the agent creation logic, using the selected `tools` and `prompt`
```

### 5. Tying it Together

The main application logic will call `create_partfinder_agent` and pass the `settings.footprint_search_enabled` value.

```python
# In the main application file where the agent is created

from .agents import create_partfinder_agent
from .config import settings

# ...

partfinder_agent = create_partfinder_agent(
    footprint_search_enabled=settings.footprint_search_enabled
)

# ...
```

## Usage

To run the application with the footprint search functionality disabled, the user will execute the following command:

```bash
circuitron --no-footprint-search "your design prompt"
```

This will ensure that the application avoids the problematic footprint search step and can proceed with the rest of the design pipeline.
