from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from itertools import count
import asyncio
from .version import VersionInfo, collect_version_info


class Run(BaseModel):
    id: int
    config: Dict[str, str] = Field(default_factory=dict)
    status: str = "pending"
    logs: List[str] = Field(default_factory=list)
    artifact: Optional[str] = None
    version: VersionInfo


class RunRegistry:
    """In-memory store for run metadata."""

    _id_counter = count(1)

    def __init__(self) -> None:
        self._runs: Dict[int, Run] = {}
        self._log_queues: Dict[int, asyncio.Queue[str]] = {}

    def create_run(self, config: Optional[Dict[str, str]] = None) -> Run:
        run_id = next(self._id_counter)
        seed_value = None
        if config and "seed" in config:
            try:
                seed_value = int(config["seed"])
            except (TypeError, ValueError):
                seed_value = None
        version = collect_version_info(seed=seed_value)
        run = Run(id=run_id, config=config or {}, version=version)
        self._runs[run_id] = run
        self._log_queues[run_id] = asyncio.Queue()
        return run

    def list_runs(self, offset: int = 0, limit: int = 10) -> List[Run]:
        runs = list(self._runs.values())
        return runs[offset: offset + limit]

    def get_run(self, run_id: int) -> Optional[Run]:
        """Return run by id if it exists."""
        return self._runs.get(run_id)

    def update_status(self, run_id: int, status: str) -> None:
        if run_id in self._runs:
            self._runs[run_id].status = status

    # Logging helpers -------------------------------------------------

    def append_log(self, run_id: int, message: str) -> None:
        if run_id in self._runs:
            self._runs[run_id].logs.append(message)
            self._log_queues[run_id].put_nowait(message)

    def get_logs(self, run_id: int) -> List[str]:
        """Return existing log lines for ``run_id``.

        ``dict.get`` eagerly evaluates its default argument, which caused a
        ``Run`` to be instantiated without required fields whenever a run was
        present in the registry. That surfaced as a validation error during
        WebSocket connections. We avoid that by looking up the run explicitly
        and creating a minimal placeholder only when it is truly missing.
        """
        run = self._runs.get(run_id)
        if run is None:
            run = Run(id=run_id, version=collect_version_info())
            self._runs[run_id] = run
            self._log_queues.setdefault(run_id, asyncio.Queue())
        return run.logs

    def get_log_queue(self, run_id: int) -> "asyncio.Queue[str]":
        return self._log_queues.setdefault(run_id, asyncio.Queue())


registry = RunRegistry()
