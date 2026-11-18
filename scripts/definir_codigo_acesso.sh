#!/usr/bin/env bash
# Define (ou troca) o código de acesso da API, guardado no AWS SSM Parameter Store como
# SecureString (criptografado). O código NUNCA vai para o repositório.
#
# Uso:
#   ./scripts/definir_codigo_acesso.sh            # gera um código aleatório de 12 caracteres
#   ./scripts/definir_codigo_acesso.sh MEU-CODIGO # usa o código informado
#
# A Lambda guarda o código em cache por até 5 minutos: uma troca leva esse tempo para valer.
set -euo pipefail

PARAMETRO=$(python3 -c "import json; print(json.load(open('.chalice/config.json'))['environment_variables']['PARAMETRO_CODIGO_ACESSO'])")

if [ $# -ge 1 ]; then
  CODIGO="$1"
else
  # 3 blocos de 4 caracteres sem letras/números ambíguos (0/O, 1/I): ~60 bits de entropia
  CODIGO=$(python3 -c "import secrets; a='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; print('-'.join(''.join(secrets.choice(a) for _ in range(4)) for _ in range(3)))")
fi

if [ ${#CODIGO} -lt 10 ]; then
  echo "Use um código com pelo menos 10 caracteres." >&2
  exit 1
fi

aws ssm put-parameter --name "$PARAMETRO" --type SecureString --value "$CODIGO" --overwrite >/dev/null
echo "Código de acesso definido em $PARAMETRO:"
echo
echo "    $CODIGO"
echo
echo "Compartilhe só com a equipe e o professor (não coloque no repositório)."
