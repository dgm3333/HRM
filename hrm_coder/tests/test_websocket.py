from pathlib import Path
from fastapi.testclient import TestClient

from .. import app
from ..run_registry import registry


def test_artifact_static_server(tmp_path):
    client = TestClient(app)
    artifact_dir = Path('hrm_coder/artifacts')
    (artifact_dir / 'sample.txt').write_text('hello')
    resp = client.get('/artifacts/sample.txt')
    assert resp.status_code == 200
    assert resp.text == 'hello'


def test_websocket_log_stream():
    client = TestClient(app)
    run = client.post('/train', json={'x': 'y'}).json()
    run_id = run['id']
    with client.websocket_connect(f'/logs/ws/{run_id}') as ws:
        first = ws.receive_text()
        assert 'training started' in first
        registry.append_log(run_id, 'next line')
        assert ws.receive_text() == 'next line'
