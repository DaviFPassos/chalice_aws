#!/usr/bin/env python3
"""Gera imagens de exemplo de placas em alemão, russo e árabe em testes/imagens/.

As imagens são sintéticas e autorais (geradas por este script), então podem ficar no
repositório público sem questões de direitos de imagem. Cobrem os casos do roteiro de
testes: os três idiomas, placa bilíngue, imagem sem texto e foto de baixa qualidade.

Uso:
    pip install -r requirements-dev.txt
    python scripts/gerar_imagens_exemplo.py

Fonte: DejaVu Sans (pacote fonts-dejavu no Linux; no Windows/macOS, instale a fonte ou
passe o caminho com --fonte). O árabe é desenhado com o motor raqm do Pillow (ligação das
letras e escrita da direita para a esquerda); sem raqm, usa arabic-reshaper + python-bidi.
"""
import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'testes' / 'imagens'
FONTES_PADRAO = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
    '/Library/Fonts/DejaVuSans-Bold.ttf',
    'C:/Windows/Fonts/DejaVuSans-Bold.ttf',
]
TEM_RAQM = features.check('raqm')


def carregar_fonte(caminho, tamanho):
    if TEM_RAQM:
        return ImageFont.truetype(caminho, tamanho, layout_engine=ImageFont.Layout.RAQM)
    return ImageFont.truetype(caminho, tamanho)


def preparar_texto(texto, rtl):
    """Sem raqm, o árabe precisa ser ligado e invertido manualmente."""
    if not rtl or TEM_RAQM:
        return texto
    import arabic_reshaper
    try:
        from bidi import get_display
    except ImportError:
        from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(texto))


def opcoes_texto(rtl):
    return {'direction': 'rtl', 'language': 'ar'} if rtl and TEM_RAQM else {}


def texto_centralizado(desenho, esquerda, direita, y, texto, tamanho, cor, rtl=False):
    """Centraliza o texto entre ``esquerda`` e ``direita``, reduzindo a fonte se não couber."""
    texto = preparar_texto(texto, rtl)
    opcoes = opcoes_texto(rtl)
    while True:
        fonte = carregar_fonte(ARGS.fonte, tamanho)
        largura = desenho.textlength(texto, font=fonte, **opcoes)
        if largura <= direita - esquerda or tamanho <= 30:
            break
        tamanho -= 4
    centro = (esquerda + direita) / 2
    desenho.text((centro - largura / 2, y), texto, font=fonte, fill=cor, **opcoes)


