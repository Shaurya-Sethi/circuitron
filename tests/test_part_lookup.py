import asyncio
import sys
import pathlib
import types
import os
from unittest.mock import AsyncMock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide lightweight stubs for modules imported by part_lookup.
prompts_stub = types.ModuleType("src.prompts")
prompts_stub.PART_PROMPT = ""
sys.modules["src.prompts"] = prompts_stub

# Stub agents module with mock Runner
agents_stub = types.ModuleType("agents")
agents_stub.Runner = AsyncMock()
sys.modules["agents"] = agents_stub

utils_stub = types.ModuleType("src.utils_llm")
# Create mock agent
utils_stub.AGENT_PART = AsyncMock()
sys.modules["src.utils_llm"] = utils_stub

# Stub tiktoken to avoid network downloads during tests
tiktoken_stub = types.ModuleType("tiktoken")
class DummyTok:
    def encode(self, text):
        return [1]
    def decode(self, toks):
        return ""
tiktoken_stub.encoding_for_model = lambda m: DummyTok()
tiktoken_stub.get_encoding = lambda n: DummyTok()
sys.modules["tiktoken"] = tiktoken_stub

os.environ["TOKEN_MODEL"] = "gpt-4o"

import src.part_lookup as pl

class DummyPart:
    def __init__(self, lib, name, desc=""):
        self.lib = lib
        self.name = name
        self.description = desc

def test_extract_queries(monkeypatch):
    plan = """header\n### DRAFT_SEARCH_QUERIES\nopamp low-noise dip-8\n^LM386$\n### PART_CANDIDATES"""

    # Mock the Runner.run result
    mock_result = AsyncMock()
    mock_result.final_output = '["opamp low-noise dip-8", "^LM386$"]'
    
    async def fake_runner_run(agent, text):
        return mock_result

    monkeypatch.setattr("agents.Runner.run", fake_runner_run)
    queries = asyncio.run(pl.extract_queries(plan))
    assert queries == ["opamp low-noise dip-8", "^LM386$"]


def test_extract_queries_handles_string_json(monkeypatch):
    plan = "### DRAFT_SEARCH_QUERIES\nopamp"

    mock_result = AsyncMock()
    mock_result.final_output = '"opamp lm324"'
    
    async def fake_runner_run(agent, text):
        return mock_result

    monkeypatch.setattr("agents.Runner.run", fake_runner_run)
    queries = asyncio.run(pl.extract_queries(plan))
    assert queries == ["opamp lm324"]

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

