"""Amazon Rekognition: extração de texto e identificação da cena."""
from chalicelib import clientes, config


def _imagem_s3(bucket, chave):
    return {'S3Object': {'Bucket': bucket, 'Name': chave}}


def extrair_texto(bucket, chave):
    """Retorna as linhas de texto detectadas (ordem de leitura do Rekognition)."""
    resposta = clientes.obter('rekognition').detect_text(Image=_imagem_s3(bucket, chave))
    linhas = [
        d for d in resposta.get('TextDetections', [])
        if d.get('Type') == 'LINE' and d.get('Confidence', 0) >= config.CONFIANCA_MINIMA_TEXTO
    ]
    return [
        {'texto': d['DetectedText'], 'confianca': round(d['Confidence'], 1)}
        for d in linhas
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
