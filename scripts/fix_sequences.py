"""
Resincroniza las sequences de auto-incremento (id SERIAL) que quedaron
desfasadas tras la migración de InsForge a Supabase.

Para cada tabla: si la sequence apunta a un valor <= MAX(id), la avanza a MAX(id).
NO modifica datos de las tablas, solo el metadato de las sequences.
"""
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
for line in (ROOT / "functions" / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ[k.strip()] = v.strip()

import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse, unquote

p = urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
    host=p.hostname, port=p.port, user=unquote(p.username),
    password=unquote(p.password), dbname="postgres", sslmode="prefer",
)
cur = conn.cursor(cursor_factory=RealDictCursor)

TABLES = [
    "clients", "client_chats", "client_schedules", "knowledge_base",
    "citas", "message_logs", "conversation_history", "sandbox_sessions",
    "appointments", "lead_tracking",
]

print("=" * 70)
print("Resincronización de sequences")
print("=" * 70)

for t in TABLES:
    cur.execute("SELECT pg_get_serial_sequence(%s, 'id') AS seq", (f"public.{t}",))
    seq = cur.fetchone()["seq"]
    if not seq:
        print(f"  [SKIP]  {t:25s} sin sequence en columna 'id'")
        continue

    cur.execute(f"SELECT COALESCE(MAX(id), 0) AS m FROM {t}")
    max_id = cur.fetchone()["m"]

    cur.execute(f"SELECT last_value, is_called FROM {seq}")
    sr = cur.fetchone()
    next_val = (sr["last_value"] + 1) if sr["is_called"] else sr["last_value"]

    if max_id == 0:
        print(f"  [OK]    {t:25s} tabla vacía, sequence sin cambios "
              f"(last={sr['last_value']} called={sr['is_called']})")
        continue

    if next_val > max_id:
        print(f"  [OK]    {t:25s} max_id={max_id:<6} next_val={next_val:<6} (sincronizada)")
    else:
        cur.execute("SELECT setval(%s, %s, true) AS v", (seq, max_id))
        conn.commit()
        new_next = cur.fetchone()["v"] + 1
        print(f"  [FIX]   {t:25s} max_id={max_id:<6} era next_val={next_val:<6} -> ahora {new_next}")

cur.close()
conn.close()
print()
print("Listo. Próximo paso: re-correr smoke_test_supabase.py para confirmar.")
