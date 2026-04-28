"""
Diagnóstico read-only del estado de auth en la BD.
NO MODIFICA NADA. Solo lee metadata e información agregada.

Uso:
    cd functions
    python ../scripts/diagnose_auth_state.py
"""
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Cargar .env de functions/
env_path = Path(__file__).resolve().parent.parent / "functions" / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL no encontrada")
    sys.exit(1)

from urllib.parse import urlparse, unquote
parsed = urlparse(DATABASE_URL)
user = unquote(parsed.username or "")
password = unquote(parsed.password or "")
host = parsed.hostname
port = parsed.port or 5432
dbname = (parsed.path or "/postgres").lstrip("/")

print(f"Conectando a: {host}:{port}")
print(f"  user='{user}'  dbname='{dbname}'  password_len={len(password)}")
print()

conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname, sslmode="prefer")
cur = conn.cursor(cursor_factory=RealDictCursor)

# 1. Existe verification_codes?
print("=" * 60)
print("1. TABLA verification_codes")
print("=" * 60)
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'verification_codes'
""")
exists = cur.fetchone()
if not exists:
    print("  NO EXISTE la tabla verification_codes")
else:
    print("  Tabla existe.")
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'verification_codes'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print("  Columnas:")
    for c in cols:
        print(f"    - {c['column_name']:20s} {c['data_type']:30s} nullable={c['is_nullable']}")
    cur.execute("""
        SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public' AND tc.table_name = 'verification_codes'
    """)
    constraints = cur.fetchall()
    print("  Constraints:")
    if not constraints:
        print("    (ninguna)")
    for c in constraints:
        print(f"    - {c['constraint_type']:15s} {c['constraint_name']:40s} col={c['column_name']}")
    cur.execute("SELECT COUNT(*) AS n FROM verification_codes")
    n = cur.fetchone()["n"]
    print(f"  Filas actuales: {n}")
    if n > 0:
        cur.execute("SELECT email, code, expires_at, expires_at >= NOW() AS valido FROM verification_codes ORDER BY expires_at DESC LIMIT 5")
        rows = cur.fetchall()
        print("  Últimas 5 (más recientes):")
        for r in rows:
            print(f"    {r['email']:35s} code={r['code']} valido_ahora={r['valido']} expires={r['expires_at']}")

# 2. Estado de clients
print()
print("=" * 60)
print("2. TABLA clients")
print("=" * 60)
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'clients'
""")
if not cur.fetchone():
    print("  NO EXISTE la tabla clients")
else:
    cur.execute("SELECT COUNT(*) AS n FROM clients")
    n = cur.fetchone()["n"]
    print(f"  Filas: {n}")
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name='clients'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print("  Columnas de clients:")
    for c in cols:
        print(f"    - {c['column_name']:25s} {c['data_type']}")
    cur.execute("SELECT id, name, email FROM clients ORDER BY id")
    rows = cur.fetchall()
    print("  Lista de clientes:")
    for r in rows:
        print(f"    id={r['id']:<5} name={(r['name'] or '')[:30]:30s} email={r['email'] or '(vacio)':35s}")
    target_emails = ["omarml@ucol.mx", "morentinomar@gmail.com", "zoteksolucionesia@gmail.com"]
    print()
    print("  Búsqueda exacta de emails relevantes (case-insensitive):")
    for em in target_emails:
        cur.execute("SELECT id, name, email FROM clients WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s))", (em,))
        match = cur.fetchall()
        if match:
            for m in match:
                print(f"    [OK]   {em} -> id={m['id']} name={m['name']}")
        else:
            print(f"    [MISS] {em} no encontrado en clients")

# 3. ADMIN_EMAIL
print()
print("=" * 60)
print("3. ADMIN_EMAIL en .env")
print("=" * 60)
print(f"  ADMIN_EMAIL = {os.environ.get('ADMIN_EMAIL')!r}")

# 4. Tablas adicionales que el código asume existen
print()
print("=" * 60)
print("4. TODAS LAS TABLAS USADAS POR EL CÓDIGO")
print("=" * 60)
expected_tables = [
    "knowledge_base", "citas", "message_logs", "conversation_history",
    "sandbox_sessions", "client_chats", "client_schedules",
    "appointments", "lead_tracking",
]
for t in expected_tables:
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
    """, (t,))
    if cur.fetchone():
        cur.execute(f"SELECT COUNT(*) AS n FROM {t}")
        n = cur.fetchone()["n"]
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position
        """, (t,))
        cols = [r["column_name"] for r in cur.fetchall()]
        print(f"  [OK]   {t:25s} filas={n:<6} cols={','.join(cols)}")
    else:
        print(f"  [MISS] {t:25s} NO EXISTE")

# 5. Listado COMPLETO de tablas en public (para encontrar las que no esperamos)
print()
print("=" * 60)
print("5. TODAS LAS TABLAS EN SCHEMA public")
print("=" * 60)
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='public' AND table_type='BASE TABLE'
    ORDER BY table_name
""")
all_tables = [r["table_name"] for r in cur.fetchall()]
print(f"  Total: {len(all_tables)}")
for t in all_tables:
    print(f"    - {t}")

cur.close()
conn.close()
print()
print("Diagnóstico completo. NO se modificó nada.")
