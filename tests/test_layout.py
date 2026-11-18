"""Reconstrução das linhas a partir das posições das palavras.

Os casos usam as posições reais devolvidas pelo Rekognition (DetectText) para as imagens
de exemplo em testes/imagens/ (1200x520 px), capturadas no teste na AWS.
"""
from chalicelib.layout import reconstruir_linhas

L, A = 1200, 520


def palavra(texto, x0, x1, y0, y1, conf=99.0, tipo='WORD'):
    return {
        'Type': tipo, 'DetectedText': texto, 'Confidence': conf,
        'Geometry': {'BoundingBox': {'Left': x0 / L, 'Top': y0 / A,
                                     'Width': (x1 - x0) / L, 'Height': (y1 - y0) / A}},
    }


def linha(texto, x0, x1, y0, y1, conf=99.0):
    return palavra(texto, x0, x1, y0, y1, conf, tipo='LINE')


def textos(deteccoes):
    return [linha['texto'] for linha in reconstruir_linhas(deteccoes, 80, L, A)]


def test_arabe_saida_emergencia_junta_pedacos_e_inverte_ordem():
    # Rekognition: "رئ" | "الطوا" | "مخرج" (esquerda -> direita)
    deteccoes = [
        palavra('رئ', 124, 334, 196, 335, 94.1),
        palavra('الطوا', 305, 695, 160, 351, 83.6),
        palavra('مخرج', 708, 1078, 202, 344, 97.4),
    ]
    assert textos(deteccoes) == ['مخرج الطوارئ']


def test_arabe_proibido_fumar_junta_palavra_cortada():
    deteccoes = [
        palavra('ممنوع', 750, 1090, 218, 331),
        palavra('التد', 528, 713, 200, 297),
        palavra('خين', 304, 526, 222, 321),
    ]
    assert textos(deteccoes) == ['ممنوع التدخين']


def test_arabe_espaco_real_com_caixas_encostadas():
    # "شارع" termina em letra que liga: a quebra é fim de palavra, mesmo com vão zero
    deteccoes = [
        palavra('التحرير', 210, 648, 136, 310, 94.7),
        palavra('شارع', 648, 972, 132, 300, 95.4),
        linha('Tahrir Street', 369, 829, 299, 354),
        palavra('Tahrir', 369, 582, 299, 353),
        palavra('Street', 605, 829, 301, 354),
    ]
    assert textos(deteccoes) == ['شارع التحرير', 'Tahrir Street']


def test_arabe_artigo_al_comeca_palavra_nova():
    deteccoes = [
        palavra('المتحف', 618, 1118, 168, 318),
        palavra('المصري', 68, 619, 159, 364),
    ]
    assert textos(deteccoes) == ['المتحف المصري']


def test_cirilico_e_latino_usam_as_linhas_do_rekognition_de_cima_para_baixo():
    deteccoes = [
        linha('Скользкий пол', 347, 1033, 278, 357, 96.0),
        linha('Выход в город', 300, 800, 100, 160),
        palavra('Скользкий', 347, 843, 278, 357, 98.4),
        palavra('пол', 875, 1033, 302, 349, 93.6),
    ]
    assert textos(deteccoes) == ['Выход в город', 'Скользкий пол']


def test_texto_latino_inclinado_nao_mistura_linhas():
    # Caso real (baixa_qualidade_alemao.jpg, girada 9°): agrupar palavras por fileira
    # produzia "Unter Tor" / "Brandenburger". As LINE do Rekognition ficam intactas.
    deteccoes = [
        linha('den Linden', 330, 560, 60, 120, 90.0),
        linha('Unter', 120, 300, 100, 160, 92.0),
        linha('Brandenburger Tor', 180, 560, 150, 230, 91.0),
        palavra('Unter', 120, 300, 100, 160, 92.0),
        palavra('Tor', 480, 560, 130, 180, 91.0),
        palavra('Brandenburger', 180, 470, 170, 230, 91.0),
    ]
    assert textos(deteccoes) == ['den Linden', 'Unter', 'Brandenburger Tor']


def test_descarta_baixa_confianca_e_linhas_sem_letras():
    deteccoes = [
        linha('OctopoXHO!', 320, 1060, 124, 283, 21.0),   # cirílico lido como latino
        linha('!', 166, 187, 231, 301, 98.5),              # "!" do ícone de atenção
        linha('Скользкий пол', 347, 1033, 278, 357, 96.0),
    ]
    assert textos(deteccoes) == ['Скользкий пол']


def test_sem_geometria_devolve_none():
    assert reconstruir_linhas([{'Type': 'LINE', 'DetectedText': 'x', 'Confidence': 99}], 80) is None
    assert reconstruir_linhas([], 80) is None


def test_confianca_da_linha_arabe_e_a_menor_das_palavras():
    deteccoes = [palavra('ممنوع', 750, 1090, 218, 331, 97.8), palavra('التد', 528, 713, 200, 297, 85.0),
                 palavra('خين', 304, 526, 222, 321, 98.8)]
    assert reconstruir_linhas(deteccoes, 80, L, A) == [{'texto': 'ممنوع التدخين', 'confianca': 85.0}]
