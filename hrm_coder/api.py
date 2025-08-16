from __future__ import annotations

from typing import Dict
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
    run.artifact = f"/artifacts/run_{run.id}/"
    registry.append_log(run.id, "training started")
    registry.update_status(run.id, "training")
    return run


@app.post("/eval", response_model=Run)
def start_eval(config: Dict[str, str] | None = None):
    run = registry.create_run(config)
    run.artifact = f"/artifacts/run_{run.id}/"
    registry.append_log(run.id, "evaluation started")
    registry.update_status(run.id, "evaluating")
    return run


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
