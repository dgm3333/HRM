from fastapi.testclient import TestClient

from .. import app


def test_websocket_log_stream():
    client = TestClient(app)
    run = client.post('/train', json={'x': 'y'}).json()
    run_id = run['id']
    with client.websocket_connect(f'/logs/ws/{run_id}') as ws:
        first = ws.receive_text()
        assert 'training started' in first
        client.post(f'/runs/{run_id}/logs', json={'message': 'next line'})
        assert ws.receive_text() == 'next line'
