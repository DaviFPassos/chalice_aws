#!/usr/bin/env python3
"""Gera docs/arquitetura.png com os ícones oficiais da AWS (AWS Architecture Icons).

Os ícones não ficam no repositório: são lidos direto do pacote oficial, baixado em
https://aws.amazon.com/architecture/icons/ ("Asset package").

Uso:
    pip install -r requirements-dev.txt
    python scripts/gerar_diagrama_arquitetura.py ~/Downloads/Icon-package_07312026.zip

Fonte: DejaVu Sans (fonts-dejavu no Linux) ou outra informada em --fonte.
"""
import argparse
import io
import math
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'docs' / 'arquitetura.png'

# Nome do arquivo dentro do pacote oficial (o prefixo de pasta muda a cada versão)
ICONES = {
    'apigw': 'Arch_Amazon-API-Gateway_64@5x.png',
    'lambda': 'Arch_AWS-Lambda_64@5x.png',
    's3': 'Arch_Amazon-Simple-Storage-Service_64@5x.png',
    'ssm': 'Arch_AWS-Systems-Manager_64@5x.png',
    'cloudwatch': 'Arch_Amazon-CloudWatch_64@5x.png',
    'iam': 'Arch_AWS-Identity-and-Access-Management_64@5x.png',
    'rekognition': 'Arch_Amazon-Rekognition_64@5x.png',
    'translate': 'Arch_Amazon-Translate_64@5x.png',
    'polly': 'Arch_Amazon-Polly_64@5x.png',
    'usuarios': 'Res_Users_48_Light.png',
    'cliente': 'Res_Client_48_Light.png',
    'nuvem': 'AWS-Cloud-logo_32.png',
    'regiao': 'Region_32.png',
}

FONTES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf',
    '/usr/share/fonts/TTF/DejaVuSans{}.ttf',
    '/Library/Fonts/DejaVuSans{}.ttf',
    'C:/Windows/Fonts/DejaVuSans{}.ttf',
]

# Cores no padrão dos diagramas da AWS
TINTA = (35, 47, 62)          # #232F3E (AWS Cloud)
REGIAO = (0, 164, 166)        # #00A4A6 (Region)
SETA = (60, 70, 84)
EVENTO = (231, 21, 123)       # destaque do evento orientado a eventos
SUAVE = (95, 105, 118)
FUNDO = (255, 255, 255)

L, A = 2560, 1440
TAM_ICONE = 118


def carregar_icones(pacote):
    icones = {}
    with zipfile.ZipFile(pacote) as z:
        nomes = [n for n in z.namelist() if not n.startswith('__MACOSX')]
        for chave, arquivo in ICONES.items():
            caminho = next((n for n in nomes if n.endswith('/' + arquivo)), None)
            if caminho is None:
                raise SystemExit(f'Ícone não encontrado no pacote: {arquivo}')
            icones[chave] = Image.open(io.BytesIO(z.read(caminho))).convert('RGBA')
    return icones


def fonte(tamanho, negrito=False):
    sufixo = '-Bold' if negrito else ''
    for modelo in FONTES:
        caminho = modelo.format(sufixo)
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    raise SystemExit('Fonte DejaVu Sans não encontrada; use --fonte')


