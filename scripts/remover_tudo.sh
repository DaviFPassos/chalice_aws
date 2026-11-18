#!/usr/bin/env bash
# Remove a aplicação da AWS (Lambdas, API Gateway, roles), o bucket, os logs e o
# código de acesso guardado no SSM.
set -euo pipefail

BUCKET=$(python3 -c "import json; print(json.load(open('.chalice/config.json'))['environment_variables']['BUCKET_NAME'])")

chalice delete
aws s3 rm "s3://$BUCKET" --recursive
aws s3api delete-bucket --bucket "$BUCKET"

# O `chalice delete` não apaga os logs das Lambdas no CloudWatch.
APP=$(python3 -c "import json; print(json.load(open('.chalice/config.json'))['app_name'])")
for GRUPO in $(aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/$APP" \
                 --query 'logGroups[].logGroupName' --output text); do
  aws logs delete-log-group --log-group-name "$GRUPO"
done
# Código de acesso no SSM Parameter Store
PARAMETRO=$(python3 -c "import json; print(json.load(open('.chalice/config.json'))['environment_variables']['PARAMETRO_CODIGO_ACESSO'])")
aws ssm delete-parameter --name "$PARAMETRO" 2>/dev/null || true

echo "Recursos removidos."
