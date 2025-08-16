from pathlib import Path
from fastapi.testclient import TestClient
from itertools import count

from .. import app
from ..run_registry import registry


def test_junit_summary_endpoint(tmp_path):
    registry._runs.clear()
    registry._log_queues.clear()
    registry._id_counter = count(1)

    client = TestClient(app)
    run = client.post('/train', json={}).json()
    run_id = run['id']
    artifact_dir = Path('hrm_coder/artifacts') / f'run_{run_id}'
    artifact_dir.mkdir(parents=True, exist_ok=True)
    junit = '<testsuite tests="3" failures="1" errors="1"></testsuite>'
    (artifact_dir / 'junit.xml').write_text(junit)
    resp = client.get(f'/runs/{run_id}/junit')
    assert resp.status_code == 200
    assert resp.json() == {'tests': 3, 'failures': 2}

    registry._runs.clear()
    registry._log_queues.clear()
    registry._id_counter = count(1)
