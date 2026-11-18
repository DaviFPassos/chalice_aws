# Leitor de Placas com Voz

**Trabalho IV — Desenvolvimento de uma Aplicação Serverless com Serviços de IA da AWS**

Aplicação serverless que recebe a foto de uma placa, monumento ou local com texto em
**árabe, russo ou alemão**, extrai o texto, traduz para o português e devolve um
**áudio narrado**, além da pronúncia do texto no idioma original.

Construída com **AWS Chalice** e implantada no **AWS Lambda**, com arquitetura
**orientada a eventos** e três serviços de IA encadeados: **Amazon Rekognition →
Amazon Translate → Amazon Polly**.

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

1. O usuário envia a foto pelo **front-end em React** (ou direto pela API, `POST /imagens`).
   Fotos grandes de celular são reduzidas no navegador antes do envio.
2. A imagem é gravada no **Amazon S3**, e o upload **dispara uma Lambda** (evento
   `s3:ObjectCreated`).
3. A Lambda encadeia os serviços de IA:
   - **Rekognition** extrai o texto da imagem (`DetectText`) e descreve a cena
     (`DetectLabels`: "monumento", "igreja", "rua"...);
   - o idioma é identificado pelo **alfabeto** do texto (árabe, cirílico ou latino);
   - **Translate** traduz o texto e a descrição da cena para o português;
   - **Polly** gera dois MP3: a **narração em português** (voz Camila) e a
     **pronúncia original** do texto (voz do idioma detectado: Vicki, Tatyana ou Zeina).
4. O resultado (JSON + áudios) é salvo no S3 e consultado em `GET /imagens/{id}`. O
   front mostra o texto original, a tradução e os players de áudio.

Exemplo de narração gerada:
> "Na imagem há: monumento, arquitetura, céu. Foi encontrado um texto em alemão. Em
> português, ele diz: Portão de Brandemburgo"

## Arquitetura

Diagrama, componentes, regiões e detalhes do encadeamento em
[`docs/arquitetura.md`](docs/arquitetura.md).

```
Front React (GitHub Pages)
   │ POST /imagens · GET /imagens/{id}
   ▼
API Gateway → Lambda (api_handler) → S3 uploads/
                                                  │ evento s3:ObjectCreated
                                                  ▼
                       Lambda (ao_enviar_imagem) → Rekognition → Translate → Polly
                                                  │
                                                  ▼
                              S3 resultados/ + audios/ → GET /imagens/{id}
```

## Estrutura do projeto

```
.
├── app.py                       # rotas da API + handler do evento do S3
├── frontend/                    # front-end em React (Vite), publicado no GitHub Pages
│   ├── src/App.jsx              # tela principal: envio, etapas e resultado
│   ├── src/api.js               # chamadas à API (envio e consulta do resultado)
│   ├── src/imagem.js            # validação e redução da foto no navegador
│   └── src/componentes/         # EnvioImagem, Etapas, Resultado
├── .github/workflows/frontend.yml  # testa e publica o front no GitHub Pages
├── chalicelib/                  # módulos empacotados junto com a Lambda
│   ├── pipeline.py              # encadeamento Rekognition → Translate → Polly
│   ├── visao.py                 # Amazon Rekognition
│   ├── traducao.py              # Amazon Translate
│   ├── voz.py                   # Amazon Polly
│   ├── armazenamento.py         # Amazon S3
│   ├── cota.py                  # limites diário e mensal de envios (custo zero)
│   ├── idiomas.py               # nomes dos idiomas e vozes do Polly
│   ├── clientes.py              # clientes boto3 (por região)
│   └── config.py                # configurações e limites
├── .chalice/
│   ├── config.json              # app_name, variáveis de ambiente, timeouts
│   └── policy-dev.json          # permissões IAM mínimas da Lambda
├── scripts/
│   ├── criar_bucket.sh          # cria o bucket S3 (privado, expiração de 7 dias)
│   ├── limitar_api.sh           # limita a taxa de requisições da API Gateway
│   ├── testar_api.py            # envia imagens à API implantada e salva os resultados
│   └── remover_tudo.sh          # remove a aplicação e o bucket da AWS
├── tests/                       # testes automatizados (pytest, sem acessar a AWS)
├── testes/
│   ├── imagens/                 # imagens de entrada usadas nos testes
│   └── resultados/              # JSON e MP3 produzidos pela aplicação
├── docs/arquitetura.md          # projeto de arquitetura
├── docs/custos.md               # levantamento de custos e limites de uso
├── requirements.txt             # dependências da Lambda (boto3 recente, para escrita condicional no S3)
└── requirements-dev.txt         # dependências de desenvolvimento
```

