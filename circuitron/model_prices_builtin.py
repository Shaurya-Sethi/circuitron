"""Built-in default model pricing for Circuitron.

These prices are expressed in USD per 1,000,000 tokens and are intended to
provide an out-of-the-box estimation experience. Users can override these via:

- A local module ``circuitron._model_prices_local`` exporting ``PRICES``
- An environment JSON file pointed to by ``CIRCUITRON_PRICES_FILE``

Set ``CIRCUITRON_DISABLE_BUILTIN_PRICES=1`` to ignore these defaults (useful in tests).

Note: Update values as needed for your environment. They are provided as
reasonable defaults and may not match current vendor pricing exactly.
"""

from __future__ import annotations

from typing import Dict

# USD per 1,000,000 tokens
PRICES: Dict[str, Dict[str, float]] = {
    "o4-mini": {"input": 1.10, "output": 4.40, "cached_input": 0.110},
    "gpt-5": {"input": 1.25, "output": 10.00, "cached_input": 0.125},
    "gpt-5-mini": {"input": 0.25, "output": 2.00, "cached_input": 0.025},
    "gpt-5-nano": {"input": 0.05, "output": 0.40, "cached_input": 0.005},
    "gpt-4.1": {"input": 2.00, "output": 8.00, "cached_input": 0.50},
    "o3": {"input": 2.00, "output": 8.00, "cached_input": 0.50},
    "o3-pro": {"input": 20.00, "output": 80.00, "cached_input": 0.00},
}

__all__ = ["PRICES"]
