import { infoIdioma } from '../idiomas.js'

export default function Resultado({ dados, previa }) {
  const idioma = infoIdioma(dados.idioma_detectado)
  const urls = dados.audios_url || {}
  const temTexto = Boolean(dados.texto_original)

  return (
    <article className="cartao resultado" aria-labelledby="titulo-resultado">
      <header className="resultado-topo">
        {previa && <img src={previa} alt="Foto enviada" className="miniatura" />}
        <div>
          <h2 id="titulo-resultado">{temTexto ? dados.texto_traduzido : 'Nenhum texto encontrado'}</h2>
          {temTexto && (
            <p className="selo"><span aria-hidden="true">{idioma.bandeira}</span> Traduzido do {idioma.nome.toLowerCase()}</p>
          )}
        </div>
      </header>

      <section className="audio-principal">
        <h3>Ouvir em português</h3>
        {urls.narracao_pt
          ? <audio controls src={urls.narracao_pt} preload="auto">Seu navegador não reproduz áudio.</audio>
          : <p className="aviso">Áudio indisponível.</p>}
        <p className="narracao">{dados.narracao}</p>
      </section>

      {temTexto && (
        <section>
          <h3>Texto original ({idioma.nome})</h3>
          <p className="texto-original" dir="auto" lang={idioma.lang}>{dados.texto_original}</p>
          {urls.pronuncia_original && (
            <>
              <h4>Pronúncia original</h4>
              <audio controls src={urls.pronuncia_original} preload="none" />
            </>
          )}
        </section>
      )}

      {dados.cena?.length > 0 && (
        <section>
          <h3>Na imagem</h3>
          <ul className="etiquetas">
            {dados.cena.map((c) => (
              <li key={c.rotulo} title={`${c.rotulo} · ${Math.round(c.confianca)}% de confiança`}>
                {c.rotulo_pt}
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  )
}
