from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from hrm_coder import app


def test_run_lifecycle():
    client = TestClient(app)

    # Initially empty
    assert client.get("/runs").json() == []

    # Start training run
    resp = client.post("/train", json={"foo": "bar"})
    run = resp.json()
    assert run["status"] == "training"

    # Listing returns the run
    runs = client.get("/runs").json()
    assert len(runs) == 1
    assert runs[0]["id"] == run["id"]

