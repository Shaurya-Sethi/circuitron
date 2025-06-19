import re, asyncio
from skidl import search
from prompts import PART_PROMPT
from utils_llm import call_llm, LLM_PART

KEYWORD_RE   = re.compile(r"^[A-Za-z0-9_\-+().]+$")
VALID_PARTRE = re.compile(r"^[A-Za-z0-9_]+:[A-Za-z0-9_.+\-]+$")

def _exact_first(keyword: str, max_choices=3):
    exact = list(search(f"^{keyword}$"))
    fuzzy = [] if exact else list(search(keyword))
    hits  = exact + fuzzy
    out   = []
    for p in hits:
        ident = f"{p.lib}:{p.name}"
        if ident not in out and VALID_PARTRE.match(ident):
            out.append(ident)
        if len(out) >= max_choices:
            break
    return out

async def extract_keywords(plan: str):
    # pull draft list from plan (lines after "Draft search keywords")
    draft = []
    grab  = False
    for line in plan.splitlines():
        if "Draft search keywords" in line:
            grab = True
            continue
        if grab and line.strip():
            draft.append(line.strip())
        elif grab and not line.strip():
            break
    draft_txt = "\n".join(draft)

    cleaned = await call_llm(LLM_PART, PART_PROMPT + "\n" + draft_txt)
    return [kw for kw in cleaned.splitlines() if KEYWORD_RE.match(kw)]

def lookup_parts(keywords, max_choices=3):
    return {kw: _exact_first(kw, max_choices) for kw in keywords}
