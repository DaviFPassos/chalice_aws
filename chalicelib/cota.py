"""Cota de uso: limita quantas imagens podem ser enviadas por dia e por mês.

Objetivo: manter o gasto dentro dos créditos gratuitos da AWS e do teste gratuito do
Amazon Translate, mesmo que a API pública seja usada por terceiros. Os limites e o
cálculo que os justifica estão em ``docs/custos.md``.

O contador fica em um objeto JSON no próprio bucket (``controle/uso-AAAA-MM.json``).
A atualização usa *escrita condicional* do S3 (``IfMatch``/``IfNoneMatch``): se duas
Lambdas tentarem atualizar ao mesmo tempo, uma delas recebe conflito e tenta de novo,
então o limite nunca é ultrapassado.
"""
import json
from datetime import datetime, timezone

from botocore.exceptions import ClientError

from chalicelib import clientes, config

TENTATIVAS = 5
_CONFLITOS = ('PreconditionFailed', 'ConditionalRequestConflict', '409', '412')


class CotaExcedida(Exception):
    """O limite diário ou mensal de envios foi atingido."""


def _chave_mes(agora):
    return f"{config.PREFIXO_CONTROLE}uso-{agora:%Y-%m}.json"


def _ler(chave):
    s3 = clientes.obter('s3')
    try:
        resposta = s3.get_object(Bucket=config.BUCKET_NAME, Key=chave)
    except ClientError as erro:
        if erro.response['Error']['Code'] in ('NoSuchKey', '404'):
            return {'total': 0, 'dias': {}}, None
        raise
    return json.loads(resposta['Body'].read()), resposta['ETag']


def reservar(agora=None):
    """Reserva uma vaga de envio. Lança ``CotaExcedida`` se algum limite foi atingido.

    Retorna o uso após a reserva: ``{'dia': n, 'mes': n}``.
    """
    agora = agora or datetime.now(timezone.utc)
    chave = _chave_mes(agora)
    dia = f'{agora:%Y-%m-%d}'
    s3 = clientes.obter('s3')

    for _ in range(TENTATIVAS):
        uso, etag = _ler(chave)
        usados_dia = uso['dias'].get(dia, 0)
        if usados_dia >= config.LIMITE_ENVIOS_DIA:
            raise CotaExcedida(
                f'Limite diário de {config.LIMITE_ENVIOS_DIA} imagens atingido. '
                'Tente novamente amanhã.')
        if uso['total'] >= config.LIMITE_ENVIOS_MES:
            raise CotaExcedida(
                f'Limite mensal de {config.LIMITE_ENVIOS_MES} imagens atingido.')

        uso['dias'][dia] = usados_dia + 1
        uso['total'] += 1
        condicao = {'IfMatch': etag} if etag else {'IfNoneMatch': '*'}
        try:
            s3.put_object(
                Bucket=config.BUCKET_NAME, Key=chave,
                Body=json.dumps(uso).encode('utf-8'),
                ContentType='application/json', **condicao,
            )
        except ClientError as erro:
            if erro.response['Error']['Code'] in _CONFLITOS:
                continue  # outra Lambda atualizou o contador: lê de novo e tenta outra vez
            raise
        return {'dia': uso['dias'][dia], 'mes': uso['total']}

    raise CotaExcedida('Muitos envios simultâneos. Tente novamente em instantes.')
