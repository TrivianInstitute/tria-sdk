"""Behavioral checks for the executable reference and its narrow HTTP boundary."""
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

PLAYGROUND = Path(__file__).resolve().parents[1] / 'playground'
sys.path.insert(0, str(PLAYGROUND))
from reference_experience import run_reference
from adapter import PlaygroundHandler, ThreadingHTTPServer, run_scenario


def test_reference_entries_restore_and_persist():
    result = run_reference()
    assert result['passed'] and all(result['checks'].values())
    assert [s['tria']['executor_calls'] for s in result['steps']] == [1, 0, 1, 0, 1]
    assert [s['cached_payload_baseline']['executor_calls'] for s in result['steps']] == [1]*5
    assert [s['tria']['suggestion'] for s in result['steps']] == ['10:30 AM', None, '10:30 AM', None, '10:30 AM']
    assert all(s['inspection']['unknowns'] for s in result['steps'])
    assert result['provenance']['sdk_version']
    assert len(result['provenance']['runner_sha256']) == 64
    assert len(result['provenance']['sdk_source_sha256']) == 64
    assert all(set(e) == {'position', 'type', 'actor', 'actor_sequence'} for e in result['events'])
    assert [s['event_count'] for s in result['steps']] == sorted(s['event_count'] for s in result['steps'])


@pytest.mark.parametrize('scenario', ['consent', 'action'])
@pytest.mark.parametrize('consent,permission', [(True, True), (True, False), (False, True), (False, False)])
def test_selected_state_matches_actual_sdk_entry(scenario, consent, permission):
    result = run_scenario({'scenario': scenario, 'state': {'consent': consent, 'permission': permission}})
    assert result['after']['executed'] == (consent and permission)
    assert result['audit']['chain_valid']
    if scenario == 'action':
        assert result['executor_calls'] == 1 + int(consent and permission)


def test_fresh_reality_fixture_does_not_invent_a_dispute():
    clean = run_scenario({'scenario': 'reality', 'state': {'dispute': False}})
    contested = run_scenario({'scenario': 'reality', 'state': {'dispute': True}})
    assert clean['interpretation_status'] != 'CONTESTED'
    assert contested['interpretation_status'] == 'CONTESTED'
    assert len(contested['events']) > len(clean['events'])


@pytest.mark.parametrize('payload', [
    {'scenario': []}, {'scenario': 'action', 'revoke': {}},
    {'scenario': 'action', 'state': None},
    {'scenario': 'action', 'state': {'consent': 'false', 'permission': True}},
    {'scenario': 'action', 'state': {'consent': 1, 'permission': True}},
    {'scenario': 'consent', 'state': {'consent': True}},
    {'scenario': 'reality', 'state': {'dispute': False, 'actor': 'admin'}},
    {'scenario': 'consent', 'state': {'consent': True, 'permission': True}, 'revoke': 'consent'},
])
def test_state_boundary_rejects_malformed_values(payload):
    with pytest.raises(ValueError):
        run_scenario(payload)


def test_cli_preserves_previous_output_and_reports_success(tmp_path):
    destination = tmp_path/'results.json'
    command = [sys.executable, str(PLAYGROUND/'reference_experience.py'), '--output', str(destination)]
    assert subprocess.run(command, capture_output=True).returncode == 0
    original = destination.read_bytes()
    assert json.loads(original)['passed'] is True
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert destination.read_bytes() == original


@pytest.fixture
def local_server():
    server = ThreadingHTTPServer(('127.0.0.1', 0), PlaygroundHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield 'http://127.0.0.1:'+str(server.server_port)
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_http_routes_reference_and_input_boundary(local_server):
    for page in ['/', '/index.html', '/before-with-tria.html', '/evaluate.html', '/evidence.html']:
        with urlopen(local_server+page) as response:
            assert response.status == 200
            assert b'<html' in response.read()
    for path in ['/adapter.py', '/reference_experience.py', '/../README.md']:
        with pytest.raises(HTTPError) as error:
            urlopen(local_server+path)
        assert error.value.code == 404
    request = Request(local_server+'/api/reference', data=b'{}', headers={'Content-Type':'application/json'})
    with urlopen(request) as response:
        assert json.load(response)['passed']
    request = Request(local_server+'/api/reference', data=b'{"actor":"admin"}', headers={'Content-Type':'application/json'})
    with pytest.raises(HTTPError) as error:
        urlopen(request)
    assert error.value.code == 400
