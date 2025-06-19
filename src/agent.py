import asyncio, json, os
import openai
from .prompts import PLAN_PROMPT, DOC_QA_PROMPT, SYSTEM_PROMPT, USER_TEMPLATE
from .mcp_client import perform_rag_query, search_code_examples
from .part_lookup import extract_queries, lookup_parts
from .skidl_exec import run_skidl_script
from .utils_llm import LLM_PLAN, call_llm
from .utils_text import trim_to_tokens, MAX_TOOL_CALLS

client = openai.AsyncOpenAI(
    api_key=os.getenv("DEVSTRAL_API_KEY"),
    base_url=os.getenv("DEVSTRAL_API_BASE", "https://api.openai.com/v1"),
)
MODEL_CODE = os.getenv("MODEL_CODE")
MODEL_TEMP = float(os.getenv("MODEL_TEMP", 0.15))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_docs",
            "description": "Fetch SKiDL documentation or code examples via the MCP server",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural-language or keyword query"},
                    "match_count": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    }
]

async def _rag(plan: str, match=8):
    docs  = await perform_rag_query({"query": plan, "match_count": match})
    codes = await search_code_examples({"query": plan, "match_count": 5})
    ctx   = "\n".join(c["content"] for c in docs + codes)
    return trim_to_tokens(ctx)

async def _retrieve_docs(query: str, match_count=3):
    docs  = await perform_rag_query({"query": query, "match_count": match_count})
    codes = await search_code_examples({"query": query, "match_count": match_count})
    return trim_to_tokens("\n".join(c["content"] for c in docs + codes))

async def pipeline(user_req: str):
    # A ▸ PLAN
    plan = await call_llm(LLM_PLAN, PLAN_PROMPT.replace("REQUIREMENTS", user_req))
    print("\n--- PLAN ---\n", plan)
    if input("\nApprove plan? [y/N] ").lower() != "y":
        print("Aborted."); return

    # B ▸ QUERIES → PARTS
    queries = await extract_queries(plan)
    parts   = lookup_parts(queries)

    # B2 ▸ DOC QUESTIONS
    doc_qs  = await call_llm(LLM_PLAN, DOC_QA_PROMPT.replace("<<<PLAN>>>", plan))
    answers = []
    for q in doc_qs.splitlines():
        q = q.strip()
        if not q:
            continue
        answers += await perform_rag_query({"query": q, "match_count": 3})
    extra_ctx = "\n".join(a["content"] for a in answers)

    # C ▸ RAG
    rag_ctx  = await _rag(plan)
    if extra_ctx:
        rag_ctx = trim_to_tokens(rag_ctx + "\n" + extra_ctx)

    # D ▸ CODEGEN with tool-calling
    user_msg = (USER_TEMPLATE
                .replace("<<<REQ>>>", user_req)
                .replace("<<<PLAN>>>", plan)
                .replace("<<<SELECTED_PARTS>>>", json.dumps(parts, indent=2))
                .replace("<<<RAG_CONTEXT>>>", rag_ctx))

    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    tool_calls = 0
    skidl_code = ""
    while True:
        stream = await client.chat.completions.create(
            model=MODEL_CODE,
            messages=msgs,
            tools=TOOLS,
            tool_choice="auto",
            temperature=MODEL_TEMP,
            stream=True,
        )
        content, call, buf = "", None, ""
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                content += delta.content
            if delta.tool_calls:
                part = delta.tool_calls[0]
                if not call:
                    call = {"id": part.id, "name": part.function.name}
                if part.function.arguments:
                    buf += part.function.arguments

        if call:
            if tool_calls >= MAX_TOOL_CALLS:
                raise RuntimeError("Max tool calls exceeded")
            tool_calls += 1
            args = json.loads(buf or "{}")
            docs = await _retrieve_docs(args.get("query", ""), args.get("match_count", 3))
            msgs.append({"role": "assistant", "tool_calls": [call]})
            msgs.append({"role": "tool", "tool_call_id": call["id"], "content": docs})
            continue
        skidl_code = content
        break

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
