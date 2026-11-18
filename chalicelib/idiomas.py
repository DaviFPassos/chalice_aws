"""Nomes dos idiomas em português e vozes do Amazon Polly para cada idioma.

O Rekognition DetectText lê: inglês, árabe, russo, alemão, francês, italiano,
português e espanhol. O foco do projeto é árabe, russo e alemão.
"""

NOMES = {
    'ar': 'árabe',
    'ru': 'russo',
    'de': 'alemão',
    'en': 'inglês',
    'es': 'espanhol',
    'fr': 'francês',
    'it': 'italiano',
    'pt': 'português',
}

# (VoiceId, Engine, LanguageCode)
VOZES = {
    'pt': ('Camila', 'neural', 'pt-BR'),
    'de': ('Vicki', 'neural', 'de-DE'),
    'ru': ('Tatyana', 'standard', 'ru-RU'),
    'ar': ('Zeina', 'standard', 'arb'),
    'en': ('Joanna', 'neural', 'en-US'),
    'es': ('Lucia', 'neural', 'es-ES'),
    'fr': ('Lea', 'neural', 'fr-FR'),
    'it': ('Bianca', 'neural', 'it-IT'),
}


def nome(codigo):
    """Nome do idioma em português; códigos regionais (ex.: 'de-AT') usam a base."""
    if not codigo:
        return 'idioma desconhecido'
    return NOMES.get(codigo, NOMES.get(codigo.split('-')[0], codigo))


def voz(codigo):
    if not codigo:
        return None
    return VOZES.get(codigo) or VOZES.get(codigo.split('-')[0])
