"""
Test de conexión DIRECTA a Supabase (sin pooler) para aislar el problema.
Lee password desde functions/.env y prueba contra db.<ref>.supabase.co:5432.
"""
import os
from pathlib import Path
from urllib.parse import urlparse, unquote

env_path = Path(__file__).resolve().parent.parent / "functions" / ".env"
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())

import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]
parsed = urlparse(DATABASE_URL)
user_full = unquote(parsed.username or "")
password = unquote(parsed.password or "")
host = parsed.hostname

print(f"Pooler host: {host}")
print(f"User: {user_full}")
print(f"Password length: {len(password)}  (first 2 = {password[:2]!r}, last 2 = {password[-2:]!r})")
print()

def attempt(port, label):
    print(f"--- Probando port {port} ({label}) ---")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user_full,
            password=password,
            dbname="postgres",
            sslmode="require",
            connect_timeout=10,
        )
        cur = conn.cursor()
        cur.execute("SELECT current_user, current_database()")
        row = cur.fetchone()
        print(f"  OK -> user={row[0]} db={row[1]}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}".strip())
        return False

ok_session = attempt(5432, "session mode")
print()
ok_tx = attempt(6543, "transaction mode")
print()

if ok_session and ok_tx:
    print(">>> Ambos OK. Pooler funcionando bien.")
elif ok_session and not ok_tx:
    print(">>> Session mode OK, transaction mode rechaza. Esperar propagación al pooler tx.")
elif not ok_session and ok_tx:
    print(">>> Tx OK, session falla. Inusual.")
else:
    print(">>> Ambos rechazan -> password no coincide con la que tiene el pooler.")
