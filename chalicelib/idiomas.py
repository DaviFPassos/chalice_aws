"""Nomes dos idiomas em português e vozes do Amazon Polly para cada idioma.

O Rekognition DetectText lê: inglês, árabe, russo, alemão, francês, italiano,
português e espanhol. O foco do projeto é árabe, russo e alemão.
"""
import re

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


# Faixas Unicode dos alfabetos suportados pelo projeto
_ARABE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
_CIRILICO = re.compile(r'[\u0400-\u04FF\u0500-\u052F]')
_LATINO = re.compile(r'[A-Za-z\u00C0-\u024F]')


MINIMO_LETRAS_NAO_LATINAS = 3


def detectar_por_alfabeto(texto):
    """Detecta o idioma pelo alfabeto das letras do texto.

    Árabe -> 'ar', cirílico -> 'ru', latino -> 'de' (no escopo do projeto, texto latino
    é tratado como alemão). Retorna None se não houver letras.

    Alfabetos não latinos têm prioridade quando aparecem com pelo menos 3 letras: em
    placas bilíngues (ex.: árabe + inglês) o texto latino costuma ser só a tradução
    auxiliar.

    Substitui o ``SourceLanguageCode='auto'`` do Translate, que depende do Amazon
    Comprehend (indisponível no plano Free da AWS).
    """
    nao_latinos = {
        'ar': len(_ARABE.findall(texto)),
        'ru': len(_CIRILICO.findall(texto)),
    }
    idioma, total = max(nao_latinos.items(), key=lambda item: item[1])
    if total >= MINIMO_LETRAS_NAO_LATINAS:
        return idioma
    return 'de' if _LATINO.search(texto) else (idioma if total else None)


def nome(codigo):
    """Nome do idioma em português; códigos regionais (ex.: 'de-AT') usam a base."""
    if not codigo:
        return 'idioma desconhecido'
    return NOMES.get(codigo, NOMES.get(codigo.split('-')[0], codigo))


def voz(codigo):
    if not codigo:
        return None
    return VOZES.get(codigo) or VOZES.get(codigo.split('-')[0])
