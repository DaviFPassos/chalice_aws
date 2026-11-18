import { describe, expect, it } from 'vitest'
import { calcularDimensoes, precisaPreparar, TAMANHO_MAXIMO, validarTipo } from './imagem.js'
import { obterApiBase, urlValida } from './config.js'
import { etapaAtual } from './componentes/Etapas.jsx'

describe('validarTipo', () => {
  it('aceita JPEG e PNG', () => {
    expect(validarTipo({ type: 'image/jpeg' })).toBeNull()
    expect(validarTipo({ type: 'image/png' })).toBeNull()
  })
  it('recusa outros formatos e ausência de arquivo', () => {
    expect(validarTipo({ type: 'image/heic' })).toMatch(/JPEG ou PNG/)
    expect(validarTipo(null)).toMatch(/Escolha/)
  })
})

describe('calcularDimensoes', () => {
  it('mantém imagens pequenas', () => {
    expect(calcularDimensoes(1200, 800)).toEqual({ largura: 1200, altura: 800, reduzir: false })
  })
  it('reduz o maior lado para 2000 px mantendo a proporção', () => {
    expect(calcularDimensoes(4000, 3000)).toEqual({ largura: 2000, altura: 1500, reduzir: true })
    expect(calcularDimensoes(3024, 4032)).toEqual({ largura: 1500, altura: 2000, reduzir: true })
  })
})

describe('precisaPreparar', () => {
  it('prepara quando passa de 5 MB ou das dimensões', () => {
    expect(precisaPreparar({ size: TAMANHO_MAXIMO + 1 }, { reduzir: false })).toBe(true)
    expect(precisaPreparar({ size: 1000 }, { reduzir: true })).toBe(true)
    expect(precisaPreparar({ size: 1000 }, { reduzir: false })).toBe(false)
  })
})

describe('obterApiBase', () => {
  const memoria = () => {
    const dados = {}
    return { getItem: (k) => dados[k] ?? null, setItem: (k, v) => { dados[k] = v } }
  }

  it('usa ?api= da URL e salva para as próximas visitas', () => {
    const armazenamento = memoria()
    const url = 'https://abc.execute-api.sa-east-1.amazonaws.com/api'
    expect(obterApiBase({ busca: `?api=${url}`, armazenamento, padrao: '' })).toBe(`${url}/`)
    expect(obterApiBase({ busca: '', armazenamento, padrao: '' })).toBe(`${url}/`)
  })
  it('ignora ?api= que não seja https', () => {
    expect(obterApiBase({ busca: '?api=javascript:alert(1)', armazenamento: memoria(), padrao: '' })).toBe('/api/')
    expect(urlValida('http://inseguro.com')).toBe(false)
  })
  it('usa a URL do build ou o proxy de desenvolvimento', () => {
    expect(obterApiBase({ busca: '', armazenamento: memoria(), padrao: 'https://x.com/api' })).toBe('https://x.com/api/')
    expect(obterApiBase({ busca: '', armazenamento: null, padrao: undefined })).toBe('/api/')
  })
  it('funciona com armazenamento bloqueado', () => {
    const bloqueado = { getItem: () => { throw new Error('bloqueado') }, setItem: () => { throw new Error('bloqueado') } }
    expect(obterApiBase({ busca: '', armazenamento: bloqueado, padrao: undefined })).toBe('/api/')
  })
})

describe('etapaAtual', () => {
  it('acompanha as fases do processamento', () => {
    expect(etapaAtual('enviando', 0)).toBe(0)
    expect(etapaAtual('processando', 0)).toBe(1)
    expect(etapaAtual('processando', 4)).toBe(3)
    expect(etapaAtual('processando', 99)).toBe(3)
    expect(etapaAtual('concluido', 5)).toBe(4)
    expect(etapaAtual('ocioso', 0)).toBe(-1)
  })
})
