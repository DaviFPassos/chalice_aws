"""Reconstrói as linhas de texto a partir das posições das palavras do Rekognition.

Problema observado nos testes reais com placas em árabe:

- o Rekognition devolve as palavras árabes como "linhas" separadas, ordenadas da
  esquerda para a direita — mas o árabe se lê da direita para a esquerda;
- letras árabes que não se ligam à seguinte (ا د ذ ر ز و ة ...) criam um vão dentro da
  palavra, e o Rekognition corta a palavra ali: "الطوارئ" vira "الطوا" + "رئ" e
  "التدخين" vira "التد" + "خين".

A solução usa a geometria (BoundingBox) das palavras:

1. agrupa as palavras em fileiras pela posição vertical;
2. ordena cada fileira da direita para a esquerda se ela for árabe, senão da esquerda
   para a direita;
3. em fileiras árabes, junta sem espaço os pedaços que são a mesma palavra. A regra é
   linguística, porque só a distância não basta (há espaços reais com distância zero):
   se o pedaço anterior termina numa letra que NÃO se liga à próxima e o pedaço seguinte
   não começa com o artigo "ال", é a mesma palavra; caso contrário, há um espaço.
"""
import re

# Letras árabes que não se ligam à letra seguinte (só à anterior)
NAO_LIGANTES = set('اأإآٱدذرزوؤةء')
_ARABE = re.compile(r'[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]')
_LETRA = re.compile(r'[^\W\d_]', re.UNICODE)
# Vão máximo (em proporção da altura da letra) para dois pedaços serem a mesma palavra
VAO_MAXIMO_MESMA_PALAVRA = 0.5


def _caixa(deteccao, largura_img, altura_img):
    caixa = deteccao['Geometry']['BoundingBox']
    esquerda = caixa['Left'] * largura_img
    topo = caixa['Top'] * altura_img
    return {
        'texto': deteccao['DetectedText'],
        'confianca': deteccao.get('Confidence', 0),
        'esquerda': esquerda,
        'direita': esquerda + caixa['Width'] * largura_img,
        'topo': topo,
        'base': topo + caixa['Height'] * altura_img,
        'altura': caixa['Height'] * altura_img,
        'centro_y': topo + caixa['Height'] * altura_img / 2,
    }


def _agrupar_em_fileiras(palavras):
    """Agrupa palavras cuja linha central cai dentro da altura da primeira palavra da fileira."""
    fileiras = []
    for palavra in sorted(palavras, key=lambda p: p['topo']):
        for fileira in fileiras:
            referencia = fileira[0]
            if referencia['topo'] <= palavra['centro_y'] <= referencia['base']:
                fileira.append(palavra)
                break
        else:
            fileiras.append([palavra])
    return sorted(fileiras, key=lambda f: min(p['topo'] for p in f))


def _eh_arabe(textos):
    letras = ''.join(textos)
    arabes = len(_ARABE.findall(letras))
    return arabes > 0 and arabes >= len(_LETRA.findall(letras)) / 2


def _mesma_palavra_arabe(anterior, seguinte):
    """``anterior`` está à direita de ``seguinte`` (ordem de leitura árabe)."""
    if not anterior['texto'] or anterior['texto'][-1] not in NAO_LIGANTES:
        return False
    if seguinte['texto'].startswith('ال'):
        return False
    vao = anterior['esquerda'] - seguinte['direita']
    altura = max(anterior['altura'], seguinte['altura'])
    return vao < VAO_MAXIMO_MESMA_PALAVRA * altura


def _montar_fileira(fileira):
    arabe = _eh_arabe([p['texto'] for p in fileira])
    ordenadas = sorted(fileira, key=lambda p: -p['direita'] if arabe else p['esquerda'])
    texto = ordenadas[0]['texto']
    for anterior, seguinte in zip(ordenadas, ordenadas[1:]):
        separador = '' if arabe and _mesma_palavra_arabe(anterior, seguinte) else ' '
        texto += separador + seguinte['texto']
    confianca = min(p['confianca'] for p in ordenadas)
    return {'texto': texto, 'confianca': round(confianca, 1)}


def reconstruir_linhas(deteccoes, confianca_minima, largura_img=1000, altura_img=1000):
    """Monta as linhas de texto na ordem de leitura.

    - Árabe: reconstruído palavra a palavra pela geometria (ordem da direita para a
      esquerda e junção dos pedaços da mesma palavra).
    - Latino e cirílico: usa as LINE do próprio Rekognition, que já vêm certas e lidam
      bem com texto inclinado (agrupar por fileira misturava linhas de fotos tortas).
    - As linhas de todos os alfabetos são ordenadas de cima para baixo.
    - Linhas sem nenhuma letra (ex.: "!" de um ícone) são descartadas.

    Retorna None se as detecções não trouxerem geometria; o chamador então usa as LINE
    do Rekognition como estão.

    O Rekognition dá posições normalizadas (0 a 1) e não informa o tamanho da imagem;
    o padrão 1000x1000 distorce um pouco a comparação entre o vão (horizontal) e a altura
    da letra (vertical) em imagens não quadradas, mas a regra principal é a das letras
    não ligantes e o limite do vão é folgado.
    """
    confiaveis = [d for d in deteccoes if d.get('Confidence', 0) >= confianca_minima]
    palavras_arabes = [d for d in confiaveis
                       if d.get('Type') == 'WORD' and _eh_arabe([d['DetectedText']])]
    linhas_outras = [d for d in confiaveis
                     if d.get('Type') == 'LINE' and not _eh_arabe([d['DetectedText']])]
    usadas = palavras_arabes + linhas_outras
    if not usadas or not all('Geometry' in d for d in usadas):
        return None

    resultado = []  # (topo, linha)
    caixas_arabes = [_caixa(d, largura_img, altura_img) for d in palavras_arabes]
    for fileira in _agrupar_em_fileiras(caixas_arabes):
        resultado.append((min(p['topo'] for p in fileira), _montar_fileira(fileira)))
    for d in linhas_outras:
        caixa = _caixa(d, largura_img, altura_img)
        resultado.append((caixa['topo'], {'texto': caixa['texto'],
                                          'confianca': round(caixa['confianca'], 1)}))
    linhas = [linha for _, linha in sorted(resultado, key=lambda item: item[0])]
    return [linha for linha in linhas if _LETRA.search(linha['texto'])]
