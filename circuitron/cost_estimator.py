"""Cost estimation utilities for Circuitron.

This module computes estimated USD cost for LLM usage using token totals
collected during a run.

Pricing resolution order (highest precedence first):
1) Local module `circuitron._model_prices_local` (gitignored) exporting `PRICES`
2) JSON file via env var `CIRCUITRON_PRICES_FILE`
3) Built-in defaults in `circuitron.model_prices_builtin` (can be disabled via env `CIRCUITRON_DISABLE_BUILTIN_PRICES=1`)

Example (do NOT commit to git):

PRICES = {
    "o4-mini": {"input": 1.10, "output": 4.40, "cached_input": 0.110},
    "gpt-5": {"input": 1.25, "output": 10.00, "cached_input": 0.125},
    "gpt-5-mini": {"input": 0.25, "output": 2.00, "cached_input": 0.025},
    "gpt-5-nano": {"input": 0.05, "output": 0.40, "cached_input": 0.005},
    "gpt-4.1": {"input": 2.00, "output": 8.00, "cached_input": 0.50},
    "o3": {"input": 2.00, "output": 8.00, "cached_input": 0.50},
    "o3-pro": {"input": 20.00, "output": 80.00, "cached_input": 0.00},
}

If `_model_prices_local.py` is missing, estimations return 0 with a flag.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple
import importlib
import os
import json

PRICES: Dict[str, Dict[str, float]] = {}
_PRICE_SOURCE = "none"

# 1) Try local-only prices (not in git)
try:
    prices_mod = importlib.import_module("circuitron._model_prices_local")
    PRICES = getattr(prices_mod, "PRICES", {}) or {}
    if PRICES:
        _PRICE_SOURCE = "local_module"
except Exception:  # pragma: no cover - absent by default
    PRICES = {}

# Optional: allow providing a JSON file via env var for local prices
if not PRICES:
    path = os.getenv("CIRCUITRON_PRICES_FILE")
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Expect {model: {input, output, cached_input}}
                PRICES = {str(k): dict(v) for k, v in data.items()}
                if PRICES:
                    _PRICE_SOURCE = "env_json"
        except Exception:
            # Silently ignore malformed files; fall back to empty PRICES
            pass

# 3) Fall back to built-in prices unless explicitly disabled
if not PRICES and os.getenv("CIRCUITRON_DISABLE_BUILTIN_PRICES") not in ("1", "true", "True"):
    try:
        from . import model_prices_builtin as builtin_prices
        PRICES = getattr(builtin_prices, "PRICES", {}) or {}
        if PRICES:
            _PRICE_SOURCE = "builtin"
    except Exception:
        PRICES = {}


def estimate_cost_usd(token_summary: Mapping[str, Any]) -> Tuple[float, bool, Dict[str, float]]:
    """Estimate USD cost for a token usage summary.

    Args:
        token_summary: Dict with shape {
            "overall": {"input": int, "output": int, "total": int, "cached_input": int},
            "by_model": {model: {"input": int, "output": int, "total": int, "cached_input": int}}
        }

    Returns:
        (total_cost, used_default_zero_prices, per_model_breakdown)
        Where per_model_breakdown maps model -> cost.
    """
    def rate(model: str, kind: str) -> float:
        return float(PRICES.get(model, {}).get(kind, 0.0))

    used_default = False if PRICES else True
    per_model_cost: Dict[str, float] = {}
    total_cost = 0.0

    for model, tt in token_summary.get("by_model", {}).items():
        inp = float(tt.get("input", 0)) / 1_000_000.0
        out = float(tt.get("output", 0)) / 1_000_000.0
        cin = float(tt.get("cached_input", 0)) / 1_000_000.0
        cost = inp * rate(model, "input") + out * rate(model, "output") + cin * rate(model, "cached_input")
        per_model_cost[model] = cost
        total_cost += cost
        if cost == 0.0 and (tt.get("input", 0) or tt.get("output", 0) or tt.get("cached_input", 0)):
            # Tokens observed for a model we don't have prices for.
            used_default = True

    return round(total_cost, 6), used_default, per_model_cost


def price_source() -> str:
    """Return the source of active prices: 'local_module' | 'env_json' | 'builtin' | 'none'."""
    return _PRICE_SOURCE


__all__ = ["estimate_cost_usd", "estimate_cost_usd_for_model", "price_source"]


def estimate_cost_usd_for_model(token_summary: Mapping[str, Any], model: str) -> Tuple[float, bool]:
    """Estimate USD cost assuming all tokens are billed to ``model``.

    This uses the overall token counts (input, output, cached_input) and applies
    the selected model's rates. Returns (total_cost, used_default_zero_prices).
    """
    overall = token_summary.get("overall", {})
    inp = float(overall.get("input", 0)) / 1_000_000.0
    out = float(overall.get("output", 0)) / 1_000_000.0
    cin = float(overall.get("cached_input", 0)) / 1_000_000.0

    def rate(kind: str) -> float:
        return float(PRICES.get(model, {}).get(kind, 0.0))

    total_cost = inp * rate("input") + out * rate("output") + cin * rate("cached_input")
    used_default = False
    # Flag if tokens exist but we don't have non-zero pricing for this model
    if (overall.get("input", 0) or overall.get("output", 0) or overall.get("cached_input", 0)) and total_cost == 0.0:
        used_default = True
    return round(total_cost, 6), used_default

