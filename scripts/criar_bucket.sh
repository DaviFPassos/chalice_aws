#!/usr/bin/env bash
# Cria o bucket S3 usado pela aplicação (deve existir antes do `chalice deploy`).
# O nome vem de .chalice/config.json -> environment_variables.BUCKET_NAME
set -euo pipefail

BUCKET=$(python3 -c "import json; print(json.load(open('.chalice/config.json'))['environment_variables']['BUCKET_NAME'])")
REGIAO=${AWS_REGION:-$(aws configure get region)}

echo "Criando s3://$BUCKET em $REGIAO ..."
if [ "$REGIAO" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGIAO"
else
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGIAO" \
    --create-bucket-configuration LocationConstraint="$REGIAO"
fi

# Bucket totalmente privado: os áudios são entregues por URLs temporárias.
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Apaga imagens, resultados e áudios após 7 dias (privacidade e custo).
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration '{
  "Rules": [{"ID": "expirar-7-dias", "Status": "Enabled", "Filter": {"Prefix": ""},
             "Expiration": {"Days": 7}}]
}'

echo "Bucket pronto: $BUCKET"
