# Custos e limites de uso

Objetivo: usar a aplicação durante todo o trabalho **sem gerar cobrança**, ou seja,
consumindo apenas parte dos créditos gratuitos da AWS e o teste gratuito do Translate,
mesmo que a API pública seja usada por terceiros.

_Levantamento feito em novembro de 2026, nas páginas oficiais de preços da AWS (links no
fim). Preços mudam; confira antes de ampliar os limites._

## 1. O que é gratuito para uma conta criada depois de 15/07/2025

Contas novas usam o modelo de **créditos** (US$ 100 na criação, e até US$ 100 a mais
explorando serviços). Nesse modelo, a maioria dos serviços **não tem mais cota gratuita
própria**: o uso é descontado dos créditos.

| Serviço | Oferta gratuita | Depois disso |
|---|---|---|
| **Amazon Translate** | **2 milhões de caracteres/mês por 12 meses**, só no **Paid Plan** (indisponível no Free Plan) | US$ 15 por milhão de caracteres |
| **Amazon Polly** | Descontado dos créditos | Neural: US$ 16/milhão · Standard: US$ 4/milhão de caracteres |
| **Amazon Rekognition** (`DetectText`, `DetectLabels`, Grupo 2) | Descontado dos créditos | ~US$ 1 por 1.000 imagens por API (preço de referência; São Paulo pode ser um pouco maior) |
| **AWS Lambda** | **Sempre gratuito:** 1 milhão de requisições e 400 mil GB-s por mês | US$ 0,20 por milhão de requisições |
| **CloudWatch Logs** | **Sempre gratuito:** 5 GB por mês | — |
| **API Gateway (REST)** | Descontado dos créditos | ~US$ 3,50 a 4,50 por milhão de requisições |
| **Amazon S3** | Descontado dos créditos | Centavos por milhares de requisições; armazenamento desprezível (objetos expiram em 7 dias) |

Situação da conta do projeto (consultada com `aws freetier get-account-plan-state`):
**Free Plan**, US$ 120 em créditos. No Free Plan não há cobrança no cartão; a conta é
encerrada quando os créditos acabam ou após 6 meses. No **Paid Plan** (necessário para o
Translate), o que passar dos créditos é cobrado no cartão — por isso os limites abaixo.

## 2. Quanto custa processar uma imagem

Cada imagem gera: 2 chamadas ao Rekognition, 1 tradução do texto + 1 dos rótulos, até 2
sínteses no Polly, ~4 escritas e algumas leituras no S3, e ~10 requisições na API
(envio + consultas até o resultado ficar pronto).

| Item | Típico (placa curta) | Pior caso (com os cortes do código) |
|---|---|---|
| Rekognition (2 chamadas) | US$ 0,003 | US$ 0,003 |
| Translate | ~150 caracteres (teste gratuito) | ~1.100 caracteres (teste gratuito) |
| Polly: narração em português (neural, até 1.500 caracteres) | US$ 0,005 | US$ 0,024 |
| Polly: pronúncia original (até 1.000 caracteres) | US$ 0,001 | US$ 0,016 (alemão, neural) |
| API Gateway + S3 + Lambda | < US$ 0,0002 | < US$ 0,0002 |
| **Total em créditos** | **~US$ 0,009** | **~US$ 0,043** |

Os cortes de texto existem no código para que o pior caso seja limitado:
`MAX_CARACTERES_TEXTO = 1000` e `MAX_CARACTERES_NARRACAO = 1500`
(`chalicelib/config.py`). O Rekognition também só lê até 100 palavras por imagem.

## 3. Limites adotados

| Limite | Valor | Onde |
|---|---|---|
| Envios por dia | **30 imagens** | `LIMITE_ENVIOS_DIA` em `.chalice/config.json` |
| Envios por mês | **300 imagens** | `LIMITE_ENVIOS_MES` em `.chalice/config.json` |
| Taxa de requisições da API | **1 req/s** (rajada de 2) | `scripts/limitar_api.sh` |
| Tamanho da imagem | 5 MB | `chalicelib/config.py` |

Acima do limite, `POST /imagens` responde **429** e a imagem **não é gravada**, então não
dispara nenhum serviço de IA. O contador fica em `controle/uso-AAAA-MM.json` no bucket e
é atualizado com escrita condicional do S3, então Lambdas simultâneas não ultrapassam o
limite.

### Por que esses valores são seguros

| Cenário (por mês) | Gasto de créditos | Translate (limite: 2 milhões) |
|---|---|---|
| Uso real do projeto (~100 imagens típicas) | ~US$ 1 | ~15 mil caracteres (0,8%) |
| Cota mensal inteira com imagens típicas (300) | ~US$ 2,70 | ~45 mil (2%) |
| Cota mensal inteira no pior caso (300) | ~US$ 13 | ~330 mil (17%) |
| **Abuso máximo** (cota cheia no pior caso + consultas a 1 req/s o mês inteiro) | **~US$ 30** | ~330 mil (17%) |

- Mesmo no **abuso máximo**, o gasto mensal fica em ~25% dos US$ 120 em créditos, e o
  Translate não passa de 17% do teste gratuito. O uso real esperado é ~1% dos créditos.
- Na duração do trabalho (1 a 2 meses), nem o cenário de abuso esgota os créditos.
- As consultas (`GET /imagens/{id}`) não entram na cota de envios, mas custam frações de
  centavo: usam HEAD/GET no S3 em vez de LIST, que é ~12x mais caro.

## 4. Proteções que dependem de você

1. **Alerta no AWS Budgets** (disponível no Free Plan): orçamento de **US$ 1** com aviso
   por e-mail em 50% e 100%. Como o uso real é de centavos, qualquer aviso indica algo
   fora do normal.
2. **Deixar a API no ar só quando precisar** (testes e gravação do vídeo) e rodar
   `./scripts/remover_tudo.sh` depois. Os scripts recriam tudo em minutos.
3. **Não aumentar os limites** sem refazer as contas acima.
4. Antes de mudar para o Paid Plan, verificar no console (*AWS Settings*) se há opção de
   **limite de gastos** e ativá-la.

## Fontes

- [Supported AWS services for Sign up for AWS (new)](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html) — Translate e Transcribe exigem o Paid Plan
- [AWS Free Tier — serviços de IA](https://aws.amazon.com/free/ai/) — Translate: 2M caracteres/mês por 12 meses no Paid Plan; Polly e Rekognition por créditos
- [AWS Free Tier](https://aws.amazon.com/free/) — créditos, Free Plan e Paid Plan
- [Preços do Amazon Translate](https://aws.amazon.com/translate/pricing/)
- [Preços do Amazon Polly](https://aws.amazon.com/polly/pricing/)
- [Preços do Amazon Rekognition](https://aws.amazon.com/rekognition/pricing/)
