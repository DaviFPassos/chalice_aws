"""Testes da detecção de idioma pelo alfabeto."""
import pytest

from chalicelib.idiomas import detectar_por_alfabeto, nome, voz


@pytest.mark.parametrize('texto, esperado', [
    ('Brandenburger Tor', 'de'),
    ('Straße des 17. Juni', 'de'),
    ('Красная площадь', 'ru'),
    ('Выход', 'ru'),
    ('المتحف المصري', 'ar'),
    ('شارع التحرير', 'ar'),
    ('المتحف المصري\nEgyptian Museum', 'ar'),   # placa bilíngue: predomina o árabe
    ('Метро M', 'ru'),                          # letra latina isolada não muda o resultado
    ('U-Bahn Москва', 'ru'),                    # cirílico relevante tem prioridade
    ('Ausgang Ж', 'de'),                        # 1 letra cirílica solta não basta
    ('', None),
    ('123 - 456', None),                        # sem letras
])
def test_detectar_por_alfabeto(texto, esperado):
    assert detectar_por_alfabeto(texto) == esperado


def test_nome_e_voz():
    assert nome('ru') == 'russo'
    assert nome('de-AT') == 'alemão'
    assert nome(None) == 'idioma desconhecido'
    assert voz('ar') == ('Zeina', 'standard', 'arb')
    assert voz(None) is None
