#!/usr/bin/env python3
"""Envia as imagens de testes/imagens/ para a API implantada e salva os resultados.

Uso:
    python scripts/testar_api.py https://<id>.execute-api.sa-east-1.amazonaws.com/api/
    python scripts/testar_api.py <URL> caminho/foto1.jpg caminho/foto2.png

Para cada imagem são gravados em testes/resultados/:
    <nome>.json                    resposta completa da API
    <nome>_narracao_pt.mp3         narração em português
    <nome>_pronuncia_original.mp3  pronúncia do texto original (se houver texto)
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_IMAGENS = RAIZ / 'testes' / 'imagens'
PASTA_RESULTADOS = RAIZ / 'testes' / 'resultados'
TIPOS = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}


def requisitar(url, dados=None, tipo=None):
    req = urllib.request.Request(url, data=dados, method='POST' if dados else 'GET')
    if tipo:
        req.add_header('Content-Type', tipo)
    req.add_header('Accept', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as erro:
        return erro.code, json.loads(erro.read() or b'{}')


def testar(base, imagem):
    print(f'\n== {imagem.name}')
    inicio = time.time()
    status, corpo = requisitar(base + 'imagens', imagem.read_bytes(), TIPOS[imagem.suffix.lower()])
    if status != 202:
        print(f'   envio falhou ({status}): {corpo}')
        return
    id_imagem = corpo['id']
    for _ in range(40):
        time.sleep(1.5)
        status, corpo = requisitar(f'{base}imagens/{id_imagem}')
        if status != 202:
            break
    duracao = time.time() - inicio

    nome = imagem.stem
    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    urls = corpo.pop('audios_url', {})
    corpo['arquivo_de_entrada'] = imagem.name
    corpo['tempo_total_segundos'] = round(duracao, 1)
    (PASTA_RESULTADOS / f'{nome}.json').write_text(
        json.dumps(corpo, ensure_ascii=False, indent=2), encoding='utf-8')
    for tipo_audio, url in urls.items():
        with urllib.request.urlopen(url, timeout=30) as resp:
            (PASTA_RESULTADOS / f'{nome}_{tipo_audio}.mp3').write_bytes(resp.read())

    print(f'   status: {corpo.get("status")} em {duracao:.1f}s')
    print(f'   idioma: {corpo.get("idioma_detectado")}')
    print(f'   texto:  {corpo.get("texto_original", "")!r}')
    print(f'   pt:     {corpo.get("texto_traduzido", "")!r}')
    print(f'   cena:   {[c["rotulo_pt"] for c in corpo.get("cena", [])]}')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    base = sys.argv[1].rstrip('/') + '/'
    imagens = [Path(p) for p in sys.argv[2:]] or sorted(
        p for p in PASTA_IMAGENS.iterdir() if p.suffix.lower() in TIPOS)
    if not imagens:
        sys.exit(f'Nenhuma imagem JPEG/PNG em {PASTA_IMAGENS}')
    for imagem in imagens:
        testar(base, imagem)


if __name__ == '__main__':
    main()
