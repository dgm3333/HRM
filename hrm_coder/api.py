from __future__ import annotations

from typing import Dict, Optional
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .run_registry import registry, Run

app = FastAPI(title="HRM Coder")

# Allow local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/runs", response_model=list[Run])
def get_runs(offset: int = 0, limit: int = 10):
    return registry.list_runs(offset, limit)


@app.post("/train", response_model=Run)
def start_train(
    config: Dict[str, str] | None = None,
    seed: Optional[int] = None,
    docker_digest: Optional[str] = None,
):
    run = registry.create_run(config, seed=seed, docker_digest=docker_digest)
    registry.update_status(run.id, "training")
    return run


@app.post("/eval", response_model=Run)
def start_eval(
    config: Dict[str, str] | None = None,
    seed: Optional[int] = None,
    docker_digest: Optional[str] = None,
):
    run = registry.create_run(config, seed=seed, docker_digest=docker_digest)
    registry.update_status(run.id, "evaluating")
    return run


@app.websocket("/logs/ws")
async def websocket_logs(ws: WebSocket):
    await ws.accept()
    await ws.send_text("log stream started")
    await ws.close()
