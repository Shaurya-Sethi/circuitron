"""Telemetry utilities for token usage aggregation via OpenTelemetry spans.

This module defines a thread-safe aggregator for GenAI token usage and a
SpanProcessor that extracts token attributes from finished spans.

Attributes captured (best-effort, based on Logfire/OTel conventions):
  - gen_ai.usage.input_tokens | gen_ai.token.input
  - gen_ai.usage.output_tokens | gen_ai.token.output
  - gen_ai.usage.total_tokens | gen_ai.token.total
  - gen_ai.usage.cached_input_tokens (optional)
  - Model: gen_ai.request.model | gen_ai.model.name | gen_ai.response.model

The aggregator is reset at the start of a run and summarized at the end.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import threading


@dataclass
class TokenTotals:
    input: int = 0
    output: int = 0
    total: int = 0
    cached_input: int = 0


class TokenUsageAggregator:
    """Aggregate token usage overall and per model in a thread-safe way."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._overall = TokenTotals()
        self._by_model: Dict[str, TokenTotals] = {}

    def reset(self) -> None:
        with self._lock:
            self._overall = TokenTotals()
            self._by_model.clear()

    def record_tokens(
        self,
        model: Optional[str],
        input_tokens: int | None,
        output_tokens: int | None,
        total_tokens: int | None,
        cached_input_tokens: int | None = None,
    ) -> None:
        """Record a usage event safely.

        If total_tokens is missing, it is computed as input + output (missing treated as 0).
        """
        m = (model or "unknown").strip() or "unknown"
        i = int(input_tokens or 0)
        o = int(output_tokens or 0)
        t = int(total_tokens if total_tokens is not None else (i + o))
        c = int(cached_input_tokens or 0)

        with self._lock:
            # Update overall
            self._overall.input += i
            self._overall.output += o
            self._overall.total += t
            self._overall.cached_input += c

            # Update per model
            mt = self._by_model.get(m)
            if mt is None:
                mt = TokenTotals()
                self._by_model[m] = mt
            mt.input += i
            mt.output += o
            mt.total += t
            mt.cached_input += c

    def get_summary(self) -> dict:
        """Return a JSON-serializable summary of token usage."""
        with self._lock:
            by_model = {
                model: {
                    "input": tt.input,
                    "output": tt.output,
                    "total": tt.total,
                    "cached_input": tt.cached_input,
                }
                for model, tt in self._by_model.items()
            }
            return {
                "overall": {
                    "input": self._overall.input,
                    "output": self._overall.output,
                    "total": self._overall.total,
                    "cached_input": self._overall.cached_input,
                },
                "by_model": by_model,
            }


# Global aggregator instance
token_usage_aggregator = TokenUsageAggregator()


# --- OpenTelemetry integration -------------------------------------------------

try:  # Optional: only if OTEL SDK is present
    from opentelemetry.trace import get_tracer_provider  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import (
        SpanProcessor,  # type: ignore
    )
    from opentelemetry.sdk.trace import ReadableSpan  # type: ignore
except Exception:  # pragma: no cover - graceful degradation if OTEL missing
    SpanProcessor = object  # type: ignore
    TracerProvider = object  # type: ignore
    ReadableSpan = object  # type: ignore
    def get_tracer_provider() -> object:  # type: ignore[explicit-ellipsis]
        return None


