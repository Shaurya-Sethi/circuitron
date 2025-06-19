import os
from dotenv import load_dotenv
from langchain.chat_models import ChatMistralAI
from langchain.schema import HumanMessage, SystemMessage

load_dotenv()

def _model(name: str, temp: float):
    return ChatMistralAI(
        model=name,
        temperature=temp,
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        base_url=os.getenv("MISTRAL_API_BASE", "https://api.mistral.ai/v1"),
    )

LLM_PLAN = _model(os.getenv("MODEL_PLAN"),  float(os.getenv("MODEL_TEMP", .15)))
LLM_PART = _model(os.getenv("MODEL_PART"),  float(os.getenv("MODEL_TEMP", .15)))
LLM_CODE = _model(os.getenv("MODEL_CODE"),  float(os.getenv("MODEL_TEMP", .15)))

async def call_llm(model, prompt: str):
    msgs = [SystemMessage(content=""), HumanMessage(content=prompt)]
    return (await model.ainvoke(msgs)).content
