// Preparo da imagem no navegador antes do envio.
// Fotos de celular costumam ter 3–8 MB e mais de 4000 px; a API aceita até 5 MB.
// Imagens grandes são reduzidas para no máximo 2000 px no maior lado (suficiente para
// o Rekognition ler placas) e recomprimidas em JPEG.

export const TIPOS_ACEITOS = ['image/jpeg', 'image/png']
export const TAMANHO_MAXIMO = 5 * 1024 * 1024
export const LADO_MAXIMO = 2000
const QUALIDADE_JPEG = 0.85

export function validarTipo(arquivo) {
  if (!arquivo) return 'Escolha uma imagem.'
  if (!TIPOS_ACEITOS.includes(arquivo.type)) return 'Formato não suportado: use JPEG ou PNG.'
  return null
}

export function calcularDimensoes(largura, altura, ladoMaximo = LADO_MAXIMO) {
  const maior = Math.max(largura, altura)
  if (maior <= ladoMaximo) return { largura, altura, reduzir: false }
  const escala = ladoMaximo / maior
  return {
    largura: Math.round(largura * escala),
    altura: Math.round(altura * escala),
    reduzir: true,
  }
}

export function precisaPreparar(arquivo, dimensoes) {
  return arquivo.size > TAMANHO_MAXIMO || dimensoes.reduzir
}

export async function prepararImagem(arquivo) {
  const erro = validarTipo(arquivo)
  if (erro) throw new Error(erro)

  const bitmap = await createImageBitmap(arquivo)
  const dimensoes = calcularDimensoes(bitmap.width, bitmap.height)
  if (!precisaPreparar(arquivo, dimensoes)) {
    bitmap.close?.()
    return arquivo
  }

  const canvas = document.createElement('canvas')
  canvas.width = dimensoes.largura
  canvas.height = dimensoes.altura
  canvas.getContext('2d').drawImage(bitmap, 0, 0, dimensoes.largura, dimensoes.altura)
  bitmap.close?.()

  const blob = await new Promise((ok) => canvas.toBlob(ok, 'image/jpeg', QUALIDADE_JPEG))
  if (!blob) throw new Error('Não foi possível processar a imagem.')
  if (blob.size > TAMANHO_MAXIMO) throw new Error('A imagem continua maior que 5 MB após a redução.')
  return blob
}
