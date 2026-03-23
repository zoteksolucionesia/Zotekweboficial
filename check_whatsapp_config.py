import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("="*70)
print("VERIFICANDO CONFIGURACION DE WHATSAPP")
print("="*70)

# Verificar bot maestro de Zotek
cur.execute("""
    SELECT id, name, phone_number_id, whatsapp_token IS NOT NULL as has_token
    FROM clients
    WHERE phone_number_id = '980996958435648' OR name LIKE '%Zotek%'
    ORDER BY id
""")

print("\nBOT MAESTRO ZOTEK:")
for row in cur.fetchall():
    print(f"  ID: {row[0]}")
    print(f"  Nombre: {row[1].encode('ascii', 'replace').decode('ascii')}")
    print(f"  Phone ID: {row[2]}")
    print(f"  Tiene Token: {row[3]}")

# Verificar todos los phone_number_id disponibles
print("\n" + "="*70)
print("TODOS LOS PHONE NUMBER ID REGISTRADOS:")
print("="*70)
cur.execute("SELECT DISTINCT phone_number_id FROM clients ORDER BY phone_number_id")
for row in cur.fetchall():
    print(f"  - {row[0]}")

cur.close()
conn.close()

print("\n" + "="*70)
