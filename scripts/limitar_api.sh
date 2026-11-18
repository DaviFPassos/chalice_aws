#!/usr/bin/env bash
# Limita a taxa de requisições da API (proteção contra abuso e custo inesperado).
# Rode depois de cada `chalice deploy`. Valores: RATE req/s e BURST simultâneas.
set -euo pipefail

RATE=${RATE:-2}
BURST=${BURST:-5}
APP=$(python3 -c "import json; print(json.load(open('.chalice/config.json'))['app_name'])")
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='$APP'].id | [0]" --output text)

if [ -z "$API_ID" ] || [ "$API_ID" = "None" ]; then
  echo "API '$APP' não encontrada. Rode 'chalice deploy' antes." >&2
  exit 1
fi

aws apigateway update-stage --rest-api-id "$API_ID" --stage-name api --patch-operations \
  "op=replace,path=/*/*/throttling/rateLimit,value=$RATE" \
  "op=replace,path=/*/*/throttling/burstLimit,value=$BURST" >/dev/null
echo "API $API_ID limitada a $RATE req/s (burst $BURST)."
