import sys
sys.path.insert(0, '.')
from functions.src.database import get_client_by_phone_id, get_connection

# 1. Fetch Zotek client info
zob = get_client_by_phone_id("980996958435648")
if zob:
    print(f"Zotek client found: {zob.get('name')}")
    print(f"Phone ID: {zob.get('phone_number_id')}")
    token = zob.get('whatsapp_token')
    print(f"Token length: {len(token) if token else 0}")
    if token:
        print(f"Token prefix: {token[:10]}...")
else:
    print("Zotek client NOT found in DB!")

# 2. Get last 5 appointments to see test numbers
conn = get_connection()
cursor = conn.cursor()
try:
    cursor.execute("SELECT id, client_id, cliente_telefono, paciente_nombre, created_at FROM citas ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    print("\nLast 5 citas:")
    for r in rows:
        print(r)
except Exception as e:
    print("Error querying citas:", e)

# 3. Get last message logs
try:
    cursor.execute("SELECT id, client_id, direction, phone_number, created_at FROM message_logs ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    print("\nLast 5 message logs:")
    for r in rows:
        print(r)
except Exception as e:
    print("Error querying message logs:", e)

cursor.close()
conn.close()
