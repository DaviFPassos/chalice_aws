# chalice_aws

API REST serverless construída com [AWS Chalice](https://aws.github.io/chalice/), seguindo o tutorial oficial
[REST API Tutorial](https://aws.github.io/chalice/tutorials/basicrestapi.html).

O Chalice gera e implanta automaticamente uma função **AWS Lambda** e uma **API Gateway (REST API)**
a partir do código em `app.py`.

Cada passo do tutorial foi registrado em um commit separado (`git log` para acompanhar a evolução).
Nos passos 6 a 9 o tutorial original substitui o `app.py` inteiro; aqui eles foram incorporados como
rotas novas no mesmo app, para que todos os exemplos fiquem disponíveis em um único deploy.

## Estrutura

```
.
├── .chalice/config.json   # configuração do Chalice (app_name, stages)
├── app.py                 # código da API
├── requirements.txt       # dependências que vão para a Lambda (vazio)
├── requirements-dev.txt   # ferramentas de desenvolvimento (chalice, httpie, pytest)
├── pytest.ini             # configuração do pytest
├── tests/test_app.py      # testes automatizados das rotas
└── README.md
```

## Pré-requisitos

- Python 3.12 (o runtime da Lambda segue a versão do Python local)
- Credenciais AWS configuradas (`aws configure`) com permissão para criar IAM Role, Lambda e API Gateway

Para conferir as credenciais:

```bash
aws configure list
aws sts get-caller-identity
```

## Instalação

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Executar localmente

```bash
chalice local          # sobe em http://127.0.0.1:8000
curl http://127.0.0.1:8000/
```

## Testes

```bash
python -m pytest -v
```

Os testes usam o `chalice.test.Client`, que executa as rotas em memória (sem servidor e sem AWS).
Como `application/json` está em `binary_types` (rota `/gzip`), as requisições de teste enviam
`Accept: application/json`.

## Deploy na AWS

```bash
chalice deploy         # cria/atualiza Lambda + API Gateway (stage "api")
chalice url            # mostra a URL da API
chalice logs           # logs da Lambda
chalice delete         # remove todos os recursos da AWS
```

Deploy atual (região `sa-east-1`):
`https://6og27bi5ki.execute-api.sa-east-1.amazonaws.com/api/`

## Endpoints

| Método | Rota | Passo do tutorial | Descrição |
|---|---|---|---|
| GET | `/` | 1 | Retorna `{"hello": "world"}` |
| GET | `/cities/{city}` | 2–3 | Estado da cidade (`seattle`, `portland`); cidade desconhecida → `400 BadRequestError` |
| PUT | `/resource/{value}` | 4 | Ecoa o valor recebido na URL |
| GET, PUT | `/objects/{key}` | 5 | Armazena (PUT) e lê (GET) um JSON em memória; chave inexistente → `404` |
| GET | `/introspect` | 5 | Devolve os metadados da requisição (`app.current_request.to_dict()`) |
| POST | `/` | 6 | Aceita apenas `application/x-www-form-urlencoded`; JSON → `415` |
| GET | `/custom-response` | 7 | Resposta customizada `text/plain` com `hello world!` |
| GET | `/gzip` | 8 | JSON comprimido com GZIP (`Content-Encoding: gzip`) |
| PUT | `/supports-cors` | 9 | CORS padrão (`cors=True`) |
| GET | `/custom-cors` | 9 | CORS customizado com `CORSConfig` |
| GET, OPTIONS | `/cors_multiple_origins` | 9 | CORS com múltiplas origens permitidas |

## Exemplos de uso

```bash
API=https://6og27bi5ki.execute-api.sa-east-1.amazonaws.com/api

http $API/cities/seattle                       # {"state": "WA"}
http $API/cities/vancouver                     # 400 BadRequestError
http PUT $API/resource/foo                     # {"value": "foo"}

http GET $API/objects/mykey                    # 404
echo '{"foo": "bar"}' | http PUT $API/objects/mykey
http GET $API/objects/mykey                    # {"mykey": {"foo": "bar"}}

http "$API/introspect?query1=value1&query2=value2" 'X-TestHeader: Foo'

http POST $API/ states=WA states=CA            # 415 (JSON não é aceito)
http --form POST $API/ states=WA states=CA     # {"states": ["WA", "CA"]}

http $API/custom-response                      # hello world!
curl --compressed $API/gzip                    # {"hello": "world"}
http OPTIONS $API/cors_multiple_origins Origin:http://allowed1.example.com
```

## Observações

- `app.debug = True` está ativo para fins didáticos (stack traces nas respostas de erro).
  Desative antes de usar em produção.
- Os dados de `/objects/{key}` ficam na memória da Lambda e se perdem quando o container é reciclado.
- Para a rota `/gzip`, `application/json` foi adicionado a `app.api.binary_types`, como no tutorial.
- **Segurança:** nunca coloque chaves da AWS no código ou no `.chalice/config.json` (ele é versionado).
  As credenciais ficam em `~/.aws/credentials`, fora do repositório. O `.gitignore` também ignora
  `.chalice/deployed/` e `.chalice/deployments/` (contêm o ID da conta e ARNs), arquivos `.env`, chaves `*.pem`/`*.key` etc.