class Diagrama:
    def __init__(self, icones):
        self.img = Image.new('RGB', (L, A), FUNDO)
        self.d = ImageDraw.Draw(self.img)
        self.icones = icones

    # ---------- elementos ----------
    def grupo(self, caixa, titulo, icone, cor, tracejado=False):
        x0, y0, x1, y1 = caixa
        if tracejado:
            self._retangulo_tracejado(caixa, cor, 3)
        else:
            self.d.rectangle(caixa, outline=cor, width=3)
        ic = self.icones[icone].resize((52, 52), Image.LANCZOS)
        self.img.paste(ic, (x0, y0), ic)
        self.d.text((x0 + 64, y0 + 12), titulo, font=fonte(26, True), fill=cor)

    def servico(self, chave, cx, cy, nome, detalhe=None, tam=TAM_ICONE, rotulo_acima=False):
        ic = self.icones[chave].resize((tam, tam), Image.LANCZOS)
        self.img.paste(ic, (int(cx - tam / 2), int(cy - tam / 2)), ic)
        linhas_detalhe = len(detalhe.split('\n')) if detalhe else 0
        altura_rotulo = 30 + 26 * linhas_detalhe
        y = cy - tam / 2 - 10 - altura_rotulo if rotulo_acima else cy + tam / 2 + 10
        for i, linha in enumerate([nome] + ([detalhe] if detalhe else [])):
            f = fonte(24 if i == 0 else 20, negrito=(i == 0))
            for parte in linha.split('\n'):
                w = self.d.textlength(parte, font=f)
                self.d.text((cx - w / 2, y), parte, font=f, fill=TINTA if i == 0 else SUAVE)
                y += 30 if i == 0 else 26

    def seta(self, pontos, cor=SETA, largura=4, tracejada=False, rotulo=None, numero=None,
             pos_rotulo=None, alinhamento='centro'):
        for a, b in zip(pontos, pontos[1:]):
            if tracejada:
                self._linha_tracejada(a, b, cor, largura)
            else:
                self.d.line([a, b], fill=cor, width=largura)
        self._ponta(pontos[-2], pontos[-1], cor)
        if rotulo or numero:
            px, py = pos_rotulo or self._meio(pontos)
            self._rotulo(px, py, rotulo, numero, cor, alinhamento)

    # ---------- auxiliares ----------
    def _meio(self, pontos):
        a, b = pontos[len(pontos) // 2 - 1], pontos[len(pontos) // 2]
        return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2

    def _ponta(self, a, b, cor):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        tam = 20
        p1 = (b[0] - tam * math.cos(ang - 0.42), b[1] - tam * math.sin(ang - 0.42))
        p2 = (b[0] - tam * math.cos(ang + 0.42), b[1] - tam * math.sin(ang + 0.42))
        self.d.polygon([b, p1, p2], fill=cor)

    def _linha_tracejada(self, a, b, cor, largura, traco=16, vao=10):
        dist = math.dist(a, b)
        if dist == 0:
            return
        ux, uy = (b[0] - a[0]) / dist, (b[1] - a[1]) / dist
        t = 0.0
        while t < dist:
            fim = min(t + traco, dist)
            self.d.line([(a[0] + ux * t, a[1] + uy * t), (a[0] + ux * fim, a[1] + uy * fim)],
                        fill=cor, width=largura)
            t += traco + vao

    def _retangulo_tracejado(self, caixa, cor, largura):
        x0, y0, x1, y1 = caixa
        for a, b in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
            self._linha_tracejada(a, b, cor, largura, traco=14, vao=8)

    def _rotulo(self, x, y, texto, numero, cor, alinhamento):
        f = fonte(20)
        linhas = texto.split('\n') if texto else []
        largura = max((self.d.textlength(l, font=f) for l in linhas), default=0)
        raio = 19
        total = (2 * raio + 10 if numero else 0) + largura
        altura = max(2 * raio, 26 * len(linhas))
        if alinhamento == 'centro':
            x0 = x - total / 2
        elif alinhamento == 'direita':
            x0 = x - total
        else:
            x0 = x
        y0 = y - altura / 2
        self.d.rounded_rectangle((x0 - 8, y0 - 6, x0 + total + 8, y0 + altura + 6), radius=10,
                                 fill=FUNDO)
        cx = x0
        if numero:
            self.d.ellipse((cx, y - raio, cx + 2 * raio, y + raio), fill=cor)
            fn = fonte(22, True)
            w = self.d.textlength(str(numero), font=fn)
            self.d.text((cx + raio - w / 2, y - 14), str(numero), font=fn, fill='white')
            cx += 2 * raio + 10
        ty = y - 26 * len(linhas) / 2
        for linha in linhas:
            self.d.text((cx, ty), linha, font=f, fill=TINTA)
            ty += 26

    def texto(self, x, y, texto, tamanho=22, negrito=False, cor=TINTA):
        self.d.text((x, y), texto, font=fonte(tamanho, negrito), fill=cor)


def desenhar(icones):
    g = Diagrama(icones)
    d = g.d

    # Título
    g.texto(40, 28, 'Leitor de Placas com Voz — arquitetura na AWS', 40, True)
    g.texto(40, 80, 'Aplicação serverless (AWS Chalice + AWS Lambda), orientada a eventos, '
                    'com Amazon Rekognition → Amazon Translate → Amazon Polly', 22, cor=SUAVE)

    # Grupos
    g.grupo((560, 140, 2520, 1410), 'AWS Cloud', 'nuvem', TINTA)
    g.grupo((590, 210, 1900, 1385), 'Região América do Sul (São Paulo) · sa-east-1', 'regiao',
            REGIAO, tracejado=True)
    g.grupo((1940, 210, 2490, 1385), 'Região Leste dos EUA · us-east-1', 'regiao', REGIAO,
            tracejado=True)

    def base(cy, linhas_detalhe, tam=TAM_ICONE):
        """Coordenada y logo abaixo do rótulo de um serviço."""
        return cy + tam / 2 + 10 + 30 + 26 * linhas_detalhe

    # Fora da AWS
    g.servico('usuarios', 210, 250, 'Usuário', 'turista, intercambista,\npessoa com deficiência visual', tam=96)
    g.servico('cliente', 210, 620, 'Front-end React', 'GitHub Pages\n(código de acesso)', tam=96)

    Y = 620           # fileira da API
    YP = 1010         # fileira do processamento
    g.servico('apigw', 790, Y, 'Amazon API Gateway', 'API REST\n1 req/s')
    g.servico('lambda', 1110, Y, 'AWS Lambda', 'api_handler\n(cota 30/dia · 300/mês)')
    g.servico('ssm', 1110, 360, 'AWS Systems Manager', 'Parameter Store')
    g.servico('s3', 1450, Y, 'Amazon S3', 'uploads/ · resultados/\naudios/ · controle/')
    g.servico('lambda', 1450, YP, 'AWS Lambda', 'ao_enviar_imagem')
    g.servico('rekognition', 1740, 770, 'Amazon Rekognition', 'DetectText +\nDetectLabels',
              rotulo_acima=True)
    g.servico('cloudwatch', 1110, YP, 'Amazon CloudWatch', 'Logs')
    g.servico('iam', 790, 1215, 'AWS IAM', 'roles com\npermissões mínimas')
    g.servico('translate', 2215, YP, 'Amazon Translate', 'ar / ru / de → pt')
    g.servico('polly', 2215, 1215, 'Amazon Polly', 'narração pt-BR +\npronúncia original')

    m = TAM_ICONE / 2 + 12
    # Usuário → front
    g.seta([(210, base(250, 2, 96) + 8), (210, Y - 48 - 10)])
    # 1 (e 8): front → API Gateway → api_handler
    g.seta([(210 + 58, Y), (790 - m, Y)], numero=1,
           rotulo='POST /imagens\n(8) GET /imagens/{id}', pos_rotulo=(545, Y - 46),
           alinhamento='direita')
    g.seta([(790 + m, Y), (1110 - m, Y)])
    # 2: código de acesso no SSM
    g.seta([(1110, Y - TAM_ICONE / 2 - 6), (1110, base(360, 1) + 6)], numero=2,
           rotulo='confere o código', pos_rotulo=(1135, (Y - 65 + base(360, 1)) / 2),
           alinhamento='esquerda')
    # 3: api_handler → S3
    g.seta([(1110 + m, Y), (1450 - m, Y)], numero=3,
           rotulo='grava a foto\nlê o resultado', pos_rotulo=(1280, Y - 58))
    # 4: evento do S3 → Lambda de processamento
    topo_proc = YP - TAM_ICONE / 2 - 8
    g.seta([(1428, base(Y, 2) + 8), (1428, topo_proc)], cor=EVENTO, largura=5, numero=4,
           rotulo='evento s3:ObjectCreated', pos_rotulo=(1410, 820), alinhamento='direita')
    # 8: resultado de volta ao S3
    g.seta([(1472, topo_proc), (1472, base(Y, 2) + 8)], numero=8,
           rotulo='resultado JSON + MP3', pos_rotulo=(1410, 905), alinhamento='direita')
    # 5: Rekognition
    g.seta([(1513, YP - 45), (1740 - 64, 770 + 30)], numero=5,
           rotulo='texto + cena', pos_rotulo=(1600, 905), alinhamento='esquerda')
    # 6: Translate
    g.seta([(1450 + m, YP), (2215 - m, YP)], numero=6,
           rotulo='texto → pt', pos_rotulo=(1950, YP - 36))
    # 7: Polly
    g.seta([(1513, YP + 45), (2215 - m, 1215)], numero=7,
           rotulo='tradução → MP3', pos_rotulo=(1800, 1178))
    # logs (tracejado)
    g.seta([(1450 - m, YP), (1110 + m, YP)], cor=SUAVE, largura=3, tracejada=True)
    g.seta([(1075, base(Y, 2) + 8), (1075, topo_proc)], cor=SUAVE, largura=3, tracejada=True)

    # Legenda (fluxo)
    passos = [
        '1  O front envia a foto (POST /imagens)',
        '2  A API confere o código de acesso no SSM',
        '3  A API grava a foto em uploads/ e',
        '    responde 202 com um id',
        '4  O upload gera o evento que dispara',
        '    a Lambda de processamento',
        '5  Rekognition lê o texto e a cena',
        '6  Translate traduz para o português',
        '7  Polly gera os áudios (MP3)',
        '8  Resultado salvo no S3; o front consulta',
        '    GET /imagens/{id} e toca os áudios',
    ]
    g.texto(40, 785, 'Fluxo', 28, True)
    y = 831
    for p in passos:
        g.texto(40, y, p, 21, cor=TINTA if not p.startswith('    ') else SUAVE)
        y += 32
    g.texto(40, 1190, 'Legenda', 24, True)
    d.line([(40, 1242), (110, 1242)], fill=EVENTO, width=5)
    g.texto(124, 1228, 'evento do S3 (orientado a eventos)', 20)
    g._linha_tracejada((40, 1282), (110, 1282), SUAVE, 3)
    g.texto(124, 1268, 'logs', 20)
    d.line([(40, 1322), (110, 1322)], fill=SETA, width=4)
    g.texto(124, 1308, 'chamada / fluxo de dados', 20)
    g.texto(40, 1372, 'Ícones: AWS Architecture Icons (oficiais)', 18, cor=SUAVE)
    return g.img


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('pacote', help='zip do pacote oficial de ícones da AWS')
    parser.add_argument('--saida', default=str(SAIDA))
    args = parser.parse_args()
    img = desenhar(carregar_icones(args.pacote))
    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    img.save(args.saida, optimize=True)
    print(f'Diagrama salvo em {args.saida} ({img.width}x{img.height})')


if __name__ == '__main__':
    main()
