export const IDIOMAS = {
  ar: { nome: 'Árabe', bandeira: 'ع', lang: 'ar' },
  ru: { nome: 'Russo', bandeira: 'Я', lang: 'ru' },
  de: { nome: 'Alemão', bandeira: 'Ä', lang: 'de' },
}

export function infoIdioma(codigo) {
  return IDIOMAS[codigo] || { nome: codigo || 'Não identificado', bandeira: '?', lang: undefined }
}
