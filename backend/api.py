from fastapi import FastAPI
from pydantic import BaseModel
import io
from contextlib import redirect_stdout

# Repo scan summary:
# CLI entry: circuitron/cli.py -> calls pipeline.pipeline
# Core orchestration in circuitron/pipeline.py
# Agents defined in circuitron/agents.py
# Tools containerize KiCad/SKiDL via Docker in circuitron/tools.py
# Many modules print to stdout which will be captured here

app = FastAPI()

class RunRequest(BaseModel):
    job_params: str

@app.post("/run")
async def run_job(req: RunRequest):
    """Execute the Circuitron pipeline and capture stdout."""
    from circuitron.pipeline import pipeline

    buf = io.StringIO()
    with redirect_stdout(buf):
        result = await pipeline(req.job_params)
    return {"status": "ok", "stdout": buf.getvalue(), "result": result.model_dump()}
