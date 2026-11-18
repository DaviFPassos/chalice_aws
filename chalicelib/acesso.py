"""Código de acesso: só quem conhece o código (equipe e professor) usa a API.

O site e a API são públicos, e cada imagem consome créditos da AWS. Para que estranhos
não gastem a cota, POST /imagens e GET /imagens/{id} exigem o cabeçalho
``X-Codigo-Acesso``.

O código fica no AWS SSM Parameter Store como SecureString (criptografado), nunca no
repositório. Para definir ou trocar: ``./scripts/definir_codigo_acesso.sh``.

- A comparação é feita em tempo constante (``hmac.compare_digest``), ignorando
  maiúsculas, minúsculas e espaços.
- O código lido do SSM fica em cache na Lambda por alguns minutos, para não consultar o
  SSM a cada requisição; uma troca de código vale em até ``CACHE_CODIGO_SEGUNDOS``.
- Se o parâmetro não existir, a API recusa tudo (falha fechada) em vez de liberar.
"""
import hmac
import time

from botocore.exceptions import ClientError

from chalicelib import clientes, config


class AcessoNegado(Exception):
    """Código ausente ou incorreto."""


class AcessoNaoConfigurado(Exception):
    """O código de acesso não foi definido no SSM."""


_cache = {'valor': None, 'expira': 0.0}


def normalizar(codigo):
    return ''.join((codigo or '').split()).upper()


def _codigo_esperado(agora):
    if _cache['valor'] and agora < _cache['expira']:
        return _cache['valor']
    try:
        resposta = clientes.obter('ssm').get_parameter(
            Name=config.PARAMETRO_CODIGO_ACESSO, WithDecryption=True)
    except ClientError as erro:
        if erro.response['Error']['Code'] == 'ParameterNotFound':
            raise AcessoNaoConfigurado() from erro
        raise
    valor = normalizar(resposta['Parameter']['Value'])
    if not valor:
        raise AcessoNaoConfigurado()
    _cache.update(valor=valor, expira=agora + config.CACHE_CODIGO_SEGUNDOS)
    return valor


def verificar(codigo_recebido, agora=None):
    """Lança ``AcessoNegado`` se o código não confere."""
    esperado = _codigo_esperado(time.monotonic() if agora is None else agora)
    recebido = normalizar(codigo_recebido)
    if not recebido or not hmac.compare_digest(recebido.encode(), esperado.encode()):
        raise AcessoNegado()


def limpar_cache():
    _cache.update(valor=None, expira=0.0)
