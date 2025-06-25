"""Text processing utilities for OpenAI-based agents."""
import os
import re
import tiktoken

# OpenAI tokenization only
TOKEN_MODEL = os.getenv("TOKEN_MODEL", "gpt-4o")
try:
    ENC = tiktoken.encoding_for_model(TOKEN_MODEL)
except Exception:
    ENC = tiktoken.get_encoding("cl100k_base")

MAX_CTX_TOK = int(os.getenv("MAX_CTX_TOK", "128000"))  # GPT-4o context limit
SAFETY_MARGIN = int(os.getenv("SAFETY_MARGIN", "4000"))

def trim_to_tokens(text: str, max_tokens: int = MAX_CTX_TOK) -> str:
    """Trim text to fit within token limits."""
    tokens = ENC.encode(text)
    limit = max_tokens - SAFETY_MARGIN
    if len(tokens) <= limit:
        return text
    return ENC.decode(tokens[:limit])

# Keep existing text parsing utilities
HDR = re.compile(r"^###\s+[A-Z_]+", re.M)
QUERY_RE = re.compile(r"^[A-Za-z0-9_ .+()\-|'\"^$*?\[\]]+$")

def extract_block(plan: str, header: str) -> str:
    """Return text under the *last* '### {header}' heading, ignoring <think>."""
    if "</think>" in plan:
        plan = plan.split("</think>", 1)[1]
    anchor = f"### {header}"
    start = plan.rfind(anchor)
    if start == -1:
        return ""
    chunk = plan[start + len(anchor):]
    nxt = HDR.search(chunk)
    return chunk[:nxt.start() if nxt else None].strip()
