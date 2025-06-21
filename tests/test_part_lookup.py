import asyncio
import sys
import pathlib
import types
import os

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide lightweight stubs for modules imported by part_lookup.
prompts_stub = types.ModuleType("src.prompts")
prompts_stub.PART_PROMPT = ""
sys.modules["src.prompts"] = prompts_stub

os.environ.setdefault("MISTRAL_API_KEY", "test")
os.environ.setdefault("MODEL_PLAN", "stub")
os.environ.setdefault("MODEL_PART", "stub")
os.environ.setdefault("MODEL_CODE", "stub")
import src.utils_llm as ul

async def dummy_call_llm(model, text):
    return "[]"

ul.call_llm = dummy_call_llm
ul.LLM_PART = object()

import src.part_lookup as pl

class DummyPart:
    def __init__(self, lib, name, desc=""):
        self.lib = lib
        self.name = name
        self.description = desc

def test_extract_queries(monkeypatch):
    plan = """header\n### DRAFT_SEARCH_QUERIES\nopamp low-noise dip-8\n^LM386$\n### PART_CANDIDATES"""

    async def fake_call_llm(model, text):
        cleaned = text.split("\n", 1)[1]
        lines = [l for l in cleaned.splitlines() if l]
        import json
        return json.dumps(lines)

    monkeypatch.setattr(ul, "call_llm", fake_call_llm)
    queries = asyncio.run(ul.extract_queries(plan))
    assert queries == ["opamp low-noise dip-8", "^LM386$"]

def test_lookup_parts_preserves_query(monkeypatch):
    captured = []

    def fake_search(q):
        captured.append(q)
        return [DummyPart("lib", "part", "desc")]

    monkeypatch.setattr(pl, "search", fake_search)
    results = pl.lookup_parts("opamp (low-noise|dip-8)")
    assert captured == ["opamp (low-noise|dip-8)"]
    assert results["opamp (low-noise|dip-8)"][0]["part"] == "lib:part"


def test_lookup_parts_handles_invalid(monkeypatch):
    def fake_search_none(q):
        return None

    monkeypatch.setattr(pl, "search", fake_search_none)
    # A malformed query should be skipped and return an empty list
    results = pl.lookup_parts("[")
    assert results == {"[": []}


def test_lookup_parts_handles_search_error(monkeypatch):
    def fake_search_error(q):
        raise RuntimeError("regex failure")

    monkeypatch.setattr(pl, "search", fake_search_error)
    results = pl.lookup_parts("bad")
    assert results == {"bad": []}

