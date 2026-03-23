import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("="*70)
print("BOTS DEMO CONFIGURADOS")
print("="*70)

cur.execute("""
    SELECT phone_number_id, name, whatsapp_token IS NOT NULL as has_token
    FROM clients 
    WHERE phone_number_id LIKE 'demo%'
    ORDER BY phone_number_id
""")

for row in cur.fetchall():
    has_token_str = "TIENE token" if row[2] else "NO tiene token"
    print(f"\n{row[0]}:")
    print(f"  Nombre: {row[1].encode('ascii', 'replace').decode('ascii')}")
    print(f"  WhatsApp Token: {has_token_str}")

print("\n" + "="*70)
print("NOTA: Los demos NO tienen token propio, usan el de Zotek")
print("="*70)

cur.close()
conn.close()
