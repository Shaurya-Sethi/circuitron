from __future__ import annotations

import types
import sys

from circuitron.cost_estimator import estimate_cost_usd_for_model


def test_estimate_cost_usd_for_model_with_local_prices(monkeypatch) -> None:
    fake = types.SimpleNamespace(
        PRICES={
            "gpt-5-mini": {"input": 0.25, "output": 2.0, "cached_input": 0.025},
        }
    )
    sys.modules['circuitron._model_prices_local'] = fake  # type: ignore
    from importlib import reload
    import circuitron.cost_estimator as ce
    reload(ce)

    token_summary = {
        "overall": {"input": 2_000_000, "output": 1_000_000, "total": 3_000_000, "cached_input": 500_000},
        "by_model": {},
    }
    total, used_default = ce.estimate_cost_usd_for_model(token_summary, "gpt-5-mini")
    # 2M*0.25 + 1M*2.0 + 0.5M*0.025 = 0.5 + 2.0 + 0.0125 = 2.5125
    assert round(total, 4) == 2.5125
    assert used_default is False


def test_estimate_cost_usd_for_model_without_prices(monkeypatch) -> None:
    token_summary = {
        "overall": {"input": 1000, "output": 500, "total": 1500, "cached_input": 0},
        "by_model": {},
    }
    total, used_default = estimate_cost_usd_for_model(token_summary, "unknown-model")
    assert total == 0.0
    assert used_default is True
