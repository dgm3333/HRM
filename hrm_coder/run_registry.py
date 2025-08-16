from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from itertools import count
import subprocess
from pathlib import Path


def _get_git_sha() -> str:
    """Return the current git commit SHA or 'unknown' if not available."""
    try:
        repo_root = Path(__file__).resolve().parent.parent
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root)
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


class Run(BaseModel):
    id: int
    config: Dict[str, str] = Field(default_factory=dict)
    status: str = "pending"
    git_sha: str = Field(default_factory=_get_git_sha)
    docker_digest: Optional[str] = None
    seed: Optional[int] = None


class RunRegistry:
    """In-memory store for run metadata."""

    _id_counter = count(1)

    def __init__(self) -> None:
        self._runs: Dict[int, Run] = {}

    def create_run(
        self,
        config: Optional[Dict[str, str]] = None,
        seed: Optional[int] = None,
        docker_digest: Optional[str] = None,
    ) -> Run:
        run_id = next(self._id_counter)
        run = Run(
            id=run_id,
            config=config or {},
            seed=seed,
            docker_digest=docker_digest,
        )
        self._runs[run_id] = run
        return run

    def list_runs(self, offset: int = 0, limit: int = 10) -> List[Run]:
        runs = list(self._runs.values())
        return runs[offset : offset + limit]

    def update_status(self, run_id: int, status: str) -> None:
        if run_id in self._runs:
            self._runs[run_id].status = status


registry = RunRegistry()
