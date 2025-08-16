from pathlib import Path
from fastapi.testclient import TestClient
from itertools import count

from .. import app
from ..run_registry import registry


def _reset_registry():
    registry._runs.clear()
    registry._log_queues.clear()
    registry._id_counter = count(1)


def test_artifact_static_server(tmp_path):
    _reset_registry()
    client = TestClient(app)
    run = client.post('/train', json={}).json()
    run_id = run['id']
    artifact_path = Path('hrm_coder/artifacts') / f'run_{run_id}'
    (artifact_path / 'result.xml').write_text('<testsuite/>')
    resp = client.get(f"/artifacts/run_{run_id}/result.xml")
    assert resp.status_code == 200
    assert '<testsuite/>' in resp.text


def test_artifact_listing(tmp_path):
    _reset_registry()
    client = TestClient(app)
    run = client.post('/train', json={}).json()
    run_id = run['id']
    artifact_path = Path('hrm_coder/artifacts') / f'run_{run_id}'
    (artifact_path / 'junit.xml').write_text('<junit/>')
    (artifact_path / 'coverage').mkdir(exist_ok=True)
    (artifact_path / 'coverage' / 'index.html').write_text('cov')
    resp = client.get(f"/runs/{run_id}/artifacts")
    files = resp.json()['files']
    assert 'junit.xml' in files
    assert 'coverage/index.html' in files
    _reset_registry()
