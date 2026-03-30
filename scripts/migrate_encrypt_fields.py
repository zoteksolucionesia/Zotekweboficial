"""
Script de migración única: cifra los campos sensibles de clientes existentes en la DB.

Ejecutar UNA SOLA VEZ antes del primer deploy con FIELD_ENCRYPTION_KEY configurada:
    cd ZotekSolucionesIA
    python scripts/migrate_encrypt_fields.py

El script es idempotente: usa decrypt() antes de cifrar, por lo que si se corre
dos veces no duplicará el cifrado.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Agregar src al path para importar encryption_service
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.encryption_service import encrypt, decrypt, SENSITIVE_CLIENT_FIELDS

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL no configurada")
    sys.exit(1)


def migrate():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT id, whatsapp_token, stripe_api_key, email_password, clabe FROM clients")
    clients = cursor.fetchall()

    print(f"Clientes encontrados: {len(clients)}")
    migrated = 0

    for client in clients:
        updates = {}
        for field in SENSITIVE_CLIENT_FIELDS:
            raw = client.get(field)
            if not raw:
                continue
            # Descifrar primero (por si ya estaba cifrado) y volver a cifrar
            plaintext = decrypt(str(raw))
            ciphertext = encrypt(plaintext)
            if ciphertext != raw:
                updates[field] = ciphertext

        if updates:
            set_clause = ", ".join(f"{k} = %s" for k in updates)
            values = list(updates.values()) + [client['id']]
            write_cursor = conn.cursor()
            write_cursor.execute(
                f"UPDATE clients SET {set_clause} WHERE id = %s",
                values
            )
            write_cursor.close()
            migrated += 1
            print(f"  Cliente {client['id']}: {list(updates.keys())} cifrados")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\nMigración completada: {migrated}/{len(clients)} clientes actualizados.")


if __name__ == "__main__":
    print("=== Migración de cifrado de campos sensibles ===")
    confirm = input("¿Confirmar ejecución en la base de datos de PRODUCCIÓN? (si/no): ")
    if confirm.lower() != "si":
        print("Cancelado.")
        sys.exit(0)
    migrate()
