"""Testes das rotas da API REST."""
import json

import pytest
from chalice.test import Client

from app import app

JPEG = b'\xff\xd8\xff\xe0' + b'0' * 100
PNG = b'\x89PNG\r\n\x1a\n' + b'0' * 100
JSON = {'Accept': 'application/json'}


@pytest.fixture
def client(aws):
    with Client(app) as c:
        yield c


def test_pagina_inicial(client):
    r = client.http.get('/')
    assert r.status_code == 200
    assert r.headers['Content-Type'].startswith('text/html')
    assert b'Leitor de Placas' in r.body


def test_envio_jpeg_salva_no_s3(client, aws):
    r = client.http.post('/imagens', body=JPEG, headers={**JSON, 'Content-Type': 'image/jpeg'})
    assert r.status_code == 202
    id_imagem = r.json_body['id']
    assert aws['s3'].objetos[f'uploads/{id_imagem}.jpg']['corpo'] == JPEG


def test_envio_png(client, aws):
    r = client.http.post('/imagens', body=PNG, headers={**JSON, 'Content-Type': 'image/png'})
    assert r.status_code == 202
    assert f"uploads/{r.json_body['id']}.png" in aws['s3'].objetos


@pytest.mark.parametrize('corpo, tipo', [
    (b'GIF89a...', 'image/png'),                         # assinatura não é JPEG/PNG
    (b'', 'image/jpeg'),                                 # vazio
])
def test_envio_invalido(client, aws, corpo, tipo):
    r = client.http.post('/imagens', body=corpo, headers={**JSON, 'Content-Type': tipo})
    assert r.status_code == 400
    assert not any(k.startswith('uploads/') for k in aws['s3'].objetos)


def test_envio_muito_grande(client):
    grande = JPEG + b'0' * (5 * 1024 * 1024)
    r = client.http.post('/imagens', body=grande, headers={**JSON, 'Content-Type': 'image/jpeg'})
    assert r.status_code == 400


def test_consulta_id_invalido(client):
    assert client.http.get('/imagens/nao-e-um-id', headers=JSON).status_code == 400


def test_consulta_inexistente(client):
    assert client.http.get('/imagens/' + 'f' * 32, headers=JSON).status_code == 404


def test_fluxo_completo(client, aws):
    aws['rekognition'].linhas = [('Brandenburger Tor', 99.0)]
    aws['translate'].dicionario = {'Brandenburger Tor': 'Portão de Brandemburgo'}

    id_imagem = client.http.post(
        '/imagens', body=JPEG, headers={**JSON, 'Content-Type': 'image/jpeg'},
    ).json_body['id']

    # Antes do evento: ainda processando
    r = client.http.get(f'/imagens/{id_imagem}', headers=JSON)
    assert r.status_code == 202
    assert r.json_body['status'] == 'processando'

    # O S3 dispara o evento (simulado aqui)
    evento = client.events.generate_s3_event(bucket='qualquer', key=f'uploads/{id_imagem}.jpg')
    client.lambda_.invoke('ao_enviar_imagem', evento)

    r = client.http.get(f'/imagens/{id_imagem}', headers=JSON)
    assert r.status_code == 200
    assert r.json_body['texto_traduzido'] == 'Portão de Brandemburgo'
    assert r.json_body['audios_url']['narracao_pt'].startswith('https://')