def fundo_parede(largura, altura, cor, semente):
    """Fundo com textura leve, para não ser um fundo liso artificial."""
    aleatorio = random.Random(semente)
    img = Image.new('RGB', (largura, altura), cor)
    pixels = img.load()
    for _ in range(largura * altura // 6):
        x, y = aleatorio.randrange(largura), aleatorio.randrange(altura)
        delta = aleatorio.randint(-14, 14)
        r, g, b = pixels[x, y]
        pixels[x, y] = (max(0, min(255, r + delta)), max(0, min(255, g + delta)), max(0, min(255, b + delta)))
    return img.filter(ImageFilter.GaussianBlur(0.6))


def placa(nome, linhas, *, cor_placa, cor_texto='white', cor_fundo=(196, 192, 184),
          tamanho=(1200, 520), tamanhos_fonte=None, rtl=None, icone=None, icone_a_esquerda=False,
          borda='white', semente=1):
    """Desenha uma placa retangular com várias linhas de texto.

    ``rtl`` é uma lista de booleanos (uma por linha): True para linhas em árabe.
    """
    largura, altura = tamanho
    img = fundo_parede(largura, altura, cor_fundo, semente)
    d = ImageDraw.Draw(img)
    margem = 50
    # sombra + placa
    d.rounded_rectangle((margem + 10, margem + 14, largura - margem + 10, altura - margem + 14),
                        radius=28, fill=(90, 90, 90))
    d.rounded_rectangle((margem, margem, largura - margem, altura - margem),
                        radius=28, fill=cor_placa, outline=borda, width=10)
    if icone:
        icone(d, largura, altura)

    tamanhos_fonte = tamanhos_fonte or [86] * len(linhas)
    rtl = rtl or [False] * len(linhas)
    # Com ícone à esquerda, o texto ocupa só a área à direita dele
    esquerda = 280 if icone_a_esquerda else margem + 40
    direita = largura - margem - 40
    altura_total = sum(t * 1.35 for t in tamanhos_fonte)
    y = (altura - altura_total) / 2
    for linha, tam, eh_rtl in zip(linhas, tamanhos_fonte, rtl):
        texto_centralizado(d, esquerda, direita, y, linha, tam, cor_texto, rtl=eh_rtl)
        y += tam * 1.35
    salvar(img, nome)
    return img


def icone_metro(d, largura, altura):
    d.ellipse((90, 90, 190, 190), fill='white')
    fonte = carregar_fonte(ARGS.fonte, 70)
    d.text((112, 98), 'M', font=fonte, fill=(200, 30, 40))


def icone_proibido(d, largura, altura):
    x, y, r = 170, altura // 2, 80
    d.ellipse((x - r, y - r, x + r, y + r), outline=(220, 20, 30), width=18, fill='white')
    d.line((x - 56, y + 56, x + 56, y - 56), fill=(220, 20, 30), width=18)


def icone_saida(d, largura, altura):
    # seta indicando a direção da saída
    y = altura - 130
    d.polygon([(largura / 2 - 120, y), (largura / 2 + 60, y), (largura / 2 + 60, y - 30),
               (largura / 2 + 130, y + 15), (largura / 2 + 60, y + 60), (largura / 2 + 60, y + 30),
               (largura / 2 - 120, y + 30)], fill='white')


def icone_atencao(d, largura, altura):
    x, y = 170, altura // 2
    d.polygon([(x, y - 85), (x - 95, y + 75), (x + 95, y + 75)], fill='black')
    d.polygon([(x, y - 55), (x - 70, y + 60), (x + 70, y + 60)], fill=(250, 205, 30))
    fonte = carregar_fonte(ARGS.fonte, 90)
    d.text((x - 14, y - 45), '!', font=fonte, fill='black')


def sem_texto(nome):
    """Paisagem com um monumento estilizado (colunas e frontão), sem nenhum texto."""
    largura, altura = 1200, 800
    img = Image.new('RGB', (largura, altura))
    d = ImageDraw.Draw(img)
    for y in range(altura):  # céu em degradê
        t = y / altura
        d.line([(0, y), (largura, y)], fill=(int(90 + 120 * t), int(150 + 80 * t), int(225 + 20 * t)))
    d.rectangle((0, 620, largura, altura), fill=(120, 120, 115))      # chão
    pedra = (214, 200, 170)
    d.rectangle((300, 560, 900, 620), fill=pedra)                       # base
    for x in range(330, 880, 92):                                       # colunas
        d.rectangle((x, 300, x + 46, 560), fill=pedra, outline=(170, 155, 125), width=3)
    d.rectangle((280, 250, 920, 300), fill=pedra)                       # arquitrave
    d.polygon([(280, 250), (600, 140), (920, 250)], fill=pedra)         # frontão
    d.ellipse((960, 90, 1060, 190), fill=(255, 240, 180))               # sol
    salvar(img.filter(ImageFilter.GaussianBlur(0.8)), nome)


def baixa_qualidade(origem, nome):
    """Simula uma foto ruim: inclinada, desfocada, escura e com compressão forte."""
    img = origem.rotate(9, resample=Image.BICUBIC, expand=True, fillcolor=(80, 80, 80))
    img = img.filter(ImageFilter.GaussianBlur(3.2))
    img = Image.eval(img, lambda v: int(v * 0.55))
    img = img.resize((img.width // 2, img.height // 2))
    salvar(img, nome, qualidade=35)


def salvar(img, nome, qualidade=88):
    SAIDA.mkdir(parents=True, exist_ok=True)
    img.save(SAIDA / nome, quality=qualidade)
    print(f'  {nome}  ({img.width}x{img.height})')


def main():
    print(f'Gerando em {SAIDA.relative_to(RAIZ)}/ (raqm: {"sim" if TEM_RAQM else "não"})')

    # ---- Alemão
    placa('alemao_saida_emergencia.jpg', ['Notausgang'], cor_placa=(0, 135, 70),
          tamanhos_fonte=[130], icone=icone_saida, semente=11)
    rua = placa('alemao_placa_rua.jpg', ['Unter den Linden', 'Brandenburger Tor'],
                cor_placa=(25, 60, 130), tamanhos_fonte=[100, 70], semente=12)
    placa('alemao_proibido_fumar.jpg', ['Rauchen verboten', 'Bitte nicht rauchen'],
          cor_placa=(245, 245, 240), cor_texto=(30, 30, 30), borda=(200, 30, 30),
          tamanhos_fonte=[84, 60], icone=icone_proibido, icone_a_esquerda=True, semente=13)

    # ---- Russo
    placa('russo_metro.jpg', ['Выход в город', 'Красная площадь'], cor_placa=(200, 30, 40),
          tamanhos_fonte=[90, 72], icone=icone_metro, icone_a_esquerda=True, semente=21)
    placa('russo_museu.jpg', ['Государственный', 'исторический музей'], cor_placa=(45, 35, 30),
          cor_texto=(225, 190, 110), borda=(225, 190, 110), tamanhos_fonte=[84, 84], semente=22)
    placa('russo_cuidado_piso.jpg', ['Осторожно!', 'Скользкий пол'], cor_placa=(250, 205, 30),
          cor_texto=(20, 20, 20), borda=(20, 20, 20), tamanhos_fonte=[100, 80],
          icone=icone_atencao, icone_a_esquerda=True, semente=23)

    # ---- Árabe
    placa('arabe_saida_emergencia.jpg', ['مخرج الطوارئ'], cor_placa=(0, 135, 70),
          tamanhos_fonte=[130], rtl=[True], icone=icone_saida, semente=31)
    placa('arabe_museu.jpg', ['المتحف المصري'], cor_placa=(110, 60, 30),
          tamanhos_fonte=[130], rtl=[True], semente=32)
    placa('arabe_bilingue_rua.jpg', ['شارع التحرير', 'Tahrir Street'], cor_placa=(25, 60, 130),
          tamanhos_fonte=[110, 64], rtl=[True, False], semente=33)
    placa('arabe_proibido_fumar.jpg', ['ممنوع التدخين'], cor_placa=(245, 245, 240),
          cor_texto=(30, 30, 30), borda=(200, 30, 30), tamanhos_fonte=[110], rtl=[True],
          icone=icone_proibido, icone_a_esquerda=True, semente=34)

    # ---- Casos-limite
    sem_texto('sem_texto_monumento.jpg')
    baixa_qualidade(rua, 'baixa_qualidade_alemao.jpg')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--fonte', help='caminho da fonte DejaVuSans-Bold.ttf')
    ARGS = parser.parse_args()
    if not ARGS.fonte:
        ARGS.fonte = next((f for f in FONTES_PADRAO if Path(f).exists()), None)
        if not ARGS.fonte:
            parser.error('fonte DejaVu Sans Bold não encontrada; informe --fonte')
    main()
