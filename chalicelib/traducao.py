"""Amazon Translate: tradução para português (idioma de origem informado)."""
from chalicelib import clientes, config


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


def traduzir_rotulos(rotulos):
    """Traduz a lista de rótulos do Rekognition (sempre em inglês) em uma única chamada."""
    if not rotulos:
        return []
    texto = '\n'.join(rotulos)
    traduzido, _ = traduzir(texto, origem='en')
    partes = [p.strip() for p in traduzido.split('\n')]
    if len(partes) != len(rotulos):
        # Se o Translate juntar linhas, mantém o original para não desalinhar.
        return list(rotulos)
    return [p.lower() for p in partes]
