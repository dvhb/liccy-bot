import os
import tempfile
import pytest
import json

import licenses


@pytest.fixture
def client():
    db_fd, licenses.app.config['DATABASE'] = tempfile.mkstemp()
    licenses.app.config['TESTING'] = True
    licenses.app.config['MANAGERS_EMAIL'] = 'test@manager'
    client = licenses.app.test_client()
    with licenses.app.app_context():
        pass

    yield client

    os.close(db_fd)
    os.unlink(licenses.app.config['DATABASE'])


# def test_api_licenses_check(client):
#     data = [{'License': 'MIT', 'Name': 'Click', 'Version': '7.0'},
#             {'License': 'GPL', 'Name': 'Tap', 'Version': '8.1'}]
#     headers = {'Content-Type': 'application/json'}
#     rv = client.post('/api/fastcheck/', headers=headers, data=json.dumps(data))
#     assert rv.get_json() == dict(License='GPL', Name='Tap', Version='8.1')

def test_api_licenses_check_true(client):
    data = [{'License': 'CC0-1.0', 'Name': 'Click', 'Version': '7.0'}]
    headers = {'Content-Type': 'application/json'}
    rv = client.post('/api/fastcheck/', headers=headers, data=json.dumps(data))
    assert rv.get_json() == {}
