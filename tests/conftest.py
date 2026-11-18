"""Fakes dos serviços AWS: os testes rodam sem acessar a AWS (e sem custo)."""
import io

import pytest
from botocore.exceptions import ClientError

from chalicelib import clientes


class FakeS3:
    def __init__(self):
        self.objetos = {}

    versao = 0
    conflitos_simulados = 0   # quantas escritas condicionais devem falhar antes de aceitar

    def put_object(self, Bucket, Key, Body, ContentType, IfMatch=None, IfNoneMatch=None):
        atual = self.objetos.get(Key)
        condicional = IfMatch is not None or IfNoneMatch is not None
        if condicional and self.conflitos_simulados:
            self.conflitos_simulados -= 1
            raise ClientError({'Error': {'Code': 'PreconditionFailed', 'Message': 'x'}}, 'PutObject')
        if (IfNoneMatch == '*' and atual) or (IfMatch and (not atual or atual['etag'] != IfMatch)):
            raise ClientError({'Error': {'Code': 'PreconditionFailed', 'Message': 'x'}}, 'PutObject')
        FakeS3.versao += 1
        self.objetos[Key] = {'corpo': Body, 'tipo': ContentType, 'etag': f'"v{FakeS3.versao}"'}

    def get_object(self, Bucket, Key):
        if Key not in self.objetos:
            raise ClientError({'Error': {'Code': 'NoSuchKey', 'Message': 'x'}}, 'GetObject')
        obj = self.objetos[Key]
        return {'Body': io.BytesIO(obj['corpo']), 'ETag': obj['etag']}

    def head_object(self, Bucket, Key):
        if Key not in self.objetos:
            raise ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, 'HeadObject')
        return {'ETag': self.objetos[Key]['etag']}

    def generate_presigned_url(self, operacao, Params, ExpiresIn):
        return f"https://s3.exemplo/{Params['Key']}?expira={ExpiresIn}"


class FakeRekognition:
    def __init__(self):
        self.linhas = []        # [(texto, confianca)]
        self.rotulos = []       # [(nome, confianca)]
        self.erro = None

    def detect_text(self, Image):
        if self.erro:
            raise self.erro
        deteccoes = [{'Type': 'LINE', 'DetectedText': t, 'Confidence': c} for t, c in self.linhas]
        # Palavras soltas (Type WORD) devem ser ignoradas pelo código
        deteccoes += [{'Type': 'WORD', 'DetectedText': t, 'Confidence': c} for t, c in self.linhas]
        return {'TextDetections': deteccoes}

    def detect_labels(self, Image, MaxLabels, MinConfidence):
        return {'Labels': [{'Name': n, 'Confidence': c} for n, c in self.rotulos]}


class FakeTranslate:
    """Traduz por dicionário. Recusa o modo 'auto' (dependeria do Comprehend)."""

    def __init__(self):
        self.dicionario = {}
        self.chamadas = []

    def translate_text(self, Text, SourceLanguageCode, TargetLanguageCode):
        assert SourceLanguageCode != 'auto', "o projeto não usa SourceLanguageCode='auto'"
        self.chamadas.append((Text, SourceLanguageCode))
        origem = SourceLanguageCode
        traduzido = '\n'.join(self.dicionario.get(linha, linha) for linha in Text.split('\n'))
        return {'TranslatedText': traduzido, 'SourceLanguageCode': origem}


class FakePolly:
    def __init__(self):
        self.chamadas = []

    def synthesize_speech(self, **kwargs):
        self.chamadas.append(kwargs)
        return {'AudioStream': io.BytesIO(b'ID3-mp3-' + kwargs['VoiceId'].encode())}


@pytest.fixture
def aws():
    fakes = {
        's3': FakeS3(),
        'rekognition': FakeRekognition(),
        'translate': FakeTranslate(),
        'polly': FakePolly(),
    }
    for servico, fake in fakes.items():
        clientes.definir_cliente(servico, fake)
    yield fakes
    clientes.limpar()
