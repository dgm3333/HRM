from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient  # noqa: E402
from hrm_coder import app  # noqa: E402


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

    # Fetch single run
    fetched = client.get(f"/runs/{run['id']}").json()
    assert fetched["id"] == run["id"]

    # Update status
    updated = client.patch(
        f"/runs/{run['id']}", json={"status": "done"}
    ).json()
    assert updated["status"] == "done"

    # Append a log line
    client.post(f"/runs/{run['id']}/logs", json={"message": "finished"})
    logs = client.get(f"/runs/{run['id']}").json()["logs"]
    assert "finished" in logs

    # Delete run
    art_dir = (
        Path(__file__).resolve().parents[1] / "artifacts" / f"run_{run['id']}"
    )
    assert art_dir.exists()
    deleted = client.delete(f"/runs/{run['id']}").json()
    assert deleted["id"] == run["id"]
    assert not art_dir.exists()
    assert client.get("/runs").json() == []
