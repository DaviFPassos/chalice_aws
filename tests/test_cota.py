"""Testes da cota de uso (limites diário e mensal de envios)."""
import json
from datetime import datetime, timezone

import pytest
from chalice.test import Client

from app import app
from chalicelib import config, cota

DIA_1 = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
DIA_2 = datetime(2026, 11, 18, 12, tzinfo=timezone.utc)
JPEG = b'\xff\xd8\xff\xe0' + b'0' * 100


@pytest.fixture
def limites(monkeypatch):
    monkeypatch.setattr(config, 'LIMITE_ENVIOS_DIA', 3)
    monkeypatch.setattr(config, 'LIMITE_ENVIOS_MES', 5)


def test_reserva_conta_dia_e_mes(aws, limites):
    assert cota.reservar(DIA_1) == {'dia': 1, 'mes': 1}
    assert cota.reservar(DIA_1) == {'dia': 2, 'mes': 2}
    salvo = json.loads(aws['s3'].objetos['controle/uso-2026-11.json']['corpo'])
    assert salvo == {'total': 2, 'dias': {'2026-11-17': 2}}


def test_limite_diario(aws, limites):
    for _ in range(3):
        cota.reservar(DIA_1)
    with pytest.raises(cota.CotaExcedida, match='diário'):
        cota.reservar(DIA_1)
    # No dia seguinte volta a aceitar
    assert cota.reservar(DIA_2) == {'dia': 1, 'mes': 4}


def test_limite_mensal(aws, limites):
    for _ in range(3):
        cota.reservar(DIA_1)
    for _ in range(2):
        cota.reservar(DIA_2)
    with pytest.raises(cota.CotaExcedida, match='mensal'):
        cota.reservar(DIA_2)


def test_conflito_de_escrita_tenta_de_novo(aws, limites):
    cota.reservar(DIA_1)
    aws['s3'].conflitos_simulados = 2   # duas Lambdas "ganharam" antes
    assert cota.reservar(DIA_1) == {'dia': 2, 'mes': 2}


def test_conflitos_demais_recusam_o_envio(aws, limites):
    aws['s3'].conflitos_simulados = cota.TENTATIVAS
    with pytest.raises(cota.CotaExcedida, match='simultâneos'):
        cota.reservar(DIA_1)


def test_api_responde_429_ao_atingir_o_limite(aws, limites):
    cabecalhos = {'Accept': 'application/json', 'Content-Type': 'image/jpeg'}
    with Client(app) as client:
        respostas = [client.http.post('/imagens', body=JPEG, headers=cabecalhos).status_code
                     for _ in range(4)]
    assert respostas == [202, 202, 202, 429]
    uploads = [k for k in aws['s3'].objetos if k.startswith('uploads/')]
    assert len(uploads) == 3   # a imagem recusada não é gravada (não gera processamento)


def test_texto_longo_e_cortado_antes_do_polly(aws):
    from chalicelib import voz
    voz.sintetizar('a' * 5000, 'pt')
    assert len(aws['polly'].chamadas[0]['Text']) == config.MAX_CARACTERES_NARRACAO
