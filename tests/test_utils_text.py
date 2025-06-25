import sys
import pathlib
import os
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["TOKEN_MODEL"] = "gpt-4o"

# Stub tiktoken before importing utils_text
tiktoken_stub = types.ModuleType("tiktoken")
class DummyTok:
    def encode(self, text):
        return [1]
    def decode(self, toks):
        return ""
tiktoken_stub.encoding_for_model = lambda m: DummyTok()
tiktoken_stub.get_encoding = lambda n: DummyTok()
sys.modules["tiktoken"] = tiktoken_stub

from src.utils_text import extract_block


def test_extract_block_last_post_think():
    plan = """
<think>foo</think>
### DRAFT_SEARCH_QUERIES
foo
### OTHER
bar
### DRAFT_SEARCH_QUERIES
baz
qux
"""
    out = extract_block(plan, "DRAFT_SEARCH_QUERIES")
    assert out == "baz\nqux"
