"""
Servicio de cifrado simétrico para campos sensibles en base de datos.
Usa Fernet (AES-128-CBC + HMAC-SHA256) de la librería cryptography.

Campos protegidos en tabla clients:
  - whatsapp_token
  - stripe_api_key
  - email_password
  - clabe
"""

import os
from cryptography.fernet import Fernet, InvalidToken

_raw_key = os.getenv("FIELD_ENCRYPTION_KEY")
if not _raw_key:
    raise ValueError("FIELD_ENCRYPTION_KEY no definida en variables de entorno")

_fernet = Fernet(_raw_key.encode())

# Campos de la tabla clients que deben cifrarse en reposo
SENSITIVE_CLIENT_FIELDS = {"whatsapp_token", "stripe_api_key", "email_password", "clabe"}


def encrypt(value: str) -> str:
    """Cifra un valor de texto. Retorna el texto cifrado en base64."""
    if not value:
        return value
    return _fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Descifra un valor previamente cifrado con encrypt(). Retorna texto plano."""
    if not value:
        return value
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        # El valor puede no estar cifrado aún (datos previos a la migración)
        return value


def encrypt_client_fields(data: dict) -> dict:
    """Cifra los campos sensibles de un dict de cliente antes de escribir en DB."""
    result = dict(data)
    for field in SENSITIVE_CLIENT_FIELDS:
        if field in result and result[field]:
            result[field] = encrypt(str(result[field]))
    return result


def decrypt_client_fields(data: dict) -> dict:
    """Descifra los campos sensibles de un dict de cliente al leer de DB."""
    if not data:
        return data
    result = dict(data)
    for field in SENSITIVE_CLIENT_FIELDS:
        if field in result and result[field]:
            result[field] = decrypt(str(result[field]))
    return result
