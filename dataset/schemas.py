"""Pydantic models defining raw dataset schemas.

These models provide explicit contracts for the JSONL records consumed by
the dataset builders. Using them ensures that malformed entries are caught
early during the build step, which is a requirement for the deterministic
dataset pipeline in Phase 3.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class IOPairRecord(BaseModel):
    """Simple input/output pair used by Codeforces and AtCoder tasks."""

    input: str
    output: str


class HumanEvalCPPRecord(BaseModel):
    """Schema for a single HumanEval-CPP JSONL record."""

    task_id: str
    prompt: str
    test: str
    reference_solution: Optional[str] = None


class CodeforcesRecord(BaseModel):
    """Schema for a Codeforces-Intro dataset record."""

    task_id: str
    prompt: str
    tests: List[IOPairRecord]
    time_limit_ms: int = Field(default=2000, ge=1)
    memory_limit_kb: int = Field(default=256_000, ge=1)


class AtCoderRecord(BaseModel):
    """Schema for an AtCoder ABC dataset record."""

    task_id: str
    prompt: str
    tests: List[IOPairRecord]
    time_limit_ms: int = Field(default=2000, ge=1)
    memory_limit_kb: int = Field(default=102_400, ge=1)
