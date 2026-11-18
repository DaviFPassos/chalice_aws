"""Amazon Translate: detecção automática do idioma e tradução para português."""
from chalicelib import clientes, config


def traduzir(texto, origem='auto'):
    """Traduz ``texto`` para português.

    Retorna ``(texto_traduzido, codigo_idioma_origem)``. Com ``origem='auto'`` o
    Translate detecta o idioma (internamente usa o Amazon Comprehend).
    """
    if not texto.strip():
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
