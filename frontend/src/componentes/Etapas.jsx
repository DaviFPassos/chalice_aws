// Mostra o encadeamento dos serviços enquanto a imagem é processada.
// A API só informa "processando"/"pronto", então a etapa ativa é estimada pelo tempo.

const ETAPAS = [
  { id: 'envio', titulo: 'Envio', servico: 'Amazon S3' },
  { id: 'leitura', titulo: 'Leitura do texto', servico: 'Amazon Rekognition' },
  { id: 'traducao', titulo: 'Tradução', servico: 'Amazon Translate' },
  { id: 'voz', titulo: 'Áudio', servico: 'Amazon Polly' },
]

export function etapaAtual(fase, tentativas) {
  if (fase === 'enviando') return 0
  if (fase === 'concluido') return ETAPAS.length
  if (fase !== 'processando') return -1
  return Math.min(1 + Math.floor(tentativas / 2), ETAPAS.length - 1)
}

export default function Etapas({ fase, tentativas }) {
  const atual = etapaAtual(fase, tentativas)
  return (
    <ol className="etapas" aria-label="Etapas do processamento">
      {ETAPAS.map((etapa, i) => {
        const estado = i < atual ? 'feita' : i === atual ? 'ativa' : 'pendente'
        return (
          <li key={etapa.id} className={`etapa ${estado}`} aria-current={estado === 'ativa' ? 'step' : undefined}>
            <span className="marcador" aria-hidden="true">{estado === 'feita' ? '✓' : i + 1}</span>
            <span className="etapa-texto">
              <strong>{etapa.titulo}</strong>
              <small>{etapa.servico}</small>
            </span>
          </li>
        )
      })}
    </ol>
  )
}
