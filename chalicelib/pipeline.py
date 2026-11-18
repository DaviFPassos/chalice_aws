"""Encadeamento dos serviços de IA: Rekognition -> Translate -> Polly."""
from datetime import datetime, timezone

from chalicelib import armazenamento, config, idiomas, traducao, visao, voz


def processar_imagem(chave_imagem):
    """Processa uma imagem já salva no S3 e grava o resultado (JSON + MP3s) no bucket."""
    id_imagem = armazenamento.id_da_chave(chave_imagem)
    bucket = config.BUCKET_NAME

    # 1. Rekognition: texto e cena
    linhas = visao.extrair_texto(bucket, chave_imagem)
    rotulos = visao.identificar_cena(bucket, chave_imagem)
    texto_original = '\n'.join(linha['texto'] for linha in linhas)[:config.MAX_CARACTERES_TEXTO]

    # 2. Idioma pelo alfabeto + Translate: texto da placa e rótulos (inglês)
    idioma_origem = idiomas.detectar_por_alfabeto(texto_original)
    texto_para_traduzir = '\n'.join(traducao.juntar_continuacoes(texto_original.split('\n')))
    texto_traduzido, _ = traducao.traduzir(texto_para_traduzir, idioma_origem)
    rotulos_pt = traducao.traduzir_rotulos([r['rotulo'] for r in rotulos])

    # 3. Polly: narração em português + pronúncia do texto original
    narracao = voz.montar_narracao(rotulos_pt, idioma_origem, texto_traduzido)
    audios = {}
    mp3_narracao = voz.sintetizar(narracao, config.IDIOMA_DESTINO)
    if mp3_narracao:
        chave = armazenamento.chave_audio(id_imagem, 'narracao_pt')
        armazenamento.salvar(chave, mp3_narracao, 'audio/mpeg')
        audios['narracao_pt'] = chave
    mp3_original = voz.sintetizar(texto_original, idioma_origem)
    if mp3_original:
        chave = armazenamento.chave_audio(id_imagem, 'pronuncia_original')
        armazenamento.salvar(chave, mp3_original, 'audio/mpeg')
        audios['pronuncia_original'] = chave

    resultado = {
        'id': id_imagem,
        'status': 'concluido',
        'imagem': chave_imagem,
        'processado_em': datetime.now(timezone.utc).isoformat(),
        'idioma_detectado': idioma_origem,
        'texto_original': texto_original,
        'linhas': linhas,
        'texto_traduzido': texto_traduzido,
        'cena': [
            {'rotulo': r['rotulo'], 'rotulo_pt': pt, 'confianca': r['confianca']}
            for r, pt in zip(rotulos, rotulos_pt)
        ],
        'narracao': narracao,
        'audios': audios,
    }
    armazenamento.salvar_resultado(id_imagem, resultado)
    return resultado


MENSAGEM_ERRO = ('Não foi possível processar a imagem. Verifique se é uma foto JPEG ou '
                 'PNG válida e tente novamente.')


def registrar_erro(chave_imagem, erro):
    """Grava um resultado de erro para que o cliente não fique esperando para sempre.

    A mensagem é genérica de propósito: exceções da AWS podem conter o ID da conta e
    ARNs, e o resultado é público. Os detalhes ficam só no CloudWatch Logs.
    """
    id_imagem = armazenamento.id_da_chave(chave_imagem)
    armazenamento.salvar_resultado(id_imagem, {
        'id': id_imagem,
        'status': 'erro',
        'imagem': chave_imagem,
        'erro': MENSAGEM_ERRO,
        'tipo_erro': type(erro).__name__,
    })
