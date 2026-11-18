"""Fakes dos serviços AWS: os testes rodam sem acessar a AWS (e sem custo)."""
import io

import pytest
from botocore.exceptions import ClientError

from chalicelib import clientes


class FakeS3:
    def __init__(self):
        self.objetos = {}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objetos[Key] = {'corpo': Body, 'tipo': ContentType}

    def get_object(self, Bucket, Key):
        if Key not in self.objetos:
            raise ClientError({'Error': {'Code': 'NoSuchKey', 'Message': 'x'}}, 'GetObject')
        return {'Body': io.BytesIO(self.objetos[Key]['corpo'])}

    def list_objects_v2(self, Bucket, Prefix, MaxKeys):
        n = sum(1 for k in self.objetos if k.startswith(Prefix))
        return {'KeyCount': min(n, MaxKeys)}

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
    """Traduz por dicionário; o idioma de origem 'auto' vem de ``idioma_detectado``."""

    def __init__(self):
        self.dicionario = {}
        self.idioma_detectado = 'de'
        self.chamadas = []

    def translate_text(self, Text, SourceLanguageCode, TargetLanguageCode):
        self.chamadas.append((Text, SourceLanguageCode))
        origem = self.idioma_detectado if SourceLanguageCode == 'auto' else SourceLanguageCode
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
