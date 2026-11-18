"""Código de acesso: estranhos não conseguem enviar imagens nem consumir a cota."""
import pytest
from chalice.test import Client

from app import app
from chalicelib import acesso, config

JPEG = b'\xff\xd8\xff\xe0' + b'0' * 100
CODIGO = 'ABCD-EFGH-JKLM'


def envio(client, codigo=None):
    cabecalhos = {'Accept': 'application/json', 'Content-Type': 'image/jpeg'}
    if codigo is not None:
        cabecalhos['X-Codigo-Acesso'] = codigo
    return client.http.post('/imagens', body=JPEG, headers=cabecalhos)


@pytest.fixture
def client(aws):
    with Client(app) as c:
        yield c


@pytest.mark.parametrize('codigo', [None, '', 'ERRADO-0000-0000', 'ABCD-EFGH-JKL'])
def test_sem_codigo_ou_codigo_errado_recebe_401_sem_gravar_nem_gastar_cota(client, aws, codigo):
    r = envio(client, codigo)
    assert r.status_code == 401
    assert r.json_body['Message'] == 'Código de acesso inválido.'
    assert aws['s3'].objetos == {}   # nem imagem, nem contador de cota


def test_codigo_correto_libera_o_envio(client, aws):
    assert envio(client, CODIGO).status_code == 202


def test_codigo_ignora_maiusculas_e_espacos(client):
    assert envio(client, '  abcd-efgh-jklm ').status_code == 202
    assert envio(client, 'ABCD -EFGH- JKLM').status_code == 202


def test_consulta_tambem_exige_codigo(client):
    r = client.http.get('/imagens/' + 'f' * 32, headers={'Accept': 'application/json'})
    assert r.status_code == 401


def test_raiz_continua_aberta(client):
    r = client.http.get('/', headers={'Accept': 'application/json'})
    assert r.status_code == 200
    assert 'X-Codigo-Acesso' in r.json_body['autenticacao']


def test_sem_parametro_no_ssm_recusa_tudo(client, aws):
    aws['ssm'].valor = None
    r = envio(client, CODIGO)
    assert r.status_code == 503
    assert aws['s3'].objetos == {}


def test_parametro_vazio_tambem_recusa(client, aws):
    aws['ssm'].valor = '   '
    assert envio(client, '').status_code == 503


def test_codigo_fica_em_cache_e_e_relido_depois_de_expirar(aws):
    acesso.verificar(CODIGO, agora=0)
    acesso.verificar(CODIGO, agora=100)
    assert aws['ssm'].chamadas == 1
    aws['ssm'].valor = 'NOVO-CODIGO-0001'
    with pytest.raises(acesso.AcessoNegado):          # ainda no cache: o novo não vale
        acesso.verificar('NOVO-CODIGO-0001', agora=200)
    acesso.verificar('NOVO-CODIGO-0001', agora=config.CACHE_CODIGO_SEGUNDOS + 1)
    assert aws['ssm'].chamadas == 2


def test_cors_permite_o_cabecalho_do_codigo(client):
    r = envio(client, CODIGO)
    assert r.headers['Access-Control-Allow-Origin'] == 'https://davifpassos.github.io'
