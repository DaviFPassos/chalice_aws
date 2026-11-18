# Leitor de Placas com Voz

**Trabalho IV — Desenvolvimento de uma Aplicação Serverless com Serviços de IA da AWS**

Aplicação serverless que recebe a foto de uma placa, monumento ou local com texto em
**árabe, russo ou alemão**, extrai o texto, traduz para o português e devolve um
**áudio narrado**, além da pronúncia do texto no idioma original.

Construída com **AWS Chalice** e implantada no **AWS Lambda**, com arquitetura
**orientada a eventos** e três serviços de IA encadeados: **Amazon Rekognition →
Amazon Translate → Amazon Polly**. A interface é um **front-end em React**.

## Equipe

| Nome | Matrícula |
|---|---|
| Davi Passos | _a preencher_ |
| Rafael Fonseca | _a preencher_ |
| Lucca Melo | _a preencher_ |

## Problema

Turistas, estudantes de intercâmbio e pessoas com deficiência visual têm dificuldade
para entender placas, avisos e inscrições em idiomas e alfabetos diferentes (cirílico,
árabe) ou com caracteres especiais (alemão). A aplicação transforma uma foto em
informação **falada em português**.

## Como funciona

1. O usuário informa o **código de acesso** e envia a foto pelo **front-end em React** (ou
   direto pela API, `POST /imagens`). Fotos grandes de celular são reduzidas no navegador
   antes do envio. Sem o código, a API recusa o envio — assim estranhos não consomem os
   créditos da AWS.
2. A API grava a imagem no **Amazon S3**, e o upload **dispara uma segunda Lambda**
   (evento `s3:ObjectCreated`). O cliente não espera: recebe um `id` na hora.
