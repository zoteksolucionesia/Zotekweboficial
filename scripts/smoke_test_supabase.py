"""
Smoke test contra Supabase, antes del deploy.
Importa las funciones reales de database.py y appointment_service.py
y las ejecuta con datos reales (lectura) + un par de inserts dummy con cleanup.

Ejecutar desde la raíz del repo:
    python scripts/smoke_test_supabase.py
"""
import os
import sys
from pathlib import Path

# Forzar UTF-8 en stdout (Windows cp1252 no soporta emojis)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# 1. Cargar functions/.env explícitamente (la fuente de verdad)
for line in (ROOT / "functions" / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ[k.strip()] = v.strip()

# 2. Neutralizar load_dotenv para que database.py no sobrescriba con .env raíz
import dotenv
dotenv.load_dotenv = lambda *a, **kw: False

# 3. Insertar functions/ en sys.path para los imports relativos del módulo
sys.path.insert(0, str(ROOT / "functions"))

# 4. Importar el código real
from src import database  # noqa: E402
from src.services.appointment_service import AppointmentService  # noqa: E402

# Sanity: confirmar que database leyó la URL correcta
db_url = database.DATABASE_URL or ""
print(f"DATABASE_URL host: {db_url.split('@')[-1].split(':')[0] if '@' in db_url else '?'}")
print()

results = []
DUMMY_EMAIL = "smoke_test_dummy@zotek.local"
DUMMY_USER = "smoke_test_user_+0000000000"


def run(label, fn):
    try:
        out = fn()
        results.append((label, True, out))
        snippet = repr(out)[:80] if out is not None else "(None)"
        print(f"  [OK]   {label:55s} -> {snippet}")
    except Exception as e:
        results.append((label, False, str(e)))
        print(f"  [FAIL] {label:55s} -> {type(e).__name__}: {e}")


print("=" * 70)
print("SMOKE TEST — funciones críticas contra Supabase")
print("=" * 70)

# 1. get_client_by_email — debe encontrar Lilibauza
def t1():
    c = database.get_client_by_email("omarml@ucol.mx")
    assert c is not None, "no encontró cliente"
    assert c["id"] == 13, f"id esperado 13, got {c['id']}"
    return f"id={c['id']} name={c['name']}"

run("get_client_by_email('omarml@ucol.mx')", t1)

# 2. get_client_by_id(13) — debe devolver Lilibauza
def t2():
    c = database.get_client_by_id(13)
    assert c is not None
    assert "Bauza" in (c.get("name") or ""), f"name inesperado: {c.get('name')}"
    return f"name={c['name']}"

run("get_client_by_id(13)", t2)

# 3. list_clients — debe devolver lista no vacía
def t3():
    cs = database.list_clients()
    assert isinstance(cs, list)
    assert len(cs) >= 1
    return f"{len(cs)} clientes"

run("list_clients()", t3)

# 4. save_verification_code + get_verification_code (ciclo completo)
def t4():
    ok = database.save_verification_code(DUMMY_EMAIL, "123456", expires_minutes=5)
    assert ok, "save_verification_code retornó False"
    code = database.get_verification_code(DUMMY_EMAIL)
    assert code == "123456", f"code mismatch: {code!r}"
    return "ciclo OK"

run("save_verification_code + get_verification_code", t4)

# 5. get_client_schedules(13) — debe devolver lista (puede estar vacía)
def t5():
    s = database.get_client_schedules(13)
    assert isinstance(s, list)
    return f"{len(s)} schedules"

run("get_client_schedules(13)", t5)

# 6. get_client_chats(13, 5) — debe devolver lista con keys correctas
def t6():
    chats = database.get_client_chats(13, limit=5)
    assert isinstance(chats, list)
    if chats:
        first = chats[0]
        for key in ("id", "user_number", "message", "response", "timestamp"):
            assert key in first, f"key {key} faltante en chat {first}"
    return f"{len(chats)} chats"

run("get_client_chats(13, limit=5)", t6)

# 7. save_chat_message (escribe + lo eliminamos al cleanup)
def t7():
    ok = database.save_chat_message(13, DUMMY_USER, "smoke msg", "smoke response")
    assert ok, "save_chat_message retornó False"
    return "OK"

run("save_chat_message(13, dummy_user, ...)", t7)

# 8. AppointmentService.get_pending_appointments(13)
def t8():
    s = AppointmentService()
    apts = s.get_pending_appointments(13)
    assert isinstance(apts, list)
    return f"{len(apts)} pending appointments"

run("AppointmentService.get_pending_appointments(13)", t8)

# 9. AppointmentService.get_tomorrow_appointments(13)
def t9():
    s = AppointmentService()
    apts = s.get_tomorrow_appointments(13)
    assert isinstance(apts, list)
    return f"{len(apts)} tomorrow appointments"

run("AppointmentService.get_tomorrow_appointments(13)", t9)

# === CLEANUP ===
print()
print("=" * 70)
print("CLEANUP")
print("=" * 70)

import psycopg2
from urllib.parse import urlparse, unquote

p = urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
    host=p.hostname, port=p.port, user=unquote(p.username),
    password=unquote(p.password), dbname="postgres", sslmode="prefer"
)
cur = conn.cursor()
cur.execute("DELETE FROM verification_codes WHERE email = %s", (DUMMY_EMAIL,))
n_codes = cur.rowcount
cur.execute("DELETE FROM client_chats WHERE user_number = %s OR phone_number = %s",
            (DUMMY_USER, DUMMY_USER))
n_chats = cur.rowcount
conn.commit()
cur.close()
conn.close()
print(f"  Borradas {n_codes} filas en verification_codes (dummy)")
print(f"  Borradas {n_chats} filas en client_chats (dummy)")

# === RESUMEN ===
print()
print("=" * 70)
ok_count = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"RESULTADO: {ok_count}/{total} tests OK")
if ok_count < total:
    print("FALLOS:")
    for label, ok, out in results:
        if not ok:
            print(f"  - {label}: {out}")
    sys.exit(1)
print("Todos los tests pasaron. Listo para deploy.")
