"""Amazon Rekognition: extração de texto e identificação da cena."""
import re

from chalicelib import clientes, config, layout

_LETRA = re.compile(r'[^\W\d_]', re.UNICODE)


def _imagem_s3(bucket, chave):
    return {'S3Object': {'Bucket': bucket, 'Name': chave}}


def extrair_texto(bucket, chave):
    """Retorna as linhas de texto na ordem de leitura.

    As linhas são reconstruídas pela posição das palavras (``layout.py``), o que corrige a
    ordem e as palavras cortadas do árabe. Sem geometria, usa as LINE do Rekognition.
    """
    resposta = clientes.obter('rekognition').detect_text(Image=_imagem_s3(bucket, chave))
    deteccoes = resposta.get('TextDetections', [])
    linhas = layout.reconstruir_linhas(deteccoes, config.CONFIANCA_MINIMA_TEXTO)
    if linhas is not None:
        return linhas
    return [
        {'texto': d['DetectedText'], 'confianca': round(d['Confidence'], 1)}
        for d in deteccoes
        if d.get('Type') == 'LINE'
        and d.get('Confidence', 0) >= config.CONFIANCA_MINIMA_TEXTO
        and _LETRA.search(d['DetectedText'])
    ]


def identificar_cena(bucket, chave):
    """Retorna os rótulos (em inglês) que descrevem a imagem, do mais ao menos provável."""
    resposta = clientes.obter('rekognition').detect_labels(
        Image=_imagem_s3(bucket, chave),
        MaxLabels=config.MAXIMO_ROTULOS,
        MinConfidence=config.CONFIANCA_MINIMA_ROTULOS,
    )
    return [
        {'rotulo': r['Name'], 'confianca': round(r['Confidence'], 1)}
        for r in resposta.get('Labels', [])
    ]
