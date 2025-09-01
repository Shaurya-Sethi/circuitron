from __future__ import annotations

import types
import sys

from circuitron.telemetry import TokenUsageAggregator
import circuitron.cost_estimator as ce


def test_token_usage_aggregator_basic() -> None:
    agg = TokenUsageAggregator()
    agg.reset()
    agg.record_tokens("o4-mini", 100, 50, None)
    agg.record_tokens("gpt-5", 200, 0, 200)
    summary = agg.get_summary()
    assert summary["overall"]["input"] == 300
    assert summary["overall"]["output"] == 50
    assert summary["overall"]["total"] == 350  # 100+50 + 200
    assert "o4-mini" in summary["by_model"]
    assert "gpt-5" in summary["by_model"]


def test_cost_estimator_without_local_prices(monkeypatch) -> None:
    import importlib
    # Ensure built-in/env prices are not used
    sys.modules.pop('circuitron._model_prices_local', None)
    monkeypatch.delenv('CIRCUITRON_PRICES_FILE', raising=False)
    monkeypatch.setenv('CIRCUITRON_DISABLE_BUILTIN_PRICES', '1')
    importlib.reload(ce)
    token_summary = {
        "overall": {"input": 1000, "output": 500, "total": 1500, "cached_input": 0},
        "by_model": {
            "o4-mini": {"input": 1000, "output": 500, "total": 1500, "cached_input": 0},
        },
    }
    total, used_default, per_model = ce.estimate_cost_usd(token_summary)
    assert total == 0.0
    assert used_default is True
    assert per_model["o4-mini"] == 0.0


def test_cost_estimator_with_local_prices(monkeypatch) -> None:
    # Inject a fake prices module
    fake = types.SimpleNamespace(PRICES={"o4-mini": {"input": 1.0, "output": 2.0, "cached_input": 0.5}})
    sys.modules['circuitron._model_prices_local'] = fake  # type: ignore
    from importlib import reload
    import circuitron.cost_estimator as ce
    reload(ce)

    token_summary = {
        "overall": {"input": 1_000_000, "output": 500_000, "total": 1_500_000, "cached_input": 100_000},
        "by_model": {"o4-mini": {"input": 1_000_000, "output": 500_000, "total": 1_500_000, "cached_input": 100_000}},
    }
    total, used_default, per_model = ce.estimate_cost_usd(token_summary)
    # Cost: 1M*1.0 + 0.5M*2.0 + 0.1M*0.5 = 1 + 1 + 0.05 = 2.05
    assert round(total, 2) == 2.05
    assert used_default is False
    assert round(per_model["o4-mini"], 2) == 2.05
