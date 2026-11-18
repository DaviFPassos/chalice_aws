"""Clientes boto3 criados sob demanda (e reaproveitados entre invocações da Lambda).

Os testes substituem esses clientes por versões falsas com ``definir_cliente``.
"""
import boto3

from chalicelib import config

_REGIOES = {
    'translate': config.TRANSLATE_REGION,
    'polly': config.POLLY_REGION,
}

_clientes = {}


def obter(servico):
    if servico not in _clientes:
        regiao = _REGIOES.get(servico)
        if regiao:
            _clientes[servico] = boto3.client(servico, region_name=regiao)
        else:
            _clientes[servico] = boto3.client(servico)
    return _clientes[servico]


def definir_cliente(servico, cliente):
    _clientes[servico] = cliente


def limpar():
    _clientes.clear()
