from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.agent.orchestrator import DesignAgent
from backend.utils.logging import get_logger
from backend.utils.config import Settings

logger = get_logger()
settings = Settings()

app = FastAPI(title="Circuitron API")


class DesignPrompt(BaseModel):
    prompt: str


class DesignResponse(BaseModel):
    plan: str


@app.get("/ping")
async def ping() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/design", response_model=DesignResponse)
async def design(prompt: DesignPrompt) -> DesignResponse:
    """Generate a design plan from a user prompt."""
    try:
        agent = DesignAgent()
        plan = await agent.plan(prompt.prompt)
        return DesignResponse(plan=plan)
    except Exception as exc:  # pragma: no cover - placeholder
        logger.exception("Design generation failed")
        raise HTTPException(status_code=500, detail=str(exc))
