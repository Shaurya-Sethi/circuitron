from __future__ import annotations

from types import SimpleNamespace

from circuitron.telemetry import token_usage_aggregator, record_from_run_result


def test_record_from_run_result_with_dict_usage() -> None:
    # Fake raw response with dict usage
    resp = {
        "model": "o4-mini",
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "cached_input_tokens": 10},
    }
    result = SimpleNamespace(raw_responses=[resp])

    token_usage_aggregator.reset()
    record_from_run_result(result)
    summary = token_usage_aggregator.get_summary()
    assert summary["overall"]["input"] == 100
    assert summary["overall"]["output"] == 40
    assert summary["overall"]["total"] == 140
    assert summary["overall"]["cached_input"] == 10
    assert "o4-mini" in summary["by_model"]


def test_record_from_run_result_with_attr_usage() -> None:
    # Fake raw response with attribute-style usage
    usage = SimpleNamespace(input_tokens=5, output_tokens=7, total_tokens=12, cached_input_tokens=0)
    resp = SimpleNamespace(model="gpt-5-mini", usage=usage)
    result = SimpleNamespace(raw_responses=[resp])

    token_usage_aggregator.reset()
    record_from_run_result(result)
    summary = token_usage_aggregator.get_summary()
    assert summary["overall"]["input"] == 5
    assert summary["overall"]["output"] == 7
    assert summary["overall"]["total"] == 12
    assert summary["overall"]["cached_input"] == 0
    assert "gpt-5-mini" in summary["by_model"]
