import os
import tempfile
import pytest

import licenses


@pytest.fixture
def client():
    db_fd, licenses.app.config['DATABASE'] = tempfile.mkstemp()
    licenses.app.config['TESTING'] = True
    client = licenses.app.test_client()
    with licenses.app.app_context():
        pass

    yield client

    os.close(db_fd)
    os.unlink(licenses.app.config['DATABASE'])


# Simple test
def test_status(client):
    rv = client.get('/')
    assert b'ok' in rv.data


# /api/licesenses/wls test
def test_api_licenses_wls(client):
    rv = client.post('/api/licenses/wls',
                     headers={'X_SLACK_REQUEST_TIMESTAMP': '12345678'})
    assert b'Request is not validated' in rv.data


# /api/licesenses/bls test
def test_api_licenses_bls(client):
    rv = client.post('/api/licenses/bls',
                     headers={'X_SLACK_REQUEST_TIMESTAMP': '12345678'})
    assert b'Request is not validated' in rv.data


def test_api_licenses_interactive(client):
    rv = client.post('/api/licenses/interactive',
                     headers={'X_SLACK_REQUEST_TIMESTAMP': '12345678'})
    assert b'Failed' in rv.data