class TokenUsageSpanProcessor(SpanProcessor):
    """SpanProcessor that extracts token attributes from GenAI spans."""

    def on_start(self, span: object) -> None:  # pragma: no cover - noop
        return None

    def on_end(self, span: object) -> None:  # pragma: no cover - integration tested indirectly
        try:
            attrs = getattr(span, "attributes", None) or {}
            # Token attributes (check both modern and legacy keys)
            i = _safe_int(attrs.get("gen_ai.usage.input_tokens", attrs.get("gen_ai.token.input")))
            o = _safe_int(attrs.get("gen_ai.usage.output_tokens", attrs.get("gen_ai.token.output")))
            t = _safe_int(attrs.get("gen_ai.usage.total_tokens", attrs.get("gen_ai.token.total")))
            c = _safe_int(attrs.get("gen_ai.usage.cached_input_tokens"))

            # Model attributes
            model = attrs.get("gen_ai.request.model") or attrs.get("gen_ai.model.name") or attrs.get("gen_ai.response.model")

            # Ignore spans without any token data
            if any(v is not None for v in (i, o, t, c)):
                token_usage_aggregator.record_tokens(
                    str(model) if model is not None else None,
                    i,
                    o,
                    t,
                    c,
                )
        except Exception:
            # Never raise from span hooks
            return None

    def shutdown(self) -> None:  # pragma: no cover - noop
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - noop
        return True


def _safe_int(v: object | None) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)  # type: ignore[arg-type]
    except Exception:
        return None


def attach_span_processor_if_possible() -> bool:
    """Attach TokenUsageSpanProcessor to the active TracerProvider if available.

    Returns True if attached; False if not possible in the current environment.
    """
    try:
        provider = get_tracer_provider()
        if not isinstance(provider, TracerProvider):  # type: ignore[arg-type]
            return False
        # Avoid duplicate processors by checking existing ones if available
        # TracerProvider API doesn't expose processors publicly; adding twice is harmless but we try to be cautious.
        provider.add_span_processor(TokenUsageSpanProcessor())  # type: ignore[no-untyped-call]
        return True
    except Exception:
        return False


__all__ = [
    "TokenUsageAggregator",
    "TokenUsageSpanProcessor",
    "token_usage_aggregator",
    "attach_span_processor_if_possible",
]


# --- Agents SDK integration (fallback if OTel attrs aren't present) ---------

def record_from_run_result(result: object) -> None:
    """Best-effort aggregation of token usage from an Agents SDK RunResult.

    Many environments won't expose OpenTelemetry token attributes locally.
    As a fallback, we read ``result.raw_responses`` which typically contains
    provider responses with model and token usage data.

    The function is defensive: it tolerates absent fields and different
    shapes (attributes vs dicts).

    Args:
        result: An instance of ``agents.result.RunResult`` (or similar) with
            a ``raw_responses`` attribute that is an iterable of provider
            responses. Each response may expose:
              - ``model`` (str)
              - ``usage`` object or dict with keys/attrs:
                    input_tokens, output_tokens, total_tokens, cached_input_tokens
    """
    try:
        raw_responses = getattr(result, "raw_responses", None)
        if not raw_responses:
            return

        for resp in raw_responses:
            # Model name
            model = None
            if isinstance(resp, dict):
                model = resp.get("model") or resp.get("response_model") or resp.get("model_name")  # type: ignore[assignment]
            else:
                model = (
                    getattr(resp, "model", None)
                    or getattr(resp, "response_model", None)
                    or getattr(resp, "model_name", None)
                )

            usage = getattr(resp, "usage", None) if not isinstance(resp, dict) else resp.get("usage")

            # Allow dict-like or attribute-like usage
            def _get_usage_val(key: str) -> int | None:
                if usage is None:
                    return None
                try:
                    if isinstance(usage, dict):
                        val = usage.get(key)
                    else:
                        val = getattr(usage, key, None)
                    return int(val) if val is not None else None
                except Exception:
                    return None

            i = _get_usage_val("input_tokens")
            o = _get_usage_val("output_tokens")
            t = _get_usage_val("total_tokens")
            c = _get_usage_val("cached_input_tokens")

            # Only record if we saw any token fields
            if any(v is not None for v in (i, o, t, c)):
                token_usage_aggregator.record_tokens(
                    str(model) if model is not None else None,
                    i,
                    o,
                    t,
                    c,
                )
    except Exception:
        # Never raise from telemetry helpers
        return None

