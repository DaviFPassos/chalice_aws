import { useRef, useState } from 'react'
import { validarTipo } from '../imagem.js'

export default function EnvioImagem({ aoEscolher, desabilitado }) {
  const entrada = useRef(null)
  const [arrastando, setArrastando] = useState(false)
  const [erro, setErro] = useState(null)

  function escolher(arquivo) {
    const problema = validarTipo(arquivo)
    setErro(problema)
    if (!problema) aoEscolher(arquivo)
  }

  function aoSoltar(evento) {
    evento.preventDefault()
    setArrastando(false)
    if (!desabilitado) escolher(evento.dataTransfer.files?.[0])
  }

  return (
    <div>
      <button
        type="button"
        className={`area-envio${arrastando ? ' arrastando' : ''}`}
        onClick={() => entrada.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setArrastando(true) }}
        onDragLeave={() => setArrastando(false)}
        onDrop={aoSoltar}
        disabled={desabilitado}
      >
        <svg width="40" height="40" viewBox="0 0 24 24" aria-hidden="true">
          <path fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"
            d="M4 7h3l2-2h6l2 2h3v12H4zM12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" />
        </svg>
        <strong>Tire ou escolha uma foto</strong>
        <span>Arraste aqui ou clique · JPEG ou PNG · fotos grandes são reduzidas automaticamente</span>
      </button>
      <input
        ref={entrada}
        type="file"
        accept="image/jpeg,image/png"
        capture="environment"
        hidden
        onChange={(e) => { escolher(e.target.files?.[0]); e.target.value = '' }}
      />
      {erro && <p className="aviso erro" role="alert">{erro}</p>}
    </div>
  )
}