## Pré-requisitos

- Python 3.12
- AWS CLI configurada (`aws configure`) na região `sa-east-1`
- Permissões do usuário IAM que faz o deploy:
  - **Deploy:** Lambda, API Gateway, IAM (criar role e `iam:PassRole`), S3 (criar bucket e
    `s3:PutBucketNotification`) e CloudWatch Logs;
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

# 2. Bucket S3 (uma única vez). O nome está em .chalice/config.json -> BUCKET_NAME;
#    nomes de bucket são globais: se já existir, troque o nome no config.json e no
#    .chalice/policy-dev.json.
./scripts/criar_bucket.sh

# 3. Deploy (cria as duas Lambdas, a API Gateway, a role e a notificação do bucket)
chalice deploy
./scripts/limitar_api.sh   # limita a API a 1 req/s (rode após cada deploy)
chalice url                # URL da API
```

## Execução

### Front-end (React)

**Publicado:** https://davifpassos.github.io/chalice_aws/ (GitHub Pages, gratuito). Depois de
um novo `chalice deploy`, a URL da API muda: abra o site uma vez com
`?api=<URL de chalice url>` (fica salva no navegador) ou atualize a variável `API_URL` do
repositório (*Settings → Secrets and variables → Actions → Variables*) e rode o workflow.
Com a API fora do ar, o site mostra um aviso.

**Local:**

```bash
cd frontend
npm install
cp .env.example .env.local     # preencha API_PROXY_TARGET com a URL da API (sem /api/)
npm run dev                    # http://localhost:5173
```

O Vite repassa as chamadas `/api` para a API implantada, então não é preciso liberar CORS
para `localhost`. Em produção, a API só aceita chamadas de navegador vindas do GitHub Pages
(`CORS_ORIGIN` em `.chalice/config.json`).

### API REST

```bash
API=$(chalice url)

# Enviar uma foto (JPEG ou PNG, até 5 MB) -> 202 {"id": "...", "status": "processando"}
curl -X POST -H 'Content-Type: image/jpeg' --data-binary @testes/imagens/foto.jpg ${API}imagens

# PNG funciona igual, com Content-Type: image/png

