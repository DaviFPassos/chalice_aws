#!/usr/bin/env bash
# Remove a aplicação da AWS (Lambdas, API Gateway, role) e apaga o bucket.
set -euo pipefail

BUCKET=$(python3 -c "import json; print(json.load(open('.chalice/config.json'))['environment_variables']['BUCKET_NAME'])")

chalice delete
aws s3 rm "s3://$BUCKET" --recursive
aws s3api delete-bucket --bucket "$BUCKET"
echo "Recursos removidos."
