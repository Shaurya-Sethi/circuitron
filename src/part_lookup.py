"""Utilities for performing advanced SKiDL part searches."""

import re, json
from skidl import search
from .prompts import PART_PROMPT
from .utils_llm import call_llm, LLM_PART

# Allow a wide range of characters so the query string can include
# SKiDL's advanced search syntax (regex, quoted strings, OR logic, etc.).
QUERY_RE     = re.compile(r"^[A-Za-z0-9_ .+()\-|'\"^$*?\[\]]+$")
VALID_PARTRE = re.compile(r"^[A-Za-z0-9_]+:[A-Za-z0-9_.+\-]+$")

def _run_search(query: str, max_choices=3):
    """Return up to *max_choices* parts matching *query*.

    The query string is passed verbatim to ``skidl.search`` which supports
    quoted phrases, regular expressions, OR pipes, and multi-term queries.
    Results are returned as ``{"part": "lib:name", "desc": "description"}``
    dictionaries.
    """

    hits = list(search(query))
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
    """Extract and clean draft search queries from *plan* using the LLM."""

    # pull draft list from plan (lines after the heading)
    draft = []
    grab  = False
    for line in plan.splitlines():
        if "Draft search queries" in line or "Draft search keywords" in line:
            grab = True
            continue
        if grab and line.strip():
            draft.append(line.strip())
        elif grab and not line.strip():
            break
    draft_txt = "\n".join(draft)

    cleaned = await call_llm(LLM_PART, PART_PROMPT + "\n" + draft_txt)
    try:
        queries = json.loads(cleaned)
    except Exception:
        queries = [q.strip() for q in cleaned.splitlines()]
    return [q for q in queries if isinstance(q, str) and q.strip() and QUERY_RE.match(q)]

def lookup_parts(queries, max_choices=3):
    """Return matching parts for each search query."""

    return {q: _run_search(q, max_choices) for q in queries}
