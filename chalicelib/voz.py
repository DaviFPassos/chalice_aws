"""Amazon Polly: narração em português e pronúncia do texto original."""
from chalicelib import clientes, config, idiomas

SAMPLE_RATE = '22050'


def sintetizar(texto, idioma):
    """Gera um MP3 com a voz configurada para ``idioma``. Retorna bytes ou None."""
    voz = idiomas.voz(idioma)
    if not texto.strip() or voz is None:
        return None
    voice_id, engine, language_code = voz
    texto = texto[:config.MAX_CARACTERES_NARRACAO]  # limite de custo do Polly
    resposta = clientes.obter('polly').synthesize_speech(
        Text=texto,
        OutputFormat='mp3',
        SampleRate=SAMPLE_RATE,
        VoiceId=voice_id,
        Engine=engine,
        LanguageCode=language_code,
    )
    return resposta['AudioStream'].read()


def montar_narracao(rotulos_pt, idioma_origem, texto_traduzido):
    """Monta o texto que será narrado em português."""
    partes = []
    if rotulos_pt:
        partes.append('Na imagem há: ' + ', '.join(rotulos_pt) + '.')
    else:
        partes.append('Não foi possível identificar elementos na imagem.')

    if texto_traduzido:
        partes.append(
            f'Foi encontrado um texto em {idiomas.nome(idioma_origem)}. '
            f'Em português, ele diz: {texto_traduzido}'
        )
    else:
        partes.append('Nenhum texto foi encontrado na imagem.')
    return ' '.join(partes)
