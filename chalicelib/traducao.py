"""Amazon Translate: tradução para português (idioma de origem informado)."""
import re

from chalicelib import clientes, config, rotulos

_FIM_DE_FRASE = re.compile(r'[.!?:;]$')
_PRIMEIRA_LETRA = re.compile(r'[^\W\d_]', re.UNICODE)


def traduzir(texto, origem):
    """Traduz ``texto`` do idioma ``origem`` (ex.: 'de', 'ru', 'ar') para português.

    Retorna ``(texto_traduzido, codigo_idioma_origem)``. A origem é sempre explícita:
    o modo ``'auto'`` dependeria do Amazon Comprehend.
    """
    if not texto.strip() or not origem:
        return '', None
    resposta = clientes.obter('translate').translate_text(
        Text=texto,
        SourceLanguageCode=origem,
        TargetLanguageCode=config.IDIOMA_DESTINO,
    )
    return resposta['TranslatedText'], resposta['SourceLanguageCode']


def juntar_continuacoes(linhas):
    """Junta as linhas que continuam a mesma frase, para o Translate ter contexto.

    Uma linha é continuação da anterior quando a anterior não termina em pontuação e a
    linha começa com letra minúscula ("Государственный" / "исторический музей"). Linhas
    que começam com maiúscula são tratadas como frases independentes ("Rauchen verboten"
    / "Bitte nicht rauchen"). Árabe não tem maiúsculas, então cada linha fica separada.
    """
    resultado = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        primeira = _PRIMEIRA_LETRA.search(linha)
        continua = (
            resultado
            and not _FIM_DE_FRASE.search(resultado[-1])
            and primeira is not None
            and primeira.group().islower()
        )
        if continua:
            resultado[-1] += ' ' + linha
        else:
            resultado.append(linha)
    return resultado


def traduzir_rotulos(lista):
    """Traduz os rótulos do Rekognition (sempre em inglês) para português.

    Os rótulos comuns usam a tradução fixa de ``rotulos.py``; só os demais vão para o
    Translate, numa única chamada.
    """
    traduzidos = [rotulos.traducao_fixa(r) for r in lista]
    pendentes = [r for r, t in zip(lista, traduzidos) if t is None]
    if pendentes:
        texto, _ = traduzir('\n'.join(pendentes), origem='en')
        partes = [p.strip().lower() for p in texto.split('\n')]
        if len(partes) != len(pendentes):
            partes = list(pendentes)  # o Translate juntou linhas: mantém o original
        respostas = iter(partes)
        traduzidos = [t if t is not None else next(respostas) for t in traduzidos]
    return traduzidos
