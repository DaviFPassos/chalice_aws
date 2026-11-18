import { useId, useState } from 'react'

export default function CodigoAcesso({ codigo, aoMudar, lembrar, aoMudarLembrar, invalido, desabilitado, entradaRef }) {
  const id = useId()
  const [visivel, setVisivel] = useState(false)

  return (
    <div className="codigo-acesso">
      <label htmlFor={id}>Código de acesso</label>
      <div className="campo-codigo">
        <input
          id={id}
          ref={entradaRef}
          type={visivel ? 'text' : 'password'}
          value={codigo}
          onChange={(e) => aoMudar(e.target.value)}
          placeholder="XXXX-XXXX-XXXX"
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          aria-invalid={invalido || undefined}
          aria-describedby={`${id}-ajuda`}
          disabled={desabilitado}
        />
        <button type="button" className="botao-secundario" onClick={() => setVisivel((v) => !v)}
          aria-pressed={visivel} disabled={desabilitado}>
          {visivel ? 'Ocultar' : 'Mostrar'}
        </button>
      </div>
      <p id={`${id}-ajuda`} className="ajuda">
        Para evitar custos com uso indevido, só quem tem o código pode enviar fotos. Peça-o à equipe do projeto.
      </p>
      <label className="lembrar">
        <input type="checkbox" checked={lembrar} onChange={(e) => aoMudarLembrar(e.target.checked)} disabled={desabilitado} />
        Lembrar neste navegador
      </label>
    </div>
  )
}
