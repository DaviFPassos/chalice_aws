"""Leitor de Placas com Voz — Trabalho IV.

Fluxo orientado a eventos:
  1. POST /imagens salva a foto no S3 (prefixo uploads/).
  2. O upload dispara a Lambda ``ao_enviar_imagem`` (evento s3:ObjectCreated).
  3. A Lambda encadeia Rekognition -> Translate -> Polly e grava o resultado no S3.
  4. GET /imagens/{id} devolve o resultado com links temporários para os áudios.
"""
import logging
import re
import uuid

from chalice import (BadRequestError, Chalice, NotFoundError, Response,
                     TooManyRequestsError)

from chalicelib import armazenamento, config, cota, pagina, pipeline

app = Chalice(app_name='leitor-placas')
app.log.setLevel(logging.INFO)

ID_VALIDO = re.compile(r'^[0-9a-f]{32}$')
ASSINATURAS = {
    b'\xff\xd8\xff': 'jpg',
    b'\x89PNG\r\n\x1a\n': 'png',
}


def _detectar_formato(dados):
    for assinatura, extensao in ASSINATURAS.items():
        if dados.startswith(assinatura):
            return extensao
    return None


def _ler_imagem_da_requisicao(requisicao):
    # Só tipos binários: o Chalice não aceita misturar tipos binários e texto na mesma rota.
    dados = requisicao.raw_body or b''

    if not dados:
        raise BadRequestError('Envie uma imagem JPEG ou PNG.')
    if len(dados) > config.TAMANHO_MAXIMO_BYTES:
        raise BadRequestError('A imagem deve ter no máximo 5 MB.')
    extensao = _detectar_formato(dados)
    if extensao is None:
        raise BadRequestError('Formato não suportado: envie JPEG ou PNG.')
    return dados, extensao


@app.route('/', methods=['GET'])
def index():
    return Response(body=pagina.HTML, status_code=200,
                    headers={'Content-Type': 'text/html; charset=utf-8'})


@app.route('/imagens', methods=['POST'],
           content_types=['image/jpeg', 'image/png'])
def enviar_imagem():
    dados, extensao = _ler_imagem_da_requisicao(app.current_request)
    try:
        cota.reservar()
    except cota.CotaExcedida as erro:
        raise TooManyRequestsError(str(erro))
    id_imagem = uuid.uuid4().hex
    chave = armazenamento.chave_upload(id_imagem, extensao)
    tipo = 'image/png' if extensao == 'png' else 'image/jpeg'
    armazenamento.salvar(chave, dados, tipo)
    return Response(
        body={'id': id_imagem, 'status': 'processando',
              'resultado': f'/imagens/{id_imagem}'},
        status_code=202,
    )


@app.route('/imagens/{id_imagem}', methods=['GET'])
def consultar_imagem(id_imagem):
    if not ID_VALIDO.match(id_imagem):
        raise BadRequestError('Identificador inválido.')

    resultado = armazenamento.ler_resultado(id_imagem)
    if resultado is None:
        if not armazenamento.upload_existe(id_imagem):
            raise NotFoundError(f'Imagem {id_imagem} não encontrada.')
        return Response(body={'id': id_imagem, 'status': 'processando'},
                        status_code=202)

    resultado['audios_url'] = {
        nome: armazenamento.url_temporaria(chave)
        for nome, chave in resultado.get('audios', {}).items()
    }
    return resultado


@app.on_s3_event(bucket=config.BUCKET_NAME,
                 events=['s3:ObjectCreated:*'],
                 prefix=config.PREFIXO_UPLOADS)
def ao_enviar_imagem(event):
    app.log.info('Nova imagem: s3://%s/%s', event.bucket, event.key)
    try:
        resultado = pipeline.processar_imagem(event.key)
        app.log.info('Concluído %s: idioma=%s, linhas=%d',
                     resultado['id'], resultado['idioma_detectado'],
                     len(resultado['linhas']))
    except Exception as erro:  # noqa: BLE001 - registra qualquer falha para o cliente
        app.log.exception('Falha ao processar %s', event.key)
        # Não relança: evita que a Lambda assíncrona repita a cobrança dos serviços.
        pipeline.registrar_erro(event.key, erro)
