from fastapi import FastAPI
from pydantic import BaseModel
import io
from contextlib import redirect_stdout, redirect_stderr

from circuitron.models import UserFeedback

# Repo scan summary:
# CLI entry: circuitron/cli.py -> calls pipeline.pipeline
# Core orchestration in circuitron/pipeline.py
# Agents defined in circuitron/agents.py
# Tools containerize KiCad/SKiDL via Docker in circuitron/tools.py
# Many modules print to stdout which will be captured here

app = FastAPI()

class RunRequest(BaseModel):
    prompt: str
    reasoning: bool = False
    debug: bool = False
    user_feedback: UserFeedback | None = None

@app.post("/run")
async def run_job(req: RunRequest):
    """Execute the Circuitron pipeline and capture stdout and stderr."""
    from circuitron.pipeline import pipeline

    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        result = await pipeline(
            req.prompt,
            show_reasoning=req.reasoning,
            debug=req.debug,
            user_feedback=req.user_feedback,
            interactive=False,
        )
    return {
        "status": "ok",
        "stdout": buf_out.getvalue(),
        "stderr": buf_err.getvalue(),
        "result": result.model_dump(),
    }
