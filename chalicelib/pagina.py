"""Página web simples (servida em GET /) para enviar fotos e ouvir o resultado."""

HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Leitor de Placas com Voz</title>
<style>
  :root { --bg:#f6f7f9; --card:#fff; --txt:#1c1f24; --muted:#5b6470; --borda:#d9dde3; --destaque:#0b6bcb; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#14171b; --card:#1d2126; --txt:#e8eaed; --muted:#9aa3ad; --borda:#323840; --destaque:#5aa9ff; }
  }
  * { box-sizing: border-box; }
  body { margin:0; font:16px/1.5 system-ui, sans-serif; background:var(--bg); color:var(--txt); }
  main { max-width:720px; margin:0 auto; padding:24px 16px 48px; }
  h1 { font-size:1.6rem; margin:0 0 4px; }
  p.sub { margin:0 0 24px; color:var(--muted); }
  .card { background:var(--card); border:1px solid var(--borda); border-radius:12px; padding:20px; margin-bottom:16px; }
  label.drop { display:block; border:2px dashed var(--borda); border-radius:10px; padding:28px; text-align:center; cursor:pointer; color:var(--muted); }
  label.drop:hover { border-color:var(--destaque); }
  input[type=file] { display:none; }
  img#previa { max-width:100%; max-height:320px; display:none; margin:16px auto 0; border-radius:8px; }
  button { margin-top:16px; width:100%; padding:12px; font-size:1rem; border:0; border-radius:8px; background:var(--destaque); color:#fff; cursor:pointer; }
  button:disabled { opacity:.5; cursor:default; }
  #status { color:var(--muted); min-height:1.5em; margin-top:12px; }
  h2 { font-size:1rem; margin:16px 0 4px; color:var(--muted); font-weight:600; }
  .texto { font-size:1.15rem; white-space:pre-wrap; }
  .tags span { display:inline-block; padding:2px 10px; margin:2px; border-radius:999px; border:1px solid var(--borda); font-size:.9rem; }
  audio { width:100%; margin-top:4px; }
  #resultado { display:none; }
</style>
</head>
<body>
<main>
  <h1>Leitor de Placas com Voz</h1>
  <p class="sub">Envie a foto de uma placa ou monumento com texto em árabe, russo ou alemão
     e ouça a tradução em português.</p>

  <div class="card">
    <label class="drop" for="arquivo">Clique para escolher uma foto (JPEG ou PNG, até 5 MB)</label>
    <input id="arquivo" type="file" accept="image/jpeg,image/png">
    <img id="previa" alt="Prévia da imagem escolhida">
    <button id="enviar" disabled>Ler e traduzir</button>
    <div id="status" role="status"></div>
  </div>

  <div class="card" id="resultado">
    <h2>Idioma detectado</h2><div id="idioma"></div>
    <h2>Texto original</h2><div class="texto" id="original" dir="auto"></div>
    <h2>Tradução</h2><div class="texto" id="traducao"></div>
    <h2>Elementos da cena</h2><div class="tags" id="cena"></div>
    <h2>Narração em português</h2><audio id="audioPt" controls></audio>
    <div id="blocoOriginal"><h2>Pronúncia original</h2><audio id="audioOriginal" controls></audio></div>
  </div>
</main>
<script>
const base = location.pathname.replace(/\/?$/, '/');
const $ = (id) => document.getElementById(id);
const NOMES = {ar:'Árabe', ru:'Russo', de:'Alemão', en:'Inglês', es:'Espanhol', fr:'Francês', it:'Italiano', pt:'Português'};
let arquivo = null;

$('arquivo').addEventListener('change', (e) => {
  arquivo = e.target.files[0] || null;
  $('enviar').disabled = !arquivo;
  if (arquivo) { $('previa').src = URL.createObjectURL(arquivo); $('previa').style.display = 'block'; }
});

$('enviar').addEventListener('click', async () => {
  $('enviar').disabled = true;
  $('resultado').style.display = 'none';
  $('status').textContent = 'Enviando imagem...';
  try {
    const r = await fetch(base + 'imagens', { method:'POST', headers:{'Content-Type': arquivo.type}, body: arquivo });
    const dados = await r.json();
    if (!r.ok) throw new Error(dados.Message || 'Erro no envio');
    await aguardar(dados.id);
  } catch (erro) {
    $('status').textContent = 'Erro: ' + erro.message;
  } finally {
    $('enviar').disabled = !arquivo;
  }
});

async function aguardar(id) {
  for (let i = 0; i < 40; i++) {
    $('status').textContent = 'Processando (Rekognition → Translate → Polly)' + '.'.repeat(i % 4);
    await new Promise((ok) => setTimeout(ok, 1500));
    const r = await fetch(base + 'imagens/' + id);
    if (r.status === 202) continue;
    const dados = await r.json();
    if (!r.ok) throw new Error(dados.Message || 'Erro na consulta');
    if (dados.status === 'erro') throw new Error(dados.erro);
    mostrar(dados);
    $('status').textContent = 'Pronto!';
    return;
  }
  throw new Error('Tempo esgotado. Tente novamente.');
}

function mostrar(d) {
  $('idioma').textContent = d.idioma_detectado ? (NOMES[d.idioma_detectado] || d.idioma_detectado) : '—';
  $('original').textContent = d.texto_original || 'Nenhum texto encontrado.';
  $('traducao').textContent = d.texto_traduzido || '—';
  $('cena').replaceChildren(...(d.cena || []).map((c) => {
    const s = document.createElement('span');
    s.textContent = c.rotulo_pt + ' (' + Math.round(c.confianca) + '%)';
    return s;
  }));
  const urls = d.audios_url || {};
  $('audioPt').src = urls.narracao_pt || '';
  $('blocoOriginal').style.display = urls.pronuncia_original ? 'block' : 'none';
  $('audioOriginal').src = urls.pronuncia_original || '';
  $('resultado').style.display = 'block';
}
</script>
</body>
</html>
"""
