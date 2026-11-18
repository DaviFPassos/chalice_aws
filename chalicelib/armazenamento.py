"""Amazon S3: chaves dos objetos, upload, resultados e URLs dos áudios."""
import json

from botocore.exceptions import ClientError

from chalicelib import clientes, config


def chave_upload(id_imagem, extensao):
    return f'{config.PREFIXO_UPLOADS}{id_imagem}.{extensao}'


def chave_resultado(id_imagem):
    return f'{config.PREFIXO_RESULTADOS}{id_imagem}.json'


def chave_audio(id_imagem, nome):
    return f'{config.PREFIXO_AUDIOS}{id_imagem}/{nome}.mp3'


def id_da_chave(chave):
    """'uploads/abc123.jpg' -> 'abc123'"""
    nome = chave.rsplit('/', 1)[-1]
    return nome.rsplit('.', 1)[0]


def salvar(chave, corpo, tipo):
    clientes.obter('s3').put_object(
        Bucket=config.BUCKET_NAME, Key=chave, Body=corpo, ContentType=tipo,
    )


def salvar_resultado(id_imagem, resultado):
    corpo = json.dumps(resultado, ensure_ascii=False, indent=2).encode('utf-8')
    salvar(chave_resultado(id_imagem), corpo, 'application/json')


def ler_resultado(id_imagem):
    """Retorna o resultado salvo ou None se ainda não existir."""
    try:
        resposta = clientes.obter('s3').get_object(
            Bucket=config.BUCKET_NAME, Key=chave_resultado(id_imagem),
        )
    except ClientError as erro:
        if erro.response['Error']['Code'] in ('NoSuchKey', '404'):
            return None
        raise
    return json.loads(resposta['Body'].read())


def url_temporaria(chave):
    return clientes.obter('s3').generate_presigned_url(
        'get_object',
        Params={'Bucket': config.BUCKET_NAME, 'Key': chave},
        ExpiresIn=config.VALIDADE_URL_AUDIO,
    )
