from __future__ import annotations

from typing import Dict, List
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
