"""Testes do encadeamento Rekognition -> Translate -> Polly (evento do S3)."""
import json

from chalice.test import Client

from app import app
from chalicelib import config, pipeline

CHAVE = 'uploads/' + 'a' * 32 + '.jpg'
ID = 'a' * 32


def _resultado(aws):
    return json.loads(aws['s3'].objetos[f'resultados/{ID}.json']['corpo'])


def test_placa_em_alemao(aws):
    aws['rekognition'].linhas = [('Brandenburger Tor', 99.1)]
    aws['rekognition'].rotulos = [('Monument', 95.0), ('Architecture', 90.0)]
    aws['translate'].idioma_detectado = 'de'
    aws['translate'].dicionario = {
        'Brandenburger Tor': 'Portão de Brandemburgo',
        'Monument': 'Monumento', 'Architecture': 'Arquitetura',
    }

    r = pipeline.processar_imagem(CHAVE)

    assert r['status'] == 'concluido'
    assert r['idioma_detectado'] == 'de'
    assert r['texto_original'] == 'Brandenburger Tor'
    assert r['texto_traduzido'] == 'Portão de Brandemburgo'
    assert [c['rotulo_pt'] for c in r['cena']] == ['monumento', 'arquitetura']
    assert 'alemão' in r['narracao'] and 'Portão de Brandemburgo' in r['narracao']
    # Dois áudios: narração (Camila, pt-BR) e pronúncia original (Vicki, de-DE)
    vozes = [c['VoiceId'] for c in aws['polly'].chamadas]
    assert vozes == ['Camila', 'Vicki']
    assert set(r['audios']) == {'narracao_pt', 'pronuncia_original'}
    assert f'audios/{ID}/narracao_pt.mp3' in aws['s3'].objetos
    assert _resultado(aws)['texto_traduzido'] == 'Portão de Brandemburgo'


def test_placa_em_russo_usa_voz_russa(aws):
    aws['rekognition'].linhas = [('Красная площадь', 97.0)]
    aws['translate'].idioma_detectado = 'ru'
    aws['translate'].dicionario = {'Красная площадь': 'Praça Vermelha'}

    r = pipeline.processar_imagem(CHAVE)

    assert r['texto_traduzido'] == 'Praça Vermelha'
    voz_original = aws['polly'].chamadas[1]
    assert (voz_original['VoiceId'], voz_original['Engine']) == ('Tatyana', 'standard')


def test_placa_em_arabe_varias_linhas(aws):
    aws['rekognition'].linhas = [('المتحف المصري', 96.0), ('مفتوح', 92.0)]
    aws['translate'].idioma_detectado = 'ar'
    aws['translate'].dicionario = {'المتحف المصري': 'Museu Egípcio', 'مفتوح': 'Aberto'}

    r = pipeline.processar_imagem(CHAVE)

    assert r['texto_traduzido'] == 'Museu Egípcio\nAberto'
    assert len(r['linhas']) == 2
    assert aws['polly'].chamadas[1]['LanguageCode'] == 'arb'


def test_texto_com_baixa_confianca_e_ignorado(aws):
    aws['rekognition'].linhas = [('ruído', 40.0)]
    r = pipeline.processar_imagem(CHAVE)
    assert r['texto_original'] == ''
    assert r['linhas'] == []


def test_imagem_sem_texto(aws):
    aws['rekognition'].rotulos = [('Church', 93.0)]
    aws['translate'].dicionario = {'Church': 'Igreja'}

    r = pipeline.processar_imagem(CHAVE)

    assert r['idioma_detectado'] is None
    assert r['texto_traduzido'] == ''
    assert 'Nenhum texto foi encontrado' in r['narracao']
    # Só a narração em português é gerada
    assert list(r['audios']) == ['narracao_pt']
    # O texto vazio não é enviado ao Translate com origem automática
    assert all(origem == 'en' for _, origem in aws['translate'].chamadas)


def test_evento_s3_dispara_processamento(aws):
    aws['rekognition'].linhas = [('Ausgang', 98.0)]
    aws['translate'].dicionario = {'Ausgang': 'Saída'}
    with Client(app) as client:
        evento = client.events.generate_s3_event(bucket=config.BUCKET_NAME, key=CHAVE)
        client.lambda_.invoke('ao_enviar_imagem', evento)
    assert _resultado(aws)['texto_traduzido'] == 'Saída'


def test_evento_s3_registra_erro(aws):
    aws['rekognition'].erro = RuntimeError('imagem corrompida')
    with Client(app) as client:
        evento = client.events.generate_s3_event(bucket=config.BUCKET_NAME, key=CHAVE)
        client.lambda_.invoke('ao_enviar_imagem', evento)
    resultado = _resultado(aws)
    assert resultado['status'] == 'erro'
    assert 'imagem corrompida' in resultado['erro']
