from __future__ import annotations

import importlib
import sys


def test_builtin_prices_used_by_default(monkeypatch) -> None:
    # Ensure no local module and no env JSON
    sys.modules.pop('circuitron._model_prices_local', None)
    monkeypatch.delenv('CIRCUITRON_PRICES_FILE', raising=False)
    monkeypatch.delenv('CIRCUITRON_DISABLE_BUILTIN_PRICES', raising=False)

    import circuitron.cost_estimator as ce
    importlib.reload(ce)

    # Verify price source and a simple computation uses built-in numbers
    assert ce.price_source() == 'builtin'
    token_summary = {
        "overall": {"input": 1_000_000, "output": 0, "total": 1_000_000, "cached_input": 0},
        "by_model": {"o4-mini": {"input": 1_000_000, "output": 0, "total": 1_000_000, "cached_input": 0}},
    }
    total, used_default, per_model = ce.estimate_cost_usd(token_summary)
    # For o4-mini input=1.10 per 1M per built-in
    assert round(total, 4) == 1.10
    assert used_default is False
    assert round(per_model["o4-mini"], 4) == 1.10


def test_builtin_prices_can_be_disabled(monkeypatch) -> None:
    # Ensure no local module and no env JSON, but disable builtin
    sys.modules.pop('circuitron._model_prices_local', None)
    monkeypatch.delenv('CIRCUITRON_PRICES_FILE', raising=False)
    monkeypatch.setenv('CIRCUITRON_DISABLE_BUILTIN_PRICES', '1')

    import circuitron.cost_estimator as ce
    importlib.reload(ce)

    assert ce.price_source() in ('none', '')
    token_summary = {
        "overall": {"input": 1_000_000, "output": 0, "total": 1_000_000, "cached_input": 0},
        "by_model": {"o4-mini": {"input": 1_000_000, "output": 0, "total": 1_000_000, "cached_input": 0}},
    }
    total, used_default, per_model = ce.estimate_cost_usd(token_summary)
    assert total == 0.0
    assert used_default is True
    assert per_model["o4-mini"] == 0.0
