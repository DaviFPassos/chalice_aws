import { describe, expect, it, vi } from 'vitest'
import { aguardarResultado, consultarResultado, enviarImagem, ErroApi } from './api.js'

const BASE = 'https://exemplo.execute-api.sa-east-1.amazonaws.com/api/'

function resposta(status, corpo) {
  return { status, ok: status >= 200 && status < 300, json: async () => corpo }
}

describe('enviarImagem', () => {
  it('envia o corpo binário com o tipo da imagem e devolve o id', async () => {
    const fetchFn = vi.fn().mockResolvedValue(resposta(202, { id: 'abc', status: 'processando' }))
    const blob = new Blob(['x'], { type: 'image/png' })
    await expect(enviarImagem(BASE, blob, { fetchFn })).resolves.toEqual({ id: 'abc', status: 'processando' })
    const [url, opcoes] = fetchFn.mock.calls[0]
    expect(url).toBe(`${BASE}imagens`)
    expect(opcoes.method).toBe('POST')
    expect(opcoes.headers['Content-Type']).toBe('image/png')
    expect(opcoes.body).toBe(blob)
  })

  it('mostra a mensagem da cota quando a API responde 429', async () => {
    const fetchFn = vi.fn().mockResolvedValue(resposta(429, { Message: 'Limite diário de 30 imagens atingido.' }))
    await expect(enviarImagem(BASE, new Blob(['x']), { fetchFn }))
      .rejects.toMatchObject({ status: 429, message: 'Limite diário de 30 imagens atingido.' })
  })

  it('traduz erro 400 para uma mensagem amigável', async () => {
    const fetchFn = vi.fn().mockResolvedValue(resposta(400, { Message: 'BadRequestError' }))
    await expect(enviarImagem(BASE, new Blob(['x']), { fetchFn })).rejects.toThrow(/JPEG ou PNG/)
  })

  it('avisa quando a API está fora do ar', async () => {
    const fetchFn = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(enviarImagem(BASE, new Blob(['x']), { fetchFn })).rejects.toMatchObject({ status: 0 })
  })
})

describe('consultarResultado', () => {
  it('202 significa que ainda está processando', async () => {
    const fetchFn = vi.fn().mockResolvedValue(resposta(202, { status: 'processando' }))
    await expect(consultarResultado(BASE, 'abc', { fetchFn })).resolves.toEqual({ pronto: false })
    expect(fetchFn.mock.calls[0][0]).toBe(`${BASE}imagens/abc`)
  })
})

describe('aguardarResultado', () => {
  const esperar = () => Promise.resolve()

  it('consulta até o resultado ficar pronto', async () => {
    const fetchFn = vi.fn()
      .mockResolvedValueOnce(resposta(202, {}))
      .mockResolvedValueOnce(resposta(202, {}))
      .mockResolvedValueOnce(resposta(200, { status: 'concluido', texto_traduzido: 'Saída' }))
    const aoTentar = vi.fn()
    const dados = await aguardarResultado(BASE, 'abc', { fetchFn, esperar, aoTentar })
    expect(dados.texto_traduzido).toBe('Saída')
    expect(aoTentar).toHaveBeenCalledTimes(3)
  })

  it('lança erro quando o processamento falhou', async () => {
    const fetchFn = vi.fn().mockResolvedValue(resposta(200, { status: 'erro', erro: 'Não foi possível processar a imagem.' }))
    await expect(aguardarResultado(BASE, 'abc', { fetchFn, esperar })).rejects.toThrow('Não foi possível processar')
  })

  it('desiste depois do número máximo de tentativas', async () => {
    const fetchFn = vi.fn().mockResolvedValue(resposta(202, {}))
    await expect(aguardarResultado(BASE, 'abc', { fetchFn, esperar, tentativas: 3 }))
      .rejects.toBeInstanceOf(ErroApi)
    expect(fetchFn).toHaveBeenCalledTimes(3)
  })
})
