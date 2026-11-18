# Imagens de teste

Imagens usadas para testar a aplicação (JPEG ou PNG, até 5 MB; no front-end, fotos
maiores são reduzidas automaticamente). O script `scripts/testar_api.py` envia todas as
imagens desta pasta para a API implantada e grava as respostas em `testes/resultados/`.

## Imagens de exemplo incluídas

Geradas por `scripts/gerar_imagens_exemplo.py` (sintéticas e autorais, sem restrição de
uso). Para recriá-las: `python scripts/gerar_imagens_exemplo.py`.

| Arquivo | Idioma | Texto na placa | Tradução esperada | O que testa |
|---|---|---|---|---|
| `alemao_saida_emergencia.jpg` | Alemão | Notausgang | Saída de emergência | Palavra composta, placa com seta |
| `alemao_placa_rua.jpg` | Alemão | Unter den Linden / Brandenburger Tor | Sob as tílias / Portão de Brandemburgo | Nomes próprios (rua e monumento) |
| `alemao_proibido_fumar.jpg` | Alemão | Rauchen verboten / Bitte nicht rauchen | Proibido fumar / Por favor, não fume | Duas linhas, ícone ao lado |
| `russo_metro.jpg` | Russo | Выход в город / Красная площадь | Saída para a cidade / Praça Vermelha | Alfabeto cirílico, placa de metrô |
| `russo_museu.jpg` | Russo | Государственный исторический музей | Museu Histórico Estatal | Frase quebrada em duas linhas |
| `russo_cuidado_piso.jpg` | Russo | Осторожно! / Скользкий пол | Cuidado! / Piso escorregadio | Pontuação, placa de aviso |
| `arabe_saida_emergencia.jpg` | Árabe | مخرج الطوارئ | Saída de emergência | Escrita da direita para a esquerda |
| `arabe_museu.jpg` | Árabe | المتحف المصري | O Museu Egípcio | Ponto turístico |
| `arabe_bilingue_rua.jpg` | Árabe + inglês | شارع التحرير / Tahrir Street | Rua Tahrir | Placa bilíngue (o árabe deve prevalecer) |
| `arabe_proibido_fumar.jpg` | Árabe | ممنوع التدخين | Proibido fumar | Árabe com ícone ao lado |
| `sem_texto_monumento.jpg` | — | (sem texto) | — | Só a descrição da cena; narração deve dizer que não há texto |
| `baixa_qualidade_alemao.jpg` | Alemão | Unter den Linden (inclinada, desfocada, escura) | — | Limites do Rekognition |

As traduções esperadas são referências; o Translate pode variar a redação (ex.: "Saia
para a cidade" em vez de "Saída para a cidade"). Diferenças assim são bons exemplos para
a seção de limitações e para o vídeo.

## Fotos reais (recomendado para a entrega)

Imagens sintéticas são ótimas para testes reproduzíveis, mas a avaliação valoriza
**diversidade dos dados**. Acrescentem fotos reais, por exemplo:

| Sugestão | O que demonstra |
|---|---|
| Placa de rua ou monumento na Alemanha | Texto real com perspectiva e iluminação natural |
| Placa do metrô de Moscou | Cirílico em foto real |
| Placa de rua ou loja em árabe (Cairo, Dubai) | Ordem das linhas em árabe em foto real |
| Foto tremida, escura ou de longe | Limites do serviço |

**Direitos de imagem:** use fotos próprias ou com licença livre (por exemplo, do
[Wikimedia Commons](https://commons.wikimedia.org/)) e registre fonte e licença abaixo,
porque o repositório é público.

| Arquivo | Fonte / autor | Licença |
|---|---|---|
| (imagens `alemao_*`, `russo_*`, `arabe_*`, `sem_texto_*`, `baixa_qualidade_*`) | Geradas por `scripts/gerar_imagens_exemplo.py` | Autorais da equipe |
