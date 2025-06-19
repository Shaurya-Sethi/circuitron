import asyncio, json, os
from prompts import PLAN_PROMPT, CODEGEN_PROMPT
from mcp_client import perform_rag_query, search_code_examples
from part_lookup import extract_keywords, lookup_parts
from skidl_exec import run_skidl_script
from utils_llm import LLM_PLAN, LLM_CODE, call_llm

async def _rag(plan: str, match=8):
    docs  = await perform_rag_query({"query": plan, "match_count": match})
    codes = await search_code_examples({"query": plan, "match_count": 5})
    return "\n".join(c["content"] for c in docs + codes)[:8000]

async def pipeline(user_req: str):
    # A ▸ PLAN
    plan = await call_llm(LLM_PLAN, PLAN_PROMPT.replace("REQUIREMENTS", user_req))
    print("\n--- PLAN ---\n", plan)
    if input("\nApprove plan? [y/N] ").lower() != "y":
        print("Aborted."); return

    # B ▸ KEYWORDS → PARTS
    keywords = await extract_keywords(plan)
    parts    = lookup_parts(keywords)

    # C ▸ RAG
    rag_ctx  = await _rag(plan)

    # D ▸ CODEGEN
    prompt = (CODEGEN_PROMPT
              .replace("<<<REQ>>>", user_req)
              .replace("<<<PLAN>>>", plan)
              .replace("<<<SELECTED_PARTS>>>", json.dumps(parts, indent=2))
              .replace("<<<RAG_CONTEXT>>>", rag_ctx))
    skidl_code = await call_llm(LLM_CODE, prompt)
    print("\n--- GENERATED CODE ---\n", skidl_code)

    # E ▸ EXECUTE
    try:
        artefacts = run_skidl_script(skidl_code)
        print(f"\nNetlist:   {artefacts['netlist']}")
        print(f"Schematic: {artefacts['svg']}")
    except Exception as e:
        print("Execution failed:", e)

def cli():
    req = input("Enter design request: ")
    asyncio.run(pipeline(req))

if __name__ == "__main__":
    cli()
