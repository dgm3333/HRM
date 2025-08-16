from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable


class SandboxCache:
    """Simple filesystem cache for sandbox execution results.

    Entries are stored as JSON files named by a SHA256 hash.  Callers are
    responsible for constructing stable hash keys from the inputs that affect
    execution (e.g. prompt, code, tests, resource limits).
    """

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def hash_parts(parts: Iterable[bytes]) -> str:
        """Return a SHA256 hex digest for the given byte ``parts``."""
        h = hashlib.sha256()
        for p in parts:
            h.update(p)
        return h.hexdigest()

    def load(self, key: str) -> Dict[str, Any] | None:
        """Load a cached entry by ``key`` if present."""
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def store(self, key: str, data: Dict[str, Any]) -> None:
        """Store ``data`` under ``key``."""
        path = self.cache_dir / f"{key}.json"
        path.write_text(json.dumps(data))