3. A Lambda encadeia os serviços de IA — a saída de cada um é a entrada do próximo:
   - **Rekognition** extrai o texto (`DetectText`) e descreve a cena (`DetectLabels`).
     No árabe, as palavras são remontadas pela posição na imagem, da direita para a
     esquerda (ver [Resultados](#resultados));
   - o idioma é identificado pelo **alfabeto** do texto (árabe, cirílico ou latino);
   - **Translate** traduz o texto para o português; os rótulos comuns da cena têm
     tradução fixa e só os demais passam pelo Translate;
   - **Polly** gera dois MP3: a **narração em português** (voz Camila) e a
     **pronúncia original** do texto (Vicki para alemão, Tatyana para russo, Zeina para
     árabe).
4. O resultado (JSON + áudios) é salvo no S3 e consultado em `GET /imagens/{id}`. O
   front mostra as etapas, a tradução, o texto original e os players de áudio.

Exemplo real de narração (`testes/imagens/arabe_saida_emergencia.jpg`):
> "Na imagem há: placa, símbolo, sinal de trânsito, primeiros socorros. Foi encontrado
> um texto em árabe. Em português, ele diz: Saída de emergência"

## Arquitetura

Diagrama, componentes, regiões e detalhes do encadeamento em
[`docs/arquitetura.md`](docs/arquitetura.md).

```
Front React (GitHub Pages)
   │  POST /imagens  ·  GET /imagens/{id}
   ▼
API Gateway ──► Lambda api_handler ──► S3  uploads/{id}.jpg
                                        │  evento s3:ObjectCreated
                                        ▼
                Lambda ao_enviar_imagem ──► Rekognition ──► Translate ──► Polly
                                        │
                                        ▼
                S3  resultados/{id}.json  +  audios/{id}/*.mp3
```

## Estrutura do projeto

```
.
├── app.py                       # rotas da API + handler do evento do S3
├── chalicelib/                  # módulos empacotados junto com a Lambda
│   ├── pipeline.py              # encadeamento Rekognition → Translate → Polly
│   ├── visao.py                 # Amazon Rekognition
│   ├── layout.py                # remonta as linhas (ordem e palavras do árabe)
│   ├── traducao.py              # Amazon Translate (+ junção de frases em duas linhas)
│   ├── rotulos.py               # tradução fixa dos rótulos comuns da cena
│   ├── voz.py                   # Amazon Polly
│   ├── idiomas.py               # detecção do idioma pelo alfabeto e vozes do Polly
│   ├── armazenamento.py         # Amazon S3
│   ├── acesso.py                # código de acesso (lido do SSM Parameter Store)
│   ├── cota.py                  # limites diário e mensal de envios (custo zero)
│   ├── clientes.py              # clientes boto3 (por região)
│   └── config.py                # configurações e limites
├── frontend/                    # front-end em React (Vite)
│   ├── src/App.jsx              # tela principal: envio, etapas e resultado
│   ├── src/api.js               # chamadas à API (envio e consulta do resultado)
│   ├── src/imagem.js            # validação e redução da foto no navegador
│   └── src/componentes/         # CodigoAcesso, EnvioImagem, Etapas, Resultado
├── .chalice/
│   ├── config.json              # app_name, variáveis de ambiente, timeouts
│   └── policy-dev.json          # permissões IAM mínimas da Lambda
├── .github/workflows/frontend.yml  # testa e publica o front no GitHub Pages
├── scripts/
│   ├── criar_bucket.sh          # cria o bucket S3 (privado, expiração de 7 dias)
│   ├── definir_codigo_acesso.sh # define ou troca o código de acesso (SSM)
│   ├── limitar_api.sh           # limita a taxa de requisições da API Gateway
│   ├── testar_api.py            # envia imagens à API implantada e salva os resultados
│   ├── gerar_imagens_exemplo.py # gera as placas de exemplo em testes/imagens/
│   └── remover_tudo.sh          # remove a aplicação, o bucket, os logs e o código da AWS
├── tests/                       # testes automatizados do backend (pytest, sem AWS)
├── testes/
│   ├── imagens/                 # 12 imagens de exemplo + LEIAME com o esperado de cada uma
│   └── resultados/              # JSON e MP3 produzidos pela aplicação na AWS
├── docs/
│   ├── arquitetura.md           # projeto de arquitetura
│   └── custos.md                # levantamento de custos e limites de uso
├── requirements.txt             # dependências da Lambda (boto3 recente)
└── requirements-dev.txt         # dependências de desenvolvimento
```

## Pré-requisitos

- **Python 3.12** e **Node.js 22** (ou 20.19+, exigido pelo Vite 7) para o front-end
- **AWS CLI** configurada (`aws configure`) na região `sa-east-1`
- Conta AWS no **Paid Plan**: o Amazon Translate não está disponível no Free Plan (o uso
  continua dentro dos créditos e do teste gratuito do Translate — ver
  [Custos e segurança](#custos-e-segurança))
- Permissões do usuário IAM que faz o deploy:
  - **Deploy:** Lambda, API Gateway, IAM (criar role e `iam:PassRole`), S3 (criar bucket,
    `s3:PutBucketNotification`), CloudWatch Logs e SSM (`ssm:PutParameter` e
    `ssm:DeleteParameter` em `/leitor-placas/*`);
  - **Testes manuais contra a AWS:** `rekognition:DetectText`, `rekognition:DetectLabels`,
    `translate:TranslateText` e `polly:SynthesizeSpeech`.

> **Nunca** compartilhe chaves de acesso entre os integrantes. Cada pessoa usa a própria
> conta ou um usuário IAM próprio. As credenciais ficam em `~/.aws/`, fora do repositório.

## Implantação

```bash
# 1. Ambiente
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 2. Bucket S3 (uma única vez). O nome está em .chalice/config.json -> BUCKET_NAME.
#    Nomes de bucket são globais: se já existir, troque o nome no config.json e no
#    .chalice/policy-dev.json.
./scripts/criar_bucket.sh

# 3. Código de acesso (guardado no SSM, nunca no repositório). Gera um código aleatório
#    e o mostra na tela: compartilhe só com a equipe e o professor.
./scripts/definir_codigo_acesso.sh

# 4. Deploy (cria as duas Lambdas, a API Gateway, as roles e a notificação do bucket)
chalice deploy
./scripts/limitar_api.sh   # limita a API a 1 req/s (rode após cada deploy)
chalice url                # URL da API
```

**Front-end no GitHub Pages** (uma única vez): em *Settings → Pages → Build and
deployment*, escolha **Source: GitHub Actions**. A partir daí, o workflow
`.github/workflows/frontend.yml` testa e publica o front a cada push na `main` que altere
`frontend/`, em https://davifpassos.github.io/chalice_aws/.

**Remover tudo da AWS** (após os testes e a avaliação):

```bash
./scripts/remover_tudo.sh
```

## Execução

### Front-end (React)

**Local (desenvolvimento):**

```bash
cd frontend
npm install
cp .env.example .env.local     # preencha API_PROXY_TARGET com a URL da API, sem o /api/
npm run dev                    # http://localhost:5173
```

O Vite repassa as chamadas `/api` para a API implantada, então não é preciso liberar CORS
para `localhost`. Informe o código de acesso, escolha uma imagem de `testes/imagens/` e
clique em "Ler e traduzir". O código pode ficar lembrado no navegador.

**GitHub Pages:** cada `chalice deploy` feito depois de um `remover_tudo.sh` gera uma
URL de API nova. Abra o site uma vez com `?api=<URL de chalice url>` (fica salva no
navegador) ou atualize a variável `API_URL` do repositório (*Settings → Secrets and
variables → Actions → Variables*) e rode o workflow. Em produção, a API só aceita chamadas
de navegador vindas do GitHub Pages (`CORS_ORIGIN` em `.chalice/config.json`). Com a API
fora do ar, o site mostra um aviso.

### API REST

```bash
API=$(chalice url)
CODIGO=XXXX-XXXX-XXXX   # código de acesso definido por scripts/definir_codigo_acesso.sh

# Enviar uma foto (JPEG ou PNG, até 5 MB) -> 202 {"id": "...", "status": "processando"}
curl -X POST -H "X-Codigo-Acesso: $CODIGO" -H 'Content-Type: image/jpeg' \
     --data-binary @testes/imagens/russo_metro.jpg ${API}imagens

# Consultar o resultado -> 202 enquanto processa; 200 com texto, tradução, cena e áudios
curl -H "X-Codigo-Acesso: $CODIGO" ${API}imagens/<id>
```

| Método | Rota | Resposta |
|---|---|---|
| GET | `/` | Status da API e link para o front-end |
| POST | `/imagens` | `202` com o `id` · `400` formato inválido ou mais de 5 MB · `401` código de acesso ausente ou errado · `429` limite diário/mensal atingido |
| GET | `/imagens/{id}` | `202` processando · `200` resultado · `401` código errado · `404` inexistente · `400` id inválido |

`POST /imagens` e `GET /imagens/{id}` exigem o cabeçalho `X-Codigo-Acesso`. Sem o código
configurado no SSM, a API responde `503` a tudo (falha fechada).

Resultado (`200`), resumido:

```json
{
  "id": "3f2a...",
  "status": "concluido",
  "idioma_detectado": "ar",
  "texto_original": "مخرج الطوارئ",
  "linhas": [{"texto": "مخرج الطوارئ", "confianca": 83.6}],
  "texto_traduzido": "Saída de emergência",
  "cena": [{"rotulo": "Sign", "rotulo_pt": "placa", "confianca": 100.0}],
  "narracao": "Na imagem há: placa, símbolo, ... Em português, ele diz: Saída de emergência",
  "audios_url": {
    "narracao_pt": "https://...s3...narracao_pt.mp3?...",
    "pronuncia_original": "https://...s3...pronuncia_original.mp3?..."
  }
}
```

Os links dos áudios são temporários (1 hora). Logs: `chalice logs --name ao_enviar_imagem`.

## Testes

**Automatizados (sem AWS e sem custo):**

```bash
python -m pytest -v               # backend: 65 testes (serviços simulados em tests/conftest.py)
cd frontend && npm test           # front-end: 21 testes (Vitest)
```

| Área | O que é testado |
|---|---|
| Leitura do texto | Ordem e junção das palavras em árabe usando as **posições reais** devolvidas pelo Rekognition; texto inclinado; descarte de baixa confiança e de símbolos soltos |
| Idioma e tradução | Detecção pelo alfabeto (inclusive placa bilíngue), junção de frases em duas linhas, rótulos com tradução fixa |
| Fluxo completo | Placas em alemão, russo e árabe com a voz certa de cada idioma, imagem sem texto, disparo pelo evento do S3, erro sem expor dados da conta |
| API | Rotas, validação de formato e tamanho, CORS restrito ao front, cota diária e mensal (`429`) |
| Código de acesso | `401` sem gravar nem gastar cota, maiúsculas/espaços ignorados, `503` sem código configurado, cache do SSM |
| Front-end | Chamadas à API com o código e mensagens de erro, espera do resultado, redução da imagem, URL da API, código lembrado no navegador |

**Na AWS (aplicação implantada):** `testes/imagens/` traz **12 imagens de exemplo**
(alemão, russo e árabe, uma bilíngue, uma sem texto e uma de baixa qualidade), geradas
por `scripts/gerar_imagens_exemplo.py`. O texto e a tradução esperada de cada uma estão em
[`testes/imagens/LEIAME.md`](testes/imagens/LEIAME.md). Acrescente fotos reais na mesma
pasta e rode:

```bash
export CODIGO_ACESSO='XXXX-XXXX-XXXX'   # ou: source segredos/codigo-acesso.env
python scripts/testar_api.py $(chalice url)
```

Para cada imagem, o script grava em `testes/resultados/` o JSON da resposta e os MP3.

## Resultados

Teste na AWS em 18/11/2026 com as 12 imagens de exemplo. Respostas completas (JSON) e
áudios (MP3) em [`testes/resultados/`](testes/resultados/).

| Imagem | Texto extraído (Rekognition) | Tradução (Translate) | Avaliação |
|---|---|---|---|
| `alemao_saida_emergencia` | Notausgang | saída de emergência | ✅ |
| `alemao_placa_rua` | Unter den Linden / Brandenburger Tor | Unter den Linden / Portão de Brandemburgo | ✅ nome da rua mantido |
| `alemao_proibido_fumar` | Rauchen verboten / Bitte nicht rauchen | Proibido fumar / Por favor, não fume | ✅ |
| `russo_metro` | Выход в город / Красная площадь | Saia para a cidade / Praça Vermelha | ⚠️ "Saia" (imperativo) em vez de "Saída" |
| `russo_museu` | Государственный / исторический музей | Museu Histórico do Estado | ✅ linhas da mesma frase unidas |
| `russo_cuidado_piso` | Скользкий пол | Piso escorregadio | ⚠️ "Осторожно!" não foi lido |
| `arabe_saida_emergencia` | مخرج الطوارئ | Saída de emergência | ✅ |
| `arabe_museu` | المتحف المصري | O Museu Egípcio | ✅ |
| `arabe_proibido_fumar` | ممنوع التدخين | Proibido fumar | ✅ |
| `arabe_bilingue_rua` | شارع التحرير / Tahrir Street | Rua Tahrir / Rua Tahrer | ✅ árabe correto · ⚠️ inglês traduzido como árabe |
| `sem_texto_monumento` | (nenhum) | — | ✅ narração descreve a cena (edifício, templo, pilar, Partenon…) |
| `baixa_qualidade_alemao` | den Linden / Unter / Brandenburger Tor | den Linden / Abaixo / Portão de Brandemburgo | ⚠️ texto inclinado e desfocado lido em pedaços |

Tempo por imagem (envio → resultado pronto): ~4 s; ~10 s na primeira chamada, quando a
Lambda inicializa.

**O que os testes revelaram e foi corrigido:**

| Problema | Antes | Correção |
|---|---|---|
| Árabe fora de ordem e com palavras cortadas | "مخرج الطوارئ" chegava como "رئ / الطوا / مخرج" → *Veja / Altawa / ventilação* | O Rekognition devolve as palavras árabes da esquerda para a direita e corta a palavra nas letras que não se ligam à seguinte (ا د ر …). `layout.py` remonta as palavras pela posição, da direita para a esquerda, e une os pedaços por regra linguística. As 4 placas em árabe passaram a sair corretas |
| Rótulos da cena | "Sign" → *assine* | Tradução fixa dos rótulos comuns (`rotulos.py`) |
| Frase quebrada em duas linhas | *De propriedade do Estado / museu histórico* | Linhas que continuam a frase são traduzidas juntas |
| Símbolos soltos | O "!" de um ícone entrava na narração | Linhas sem letras são descartadas |

## Limitações

- **Idiomas:** o Rekognition `DetectText` foi projetado para inglês, árabe, russo, alemão,
  francês, italiano, português e espanhol, e lê até **100 palavras** por imagem. Não lê
  mandarim, japonês ou tailandês. Como o idioma é detectado pelo alfabeto, textos em
  outros idiomas latinos (inglês, francês…) são tratados como alemão.
- **Palavras sem contexto** podem ganhar outro sentido na tradução ("Выход" → "Saia").
- **Letras parecidas:** o Rekognition pode confundir cirílico com latino ("Осторожно!"
  foi lido como "OctopoXHO!", com 21% de confiança, e descartado pelo filtro de 80%).
- **Placas bilíngues:** o trecho em outro idioma é traduzido como se fosse do idioma
  principal ("Tahrir Street" → "Rua Tahrer").
- **Árabe:** a junção dos pedaços de palavra é uma regra heurística, validada com as
  imagens de exemplo; fotos reais podem trazer casos não previstos.
- **Monumentos:** o Rekognition não identifica monumentos **pelo nome**, só a categoria
  ("monumento", "templo", "torre").
- **Qualidade da foto:** imagens tremidas, escuras ou com texto inclinado reduzem a
  precisão.

## Vídeo de demonstração

_Link do vídeo:_ a definir.

## Custos e segurança

- **Código de acesso:** só quem tem o código (equipe e professor) consegue enviar fotos
  ou consultar resultados. O código fica no **AWS SSM Parameter Store** como
  `SecureString` (criptografado), nunca no repositório; é comparado em tempo constante, e
  um código errado recebe `401` antes de qualquer gravação ou consumo de cota. Com 12
  caracteres aleatórios e o limite de 1 req/s, adivinhá-lo é inviável. Para trocar:
  `./scripts/definir_codigo_acesso.sh` (vale em até 5 minutos).
- O bucket é **privado** e os objetos expiram em **7 dias**. Os áudios são entregues por
  URLs temporárias.
- A API valida formato (assinatura JPEG/PNG) e tamanho (5 MB) antes de gravar no S3, e
  libera CORS só para o endereço do front-end no GitHub Pages (`CORS_ORIGIN`).
- Erros de processamento retornam uma mensagem genérica; os detalhes (que podem conter
  ARNs e o ID da conta) ficam só no CloudWatch Logs.
- A Lambda usa uma política IAM mínima (`.chalice/policy-dev.json`), sem permissões
  geradas automaticamente.
- **Uso sem custo:** cada imagem consome créditos da AWS (Rekognition, Translate e Polly).
  Além do código de acesso, a aplicação tem limites definidos a partir de um levantamento
  de preços ([`docs/custos.md`](docs/custos.md)), que valem mesmo para quem tem o código:

  | Limite | Valor |
  |---|---|
  | Envios por dia / por mês | **30 / 300 imagens** (acima disso, `POST /imagens` responde `429` e a imagem não é gravada) |
  | Taxa de requisições da API | 1 req/s (`scripts/limitar_api.sh`) |
  | Texto enviado ao Translate / narração enviada ao Polly | 1.000 / 1.500 caracteres |

  Mesmo com abuso máximo, o gasto fica em ~25% dos créditos por mês, e o Translate em
  ~17% do teste gratuito. O uso real esperado é ~1% dos créditos.
- Configure um alerta de **US$ 1** no **AWS Budgets** e rode `./scripts/remover_tudo.sh`
  depois dos testes e da avaliação.

## Como contribuir

- Crie uma branch a partir da `main` para cada mudança (`feat/...`, `fix/...`) e abra um
  Pull Request explicando o que muda e por quê.
- Rode `python -m pytest` e `cd frontend && npm test` antes de enviar.
- Nunca versione credenciais, arquivos `.env` ou a pasta `.chalice/deployed/` (já estão
  no `.gitignore`). O repositório é público e tem *push protection* contra segredos.
- Guarde o código de acesso e outros segredos locais na pasta `segredos/` (por exemplo,
  `segredos/codigo-acesso.env` com `export CODIGO_ACESSO='...'`). Ela é ignorada pelo
  `.gitignore` e nunca vai para o repositório.

## Histórico

O tutorial [REST API do Chalice](https://aws.github.io/chalice/tutorials/basicrestapi.html),
usado como ponto de partida, está preservado na tag
[`tutorial-basicrestapi`](https://github.com/DaviFPassos/chalice_aws/tree/tutorial-basicrestapi).
