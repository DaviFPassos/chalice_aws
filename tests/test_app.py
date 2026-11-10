import gzip
import json

import pytest
from chalice.test import Client

import app as app_module
from app import app

# app.api.binary_types inclui 'application/json' (passo 8 - gzip), então o
# gateway local do Chalice exige um Accept compatível nas requisições.
JSON = {'Accept': 'application/json'}


@pytest.fixture
def client():
    app_module.OBJECTS.clear()
    with Client(app) as c:
        yield c


def test_index(client):
    r = client.http.get('/', headers=JSON)
    assert r.status_code == 200
    assert r.json_body == {'hello': 'world'}


@pytest.mark.parametrize('city, state', [('seattle', 'WA'), ('portland', 'OR')])
def test_cidade_valida(client, city, state):
    r = client.http.get(f'/cities/{city}', headers=JSON)
    assert r.status_code == 200
    assert r.json_body == {'state': state}


def test_cidade_invalida(client):
    r = client.http.get('/cities/vancouver', headers=JSON)
    assert r.status_code == 400
    assert r.json_body['Code'] == 'BadRequestError'


def test_put_resource(client):
    r = client.http.put('/resource/foo', headers=JSON)
    assert r.json_body == {'value': 'foo'}


def test_objects_put_get(client):
    assert client.http.get('/objects/k', headers=JSON).status_code == 404
    client.http.put('/objects/k', body=json.dumps({'a': 1}),
                    headers={**JSON, 'Content-Type': 'application/json'})
    r = client.http.get('/objects/k', headers=JSON)
    assert r.status_code == 200
    assert r.json_body == {'k': {'a': 1}}


def test_introspect(client):
    r = client.http.get('/introspect?q=1', headers={**JSON, 'X-TestHeader': 'Foo'})
    assert r.json_body['query_params'] == {'q': '1'}
    assert r.json_body['headers']['x-testheader'] == 'Foo'


def test_form(client):
    r = client.http.post('/', body='states=WA&states=CA',
                         headers={**JSON, 'Content-Type': 'application/x-www-form-urlencoded'})
    assert r.json_body == {'states': ['WA', 'CA']}


def test_form_rejeita_json(client):
    r = client.http.post('/', body='{}',
                         headers={**JSON, 'Content-Type': 'application/json'})
    assert r.status_code == 415


def test_custom_response(client):
    r = client.http.get('/custom-response', headers={'Accept': 'text/plain'})
    assert r.body == b'hello world!'
    assert r.headers['Content-Type'] == 'text/plain'


def test_gzip(client):
    r = client.http.get('/gzip', headers=JSON)
    assert r.headers['Content-Encoding'] == 'gzip'
    assert json.loads(gzip.decompress(r.body)) == {'hello': 'world'}


def test_cors_multiple_origins(client):
    r = client.http.request('OPTIONS', '/cors_multiple_origins',
                            headers={**JSON, 'Origin': 'http://allowed1.example.com'})
    assert r.headers['Access-Control-Allow-Origin'] == 'http://allowed1.example.com'
