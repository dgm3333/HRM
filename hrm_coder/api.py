from __future__ import annotations

from typing import Dict, List
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .run_registry import registry, Run

app = FastAPI(title="HRM Coder")

# Allow local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts
STATIC_DIR = Path(__file__).parent / "static"
ARTIFACT_DIR = Path(__file__).parent / "artifacts"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/artifacts", StaticFiles(directory=ARTIFACT_DIR), name="artifacts")


@app.get("/runs", response_model=list[Run])
def get_runs(offset: int = 0, limit: int = 10):
    return registry.list_runs(offset, limit)


@app.get("/runs/{run_id}", response_model=Run)
def get_run(run_id: int):
    run = registry.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@app.post("/train", response_model=Run)
def start_train(config: Dict[str, str] | None = None):
    run = registry.create_run(config)
    _init_artifact(run.id)
    registry.append_log(run.id, "training started")
    registry.update_status(run.id, "training")
    return run


@app.post("/eval", response_model=Run)
def start_eval(config: Dict[str, str] | None = None):
    run = registry.create_run(config)
    _init_artifact(run.id)
    registry.append_log(run.id, "evaluation started")
    registry.update_status(run.id, "evaluating")
    return run


def _init_artifact(run_id: int) -> None:
    """Create an artifact directory with a placeholder file."""
    path = ARTIFACT_DIR / f"run_{run_id}"
    path.mkdir(parents=True, exist_ok=True)
    placeholder = path / "README.txt"
    if not placeholder.exists():
        placeholder.write_text("artifacts for run %d" % run_id)
    registry.get_run(run_id).artifact = f"/artifacts/run_{run_id}/"


@app.get("/runs/{run_id}/artifacts")
def list_artifacts(run_id: int) -> Dict[str, List[str]]:
    """Return a list of artifact files for a run."""
    run = registry.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    path = ARTIFACT_DIR / f"run_{run_id}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact not found")
    files = [str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()]
    return {"files": files}


@app.get("/runs/{run_id}/junit")
def junit_summary(run_id: int) -> Dict[str, int]:
    """Return a summary of JUnit results for a run."""
    run = registry.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    junit_path = ARTIFACT_DIR / f"run_{run_id}" / "junit.xml"
    if not junit_path.exists():
        raise HTTPException(status_code=404, detail="junit not found")
    try:
        root = ET.parse(junit_path).getroot()
    except ET.ParseError:
        raise HTTPException(status_code=400, detail="invalid junit")

    def _extract(node: ET.Element) -> tuple[int, int]:
        tests = int(node.attrib.get("tests", 0))
        failures = int(node.attrib.get("failures", 0))
        errors = int(node.attrib.get("errors", 0))
        return tests, failures + errors

    if root.tag == "testsuites":
        total_tests = total_failures = 0
        for child in root.findall("testsuite"):
            t, f = _extract(child)
            total_tests += t
            total_failures += f
    else:
        total_tests, total_failures = _extract(root)

    return {"tests": total_tests, "failures": total_failures}


@app.get("/runs/{run_id}/coverage")
def coverage_summary(run_id: int) -> Dict[str, float]:
    """Return line coverage percentage for a run."""
    run = registry.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    cov_path = ARTIFACT_DIR / f"run_{run_id}" / "coverage.json"
    if not cov_path.exists():
        raise HTTPException(status_code=404, detail="coverage not found")
    try:
        data = json.loads(cov_path.read_text())
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid coverage")
    line_cov = data.get("line") or data.get("lines") or data.get("line_percent")
    try:
        line_cov = float(line_cov)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="invalid coverage")
    return {"line": line_cov}


class RunUpdate(BaseModel):
    """Payload for run status updates."""

    status: str | None = None


@app.patch("/runs/{run_id}", response_model=Run)
def update_run(run_id: int, payload: RunUpdate):
    """Update mutable fields of a run such as status."""
    run = registry.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    if payload.status is not None:
        registry.update_status(run_id, payload.status)
    return registry.get_run(run_id)


class LogMessage(BaseModel):
    message: str


@app.post("/runs/{run_id}/logs")
def post_log(run_id: int, msg: LogMessage) -> Dict[str, str]:
    """Append a log line to a run."""
    run = registry.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    registry.append_log(run_id, msg.message)
    return {"status": "ok"}


@app.websocket("/logs/ws/{run_id}")
async def websocket_logs(ws: WebSocket, run_id: int):
    await ws.accept()
    # Send existing logs
    for line in registry.get_logs(run_id):
        await ws.send_text(line)
    queue = registry.get_log_queue(run_id)
    while not queue.empty():
        queue.get_nowait()
    try:
        while True:
            line = await queue.get()
            await ws.send_text(line)
    except WebSocketDisconnect:
        return
