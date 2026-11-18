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

1. O usuário envia a foto pela página web ou pela API (`POST /imagens`).
2. A imagem é gravada no **Amazon S3**, e o upload **dispara uma Lambda** (evento
   `s3:ObjectCreated`).
3. A Lambda encadeia os serviços de IA:
   - **Rekognition** extrai o texto da imagem (`DetectText`) e descreve a cena
     (`DetectLabels`: "monumento", "igreja", "rua"...);
   - **Translate** detecta o idioma automaticamente e traduz o texto e a descrição da
     cena para o português;
   - **Polly** gera dois MP3: a **narração em português** (voz Camila) e a
     **pronúncia original** do texto (voz do idioma detectado: Vicki, Tatyana ou Zeina).
4. O resultado (JSON + áudios) é salvo no S3 e consultado em `GET /imagens/{id}`.

Exemplo de narração gerada:
> "Na imagem há: monumento, arquitetura, céu. Foi encontrado um texto em alemão. Em
> português, ele diz: Portão de Brandemburgo"

## Arquitetura

Diagrama, componentes, regiões e detalhes do encadeamento em
[`docs/arquitetura.md`](docs/arquitetura.md).

```
Usuário → API Gateway → Lambda (api_handler) → S3 uploads/
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
├── chalicelib/                  # módulos empacotados junto com a Lambda
│   ├── pipeline.py              # encadeamento Rekognition → Translate → Polly
│   ├── visao.py                 # Amazon Rekognition
│   ├── traducao.py              # Amazon Translate
│   ├── voz.py                   # Amazon Polly
│   ├── armazenamento.py         # Amazon S3
│   ├── idiomas.py               # nomes dos idiomas e vozes do Polly
│   ├── clientes.py              # clientes boto3 (por região)
│   ├── config.py                # configurações e limites
│   └── pagina.py                # página web da demonstração
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
├── requirements.txt             # dependências da Lambda (vazio: boto3 já vem no runtime)
└── requirements-dev.txt         # dependências de desenvolvimento
```

## Pré-requisitos

- Python 3.12
- AWS CLI configurada (`aws configure`) na região `sa-east-1`
- Permissões do usuário IAM que faz o deploy:
  - **Deploy:** Lambda, API Gateway, IAM (criar role e `iam:PassRole`), S3 (criar bucket e
    `s3:PutBucketNotification`) e CloudWatch Logs;
  - **Testes manuais contra a AWS:** `rekognition:DetectText`, `rekognition:DetectLabels`,
    `translate:TranslateText`, `comprehend:DetectDominantLanguage` e
    `polly:SynthesizeSpeech`.

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
./scripts/limitar_api.sh   # limita a API a 2 req/s (rode após cada deploy)
chalice url                # URL da API
```

## Execução

**Página web:** abra no navegador a URL exibida por `chalice url`, escolha uma foto e
clique em "Ler e traduzir".

**API REST:**

```bash
API=$(chalice url)

# Enviar uma foto (JPEG ou PNG, até 5 MB) -> 202 {"id": "...", "status": "processando"}
curl -X POST -H 'Content-Type: image/jpeg' --data-binary @testes/imagens/foto.jpg ${API}imagens

# Alternativa em JSON com base64
curl -X POST -H 'Content-Type: application/json' \
     -d "{\"imagem_base64\": \"$(base64 -w0 foto.png)\"}" ${API}imagens

# Consultar o resultado -> 202 enquanto processa; 200 com texto, tradução, cena e áudios
curl ${API}imagens/<id>
```

| Método | Rota | Resposta |
|---|---|---|
| GET | `/` | Página web da aplicação |
| POST | `/imagens` | `202` com o `id`; `400` se o formato for inválido ou a imagem passar de 5 MB |
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
python -m pytest -v
```

Cobrem: placas em alemão, russo e árabe (escolha da voz correta), texto com baixa
confiança, imagem sem texto, validação de envio (formato, tamanho, base64), rotas da
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
  não habilita CORS: só a própria página da aplicação a usa pelo navegador.
- Erros de processamento retornam uma mensagem genérica; os detalhes (que podem conter
  ARNs e o ID da conta) ficam só no CloudWatch Logs.
- A Lambda usa uma política IAM mínima (`.chalice/policy-dev.json`), sem permissões
  geradas automaticamente.
- A API é pública e cada imagem gera chamadas pagas ao Rekognition, Translate e Polly.
  Por isso `scripts/limitar_api.sh` limita a taxa de requisições. Configure também um
  alerta no **AWS Budgets** e remova tudo após a avaliação:

```bash
./scripts/remover_tudo.sh
```

## Histórico

O tutorial [REST API do Chalice](https://aws.github.io/chalice/tutorials/basicrestapi.html),
usado como ponto de partida, está preservado na tag
[`tutorial-basicrestapi`](https://github.com/DaviFPassos/chalice_aws/tree/tutorial-basicrestapi).
