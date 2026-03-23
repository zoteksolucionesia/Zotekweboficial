import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Obtener el token de Zotek
cur.execute("SELECT whatsapp_token FROM clients WHERE phone_number_id = '980996958435648'")
zotek_token_row = cur.fetchone()

if not zotek_token_row:
    print("ERROR: No se encontro el bot de Zotek")
    conn.close()
    exit(1)

zotek_token = zotek_token_row[0]
print(f"Token de Zotek: {zotek_token[:20]}... (longitud: {len(zotek_token)})")

# Actualizar todos los demos con el mismo token
demo_ids = ['demo_restaurant', 'demo_retail', 'demo_dental', 'demo_psychology', 'demo_salon']

print("\nActualizando tokens de demos...")
for demo_id in demo_ids:
    cur.execute("""
        UPDATE clients 
        SET whatsapp_token = %s 
        WHERE phone_number_id = %s
    """, (zotek_token, demo_id))
    print(f"  {demo_id}: {cur.rowcount} fila(s) actualizada(s)")

conn.commit()
print("\n✅ Todos los demos ahora usan el token de Zotek")

# Verificar
print("\nVerificando actualizacion:")
cur.execute("SELECT phone_number_id, LENGTH(whatsapp_token) as token_len FROM clients WHERE phone_number_id LIKE 'demo%'")
for row in cur.fetchall():
    print(f"  {row[0]}: Token length: {row[1]}")

cur.close()
conn.close()
