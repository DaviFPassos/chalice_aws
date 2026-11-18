// Descobre a URL da API, nesta ordem:
//   1. parâmetro ?api= na URL da página (útil depois de um novo `chalice deploy`,
//      que gera uma URL nova) — fica salvo no navegador para as próximas visitas;
//   2. URL salva anteriormente no navegador;
//   3. VITE_API_URL definida no build;
//   4. '/api/' (desenvolvimento, com o proxy do Vite).

const CHAVE = 'leitor-placas:api'

function comBarra(url) {
  return url.endsWith('/') ? url : `${url}/`
}

function lerSalvo(armazenamento) {
  try {
    return armazenamento?.getItem(CHAVE) || null
  } catch {
    return null
  }
}

function salvar(armazenamento, valor) {
  try {
    armazenamento?.setItem(CHAVE, valor)
  } catch {
    // navegação privada ou armazenamento bloqueado: segue sem salvar
  }
}

export function urlValida(valor) {
  try {
    const url = new URL(valor)
    return url.protocol === 'https:'
  } catch {
    return false
  }
}

export function obterApiBase({
  busca = typeof window !== 'undefined' ? window.location.search : '',
  armazenamento = typeof window !== 'undefined' ? window.localStorage : null,
  padrao = import.meta.env.VITE_API_URL,
} = {}) {
  const daUrl = new URLSearchParams(busca).get('api')
  if (daUrl && urlValida(daUrl)) {
    salvar(armazenamento, daUrl)
    return comBarra(daUrl)
  }
  const salvo = lerSalvo(armazenamento)
  if (salvo && urlValida(salvo)) return comBarra(salvo)
  if (padrao) return comBarra(padrao)
  return '/api/'
}