# Consultar o resultado -> 202 enquanto processa; 200 com texto, tradução, cena e áudios
curl ${API}imagens/<id>
```

| Método | Rota | Resposta |
|---|---|---|
| GET | `/` | Status da API e link para o front-end |
| POST | `/imagens` | `202` com o `id`; `400` se o formato for inválido ou a imagem passar de 5 MB; `429` se o limite diário/mensal foi atingido |
| GET | `/imagens/{id}` | `202` processando · `200` resultado · `404` inexistente · `400` id inválido |

Resultado (`200`):

```json
{
  "id": "3f2a...",
  "status": "concluido",
  "idioma_detectado": "de",
  "texto_original": "Brandenburger Tor",
  "texto_traduzido": "Portão de Brandemburgo",
  "cena": [{"rotulo": "Monument", "rotulo_pt": "monumento", "confianca": 95.0}],
  "narracao": "Na imagem há: monumento. Foi encontrado um texto em alemão. ...",
  "audios_url": {
    "narracao_pt": "https://...s3...narracao_pt.mp3?...",
    "pronuncia_original": "https://...s3...pronuncia_original.mp3?..."
  }
}
```

Os links dos áudios são temporários (1 hora). Logs: `chalice logs --name ao_enviar_imagem`.

## Testes

**Automatizados (sem AWS e sem custo):** os serviços são substituídos por versões falsas
em `tests/conftest.py`.

```bash
python -m pytest -v               # backend
cd frontend && npm test           # front-end (Vitest): chamadas à API, cota, redução de imagem
```

Cobrem: detecção do idioma pelo alfabeto (inclusive placas bilíngues), placas em alemão,
russo e árabe (escolha da voz correta), texto com baixa
confiança, imagem sem texto, validação de envio (formato e tamanho), rotas da
API, disparo pelo evento do S3 e registro de erro no processamento.

**Na AWS (aplicação implantada):** coloque as fotos em `testes/imagens/` (sugestões em
[`testes/imagens/LEIAME.md`](testes/imagens/LEIAME.md)) e rode:

```bash
python scripts/testar_api.py $(chalice url)
```

Para cada imagem, o script grava em `testes/resultados/` o JSON da resposta e os MP3
gerados.

## Resultados

_A preencher após os testes na AWS: tabela com imagem, idioma detectado, texto extraído,
tradução e observações (acertos, erros e limites)._

## Vídeo de demonstração

_Link do vídeo:_ a definir.

## Limitações

- O Rekognition `DetectText` lê até **100 palavras** por imagem e foi projetado para
  inglês, árabe, russo, alemão, francês, italiano, português e espanhol. Não lê
  mandarim, japonês ou tailandês.
- No árabe (escrito da direita para a esquerda), a ordem das linhas retornada pode variar.
- O Rekognition não identifica monumentos **pelo nome**, apenas a categoria ("monumento",
  "igreja", "torre").
- Fotos tremidas, escuras ou com texto inclinado reduzem a precisão.

## Custos e segurança

- O bucket é **privado** e os objetos expiram em **7 dias**. Os áudios são entregues por
  URLs temporárias.
- A API valida formato (assinatura JPEG/PNG) e tamanho (5 MB) antes de gravar no S3, e
  libera CORS só para o endereço do front-end no GitHub Pages (`CORS_ORIGIN`).
- Erros de processamento retornam uma mensagem genérica; os detalhes (que podem conter
  ARNs e o ID da conta) ficam só no CloudWatch Logs.
- A Lambda usa uma política IAM mínima (`.chalice/policy-dev.json`), sem permissões
  geradas automaticamente.
- **Uso sem custo:** a API é pública e cada imagem consome créditos da AWS (Rekognition,
  Translate e Polly). Para que o projeto nunca gere cobrança, a aplicação tem limites
  definidos a partir de um levantamento de preços ([`docs/custos.md`](docs/custos.md)):

  | Limite | Valor |
  |---|---|
  | Envios por dia / por mês | **30 / 300 imagens** (acima disso, `POST /imagens` responde `429`) |
  | Taxa de requisições da API | 1 req/s (`scripts/limitar_api.sh`) |
  | Texto enviado ao Translate / narração enviada ao Polly | 1.000 / 1.500 caracteres |

  Mesmo com abuso máximo, o gasto fica em ~25% dos créditos por mês, e o Translate
  em ~17% do teste gratuito. O uso real esperado é ~1% dos créditos.
- Configure um alerta de **US$ 1** no **AWS Budgets** e remova tudo após a avaliação:

```bash
./scripts/remover_tudo.sh
```

## Histórico

O tutorial [REST API do Chalice](https://aws.github.io/chalice/tutorials/basicrestapi.html),
usado como ponto de partida, está preservado na tag
[`tutorial-basicrestapi`](https://github.com/DaviFPassos/chalice_aws/tree/tutorial-basicrestapi).
