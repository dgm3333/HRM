from __future__ import annotations

"""Utilities for capturing reproducibility metadata."""

import os
import subprocess
from pydantic import BaseModel
from typing import Optional


class VersionInfo(BaseModel):
    """Record identifying a run's code and environment versions."""

    git_sha: str
    docker_digest: str
    seed: Optional[int] = None


def collect_version_info(seed: Optional[int] = None) -> VersionInfo:
    """Gather versioning information for the current run.

    Parameters
    ----------
    seed: Optional[int]
        The random seed associated with the run, if any.

    Returns
    -------
    VersionInfo
        Populated version information.
    """
    try:
        git_sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
            .strip()
        )
    except Exception:
        git_sha = "unknown"

    docker_digest = os.getenv("DOCKER_DIGEST", "unknown")

    return VersionInfo(git_sha=git_sha, docker_digest=docker_digest, seed=seed)
