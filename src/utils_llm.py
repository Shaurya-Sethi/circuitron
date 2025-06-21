import os
from typing import Optional, cast

from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from pydantic.types import SecretStr

load_dotenv()

_api_key = os.getenv("MISTRAL_API_KEY")
if not _api_key:
    raise RuntimeError("MISTRAL_API_KEY environment variable not set")
API_KEY: str = cast(str, _api_key)


def _model(name: Optional[str], temp: float) -> ChatMistralAI:
    if not name:
        raise RuntimeError("Model name not specified")
    return ChatMistralAI(
        model_name=name,
        temperature=temp,
        api_key=SecretStr(API_KEY),
        base_url=os.getenv("MISTRAL_API_BASE", "https://api.mistral.ai/v1"),
    )


LLM_PLAN = _model(os.getenv("MODEL_PLAN"), float(os.getenv("MODEL_TEMP", 0.15)))
LLM_PART = _model(os.getenv("MODEL_PART"), float(os.getenv("MODEL_TEMP", 0.15)))
LLM_CODE = _model(os.getenv("MODEL_CODE"), float(os.getenv("MODEL_TEMP", 0.15)))


async def call_llm(model: ChatMistralAI, prompt: str) -> str:
    msgs = [SystemMessage(content=""), HumanMessage(content=prompt)]
    result: BaseMessage = await model.ainvoke(msgs)
    return cast(str, result.content)
