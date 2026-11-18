"""Configurações lidas das variáveis de ambiente (definidas em .chalice/config.json)."""
import os

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'leitor-placas-bucket-local')

# O Amazon Translate não existe em sa-east-1; o Polly com vozes neurais é
# garantido em us-east-1. O Rekognition roda na região do bucket (usa S3Object).
TRANSLATE_REGION = os.environ.get('TRANSLATE_REGION', 'us-east-1')
POLLY_REGION = os.environ.get('POLLY_REGION', 'us-east-1')

IDIOMA_DESTINO = 'pt'

# Prefixos das chaves no S3
PREFIXO_UPLOADS = 'uploads/'
PREFIXO_RESULTADOS = 'resultados/'
PREFIXO_AUDIOS = 'audios/'

# Limites
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024        # 5 MB
CONFIANCA_MINIMA_TEXTO = 80.0                  # %
CONFIANCA_MINIMA_ROTULOS = 75.0                # %
MAXIMO_ROTULOS = 8
VALIDADE_URL_AUDIO = 3600                      # segundos

TIPOS_ACEITOS = {
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/png': 'png',
}
