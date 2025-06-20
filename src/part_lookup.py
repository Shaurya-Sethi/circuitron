"""Utilities for performing advanced SKiDL part searches.

This module exposes helper functions used by the agent to turn natural
language queries into component selections.  Queries may contain quoted
phrases, regular expressions and boolean logic as supported by
``skidl.search``.  The search path respects the ``KICAD_SYMBOL_DIR``
environment variable so results mirror the user's KiCad setup.
"""

import re, json
from skidl import search
from .prompts import PART_PROMPT
from .utils_llm import call_llm, LLM_PART

# Allow a wide range of characters so the query string can include
# SKiDL's advanced search syntax (regex, quoted strings, OR logic, etc.).
QUERY_RE = re.compile(r"^[A-Za-z0-9_ .+()\-|'\"^$*?\[\]]+$")
VALID_PARTRE = re.compile(r"^[A-Za-z0-9_]+:[A-Za-z0-9_.+\-]+$")


def _run_search(query: str, max_choices: int = 3) -> list[dict]:
    """Return up to ``max_choices`` parts matching ``query``.

    The *query* string is passed verbatim to :func:`skidl.search` so callers may
    use regular expressions, quoted phrases and boolean logic.  The search path
    honours ``KICAD_SYMBOL_DIR`` if set.

    Each result is a ``{"part": "lib:name", "desc": "description"}`` dictionary.
    """

    try:
        hits = list(search(query))
    except Exception as exc:
        # Propagate a clear error message rather than failing silently.
        raise RuntimeError(f"search failed for '{query}': {exc}") from exc
    out: list[dict] = []
    seen = set()
    for p in hits:
        ident = f"{p.lib}:{p.name}"
        if ident in seen or not VALID_PARTRE.match(ident):
            continue
        out.append({"part": ident, "desc": getattr(p, "description", "").strip()})
        seen.add(ident)
        if len(out) >= max_choices:
            break
    return out


async def extract_queries(plan: str):
    """Extract and clean search terms from ``plan`` using the LLM.

    The lines following the ``DRAFT_SEARCH_QUERIES`` heading are collected until
    the next ``###`` heading.  The text is then passed to the LLM for
    normalisation according to :data:`PART_PROMPT`.
    """

    draft: list[str] = []
    grab = False
    for line in plan.splitlines():
        tag = line.replace(" ", "_").upper()
        if not grab and "DRAFT_SEARCH_QUERIES" in tag:
            grab = True
            continue
        if grab and line.startswith("### "):
            break
        if grab and line.strip():
            draft.append(line.strip())
    draft_txt = "\n".join(draft)

    cleaned = await call_llm(LLM_PART, PART_PROMPT + "\n" + draft_txt)
    try:
        queries = json.loads(cleaned)
    except Exception:
        queries = [q.strip() for q in cleaned.splitlines()]
    return [
        q for q in queries if isinstance(q, str) and q.strip() and QUERY_RE.match(q)
    ]


def lookup_parts(queries, max_choices: int = 3):
    """Return matching parts for each search query.

    ``queries`` may be a single string (with line breaks) or an iterable of
    strings.  Each query is sent verbatim to :func:`skidl.search`.
    """

    if isinstance(queries, str):
        queries = [q.strip() for q in queries.splitlines() if q.strip()]
    return {q: _run_search(q, max_choices) for q in queries}
