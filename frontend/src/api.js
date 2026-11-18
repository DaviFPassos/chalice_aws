// Comunicação com a API Chalice.
//   POST /imagens          envia a imagem (corpo binário) -> 202 { id }
//   GET  /imagens/{id}     202 enquanto processa; 200 com o resultado

export class ErroApi extends Error {
  constructor(mensagem, status) {
    super(mensagem)
    this.name = 'ErroApi'
    this.status = status
  }
}

const MENSAGENS = {
  400: 'A imagem foi recusada. Envie uma foto JPEG ou PNG de até 5 MB.',
  404: 'Imagem não encontrada.',
  429: 'Limite de envios atingido. Tente novamente mais tarde.',
}

async function lerErro(resposta) {
  let detalhe = ''
  try {
    const corpo = await resposta.json()
    detalhe = corpo?.Message || ''
  } catch {
    // corpo vazio ou não-JSON
  }
  // 429 traz a mensagem da cota (diária ou mensal), que é mais informativa
  if (resposta.status === 429 && detalhe) return new ErroApi(detalhe, 429)
  return new ErroApi(MENSAGENS[resposta.status] || detalhe || `Erro ${resposta.status}`, resposta.status)
}

export async function enviarImagem(base, blob, { fetchFn = fetch } = {}) {
  let resposta
  try {
    resposta = await fetchFn(`${base}imagens`, {
      method: 'POST',
      headers: { 'Content-Type': blob.type || 'image/jpeg', Accept: 'application/json' },
      body: blob,
    })
  } catch {
    throw new ErroApi('Não foi possível conectar à API. Verifique se ela está no ar.', 0)
  }
  if (resposta.status !== 202) throw await lerErro(resposta)
  return resposta.json()
}

export async function consultarResultado(base, id, { fetchFn = fetch } = {}) {
  const resposta = await fetchFn(`${base}imagens/${id}`, { headers: { Accept: 'application/json' } })
  if (resposta.status === 202) return { pronto: false }
  if (!resposta.ok) throw await lerErro(resposta)
  return { pronto: true, dados: await resposta.json() }
}

const pausa = (ms) => new Promise((ok) => setTimeout(ok, ms))

export async function aguardarResultado(
  base,
  id,
  { intervalo = 1500, tentativas = 40, aoTentar = () => {}, esperar = pausa, fetchFn = fetch } = {},
) {
  for (let i = 1; i <= tentativas; i++) {
    await esperar(intervalo)
    aoTentar(i)
    const { pronto, dados } = await consultarResultado(base, id, { fetchFn })
    if (!pronto) continue
    if (dados.status === 'erro') throw new ErroApi(dados.erro || 'Falha no processamento.', 500)
    return dados
  }
  throw new ErroApi('O processamento demorou mais que o esperado. Tente novamente.', 408)
}
