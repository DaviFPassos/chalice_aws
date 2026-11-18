import { useEffect, useMemo, useRef, useState } from 'react'
import { aguardarResultado, enviarImagem } from './api.js'
import { esquecerCodigo, lerCodigoSalvo, obterApiBase, salvarCodigo } from './config.js'
import { prepararImagem } from './imagem.js'
import CodigoAcesso from './componentes/CodigoAcesso.jsx'
import EnvioImagem from './componentes/EnvioImagem.jsx'
import Etapas from './componentes/Etapas.jsx'
import Resultado from './componentes/Resultado.jsx'

export default function App() {
  const apiBase = useMemo(() => obterApiBase(), [])
  const [arquivo, setArquivo] = useState(null)
  const [previa, setPrevia] = useState(null)
  const [fase, setFase] = useState('ocioso') // ocioso | enviando | processando | concluido | erro
  const [tentativas, setTentativas] = useState(0)
  const [erro, setErro] = useState(null)
  const [historico, setHistorico] = useState([]) // [{ dados, previa }], mais recente primeiro
  const previasEmUso = useRef(new Set()) // prévias exibidas no histórico não podem ser liberadas
  const [codigo, setCodigo] = useState(() => lerCodigoSalvo())
  const [lembrar, setLembrar] = useState(() => Boolean(lerCodigoSalvo()))
  const [codigoInvalido, setCodigoInvalido] = useState(false)
  const campoCodigo = useRef(null)

  useEffect(() => {
    if (!arquivo) return undefined
    const url = URL.createObjectURL(arquivo)
    setPrevia(url)
    return () => {
      if (!previasEmUso.current.has(url)) URL.revokeObjectURL(url)
    }
  }, [arquivo])

  const ocupado = fase === 'enviando' || fase === 'processando'

  function mudarCodigo(valor) {
    setCodigo(valor)
    setCodigoInvalido(false)
  }

  function mudarLembrar(valor) {
    setLembrar(valor)
    if (!valor) esquecerCodigo()
  }

  function escolher(novo) {
    setArquivo(novo)
    setErro(null)
    setFase('ocioso')
  }

  async function processar() {
    setErro(null)
    setTentativas(0)
    setFase('enviando')
    try {
      const imagem = await prepararImagem(arquivo)
      const { id } = await enviarImagem(apiBase, imagem, { codigo })
      if (lembrar) salvarCodigo(codigo)
      setFase('processando')
      const dados = await aguardarResultado(apiBase, id, { codigo, aoTentar: setTentativas })
      previasEmUso.current.add(previa)
      setHistorico((h) => [{ dados, previa }, ...h].slice(0, 10))
      setFase('concluido')
      setArquivo(null)
    } catch (e) {
      setErro(e.message)
      setFase('erro')
      if (e.status === 401) {
        setCodigoInvalido(true)
        esquecerCodigo()
        campoCodigo.current?.focus()
      }
    }
  }

  const [atual, ...anteriores] = historico

  return (
    <div className="pagina">
      <header className="topo">
        <h1>Leitor de Placas com Voz</h1>
        <p>Fotografe uma placa ou monumento em <strong>árabe</strong>, <strong>russo</strong> ou{' '}
          <strong>alemão</strong> e ouça a tradução em português.</p>
      </header>

      <main>
        <section className="cartao" aria-label="Enviar imagem">
          <CodigoAcesso
            codigo={codigo}
            aoMudar={mudarCodigo}
            lembrar={lembrar}
            aoMudarLembrar={mudarLembrar}
            invalido={codigoInvalido}
            desabilitado={ocupado}
            entradaRef={campoCodigo}
          />
          <EnvioImagem aoEscolher={escolher} desabilitado={ocupado} />
          {previa && arquivo && <img src={previa} alt="Prévia da foto escolhida" className="previa" />}
          <button type="button" className="botao" onClick={processar} disabled={!arquivo || !codigo.trim() || ocupado}>
            {ocupado ? 'Processando…' : 'Ler e traduzir'}
          </button>
          {(ocupado || fase === 'concluido') && <Etapas fase={fase} tentativas={tentativas} />}
          <div aria-live="polite">
            {erro && <p className="aviso erro" role="alert">{erro}</p>}
          </div>
        </section>

        {atual && <Resultado dados={atual.dados} previa={atual.previa} />}

        {anteriores.length > 0 && (
          <section className="historico" aria-label="Traduções anteriores">
            <h2>Anteriores</h2>
            <ul>
              {anteriores.map(({ dados, previa: img }) => (
                <li key={dados.id} className="cartao item-historico">
                  {img && <img src={img} alt="" className="miniatura pequena" />}
                  <div>
                    <strong>{dados.texto_traduzido || 'Sem texto'}</strong>
                    {dados.audios_url?.narracao_pt && <audio controls src={dados.audios_url.narracao_pt} preload="none" />}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>

      <footer className="rodape">
        Amazon Rekognition → Amazon Translate → Amazon Polly · AWS Lambda com Chalice
      </footer>
    </div>
  )
}
