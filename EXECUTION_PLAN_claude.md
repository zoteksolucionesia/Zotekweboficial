# Plan de Ejecución — Zotek Soluciones IA
> Basado en: Auditoría de seguridad + Code Review (obra/superpowers)
> Arquitectura confirmada: dos archivos canónicos activos simultáneamente
> Fecha: 2026-03-27

---

## Mapa de archivos canónicos

| Archivo | Rol | Entorno | Estado de seguridad |
|---|---|---|---|
| `functions/src/main.py` | Bot WhatsApp + Agentes | Firebase Functions (VIVO HOY) | ⚠️ Más vulnerable |
| `src/main.py` | Plataforma SaaS + Admin | Cloud Run / Docker | ✅ Más seguro |

> **Regla de oro del plan:** Un fix que toca lógica de seguridad va a **ambos** archivos.
> Un fix de infraestructura SaaS va solo a `src/main.py`.
> La lógica de agentes solo existe en `functions/src/main.py`.

---

## FASE 1 — EMERGENCIA (Hoy · Prioridad: BLOQUEANTE)

> Riesgo de explotación activa. No escalar ni publicitar la plataforma hasta completar esta fase.

### 1.1 — Firestore abierto al público (expira en 5 días)
**Archivo:** `firestore.rules`
**Impacto:** Lectura y escritura pública a toda la DB Firestore hasta el 1-abr-2026.

```javascript
// REEMPLAZAR TODO EL CONTENIDO CON:
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```
**Después:** Desplegar con `firebase deploy --only firestore:rules`

---

### 1.2 — `/api/recent_logs` expuesto sin autenticación
**Archivo:** `functions/src/main.py` línea 281

```python
# ANTES:
@app.get("/api/recent_logs")
async def get_recent_logs():
    return {"logs": list(RECENT_LOGS)}

# DESPUÉS:
@app.get("/api/recent_logs")
async def get_recent_logs(current_user: str = Depends(get_current_user)):
    return {"logs": list(RECENT_LOGS)}
```

---

### 1.3 — Eliminar `/debug-paths`
**Archivo:** `src/main.py` línea 521-530

```python
# ELIMINAR COMPLETAMENTE:
@app.get("/debug-paths")
async def debug_paths():
    return {
        "BASE_DIR": BASE_DIR,
        ...
    }
```

---

### 1.4 — Eliminar credenciales hardcodeadas como fallback
**Archivos:** `src/config.py` línea 24-26 y `functions/src/main.py` líneas 38-40, 261

**`src/config.py`:**
```python
# ANTES:
SECRET_KEY = os.getenv("SECRET_KEY", "ZOTEK_SECRET_DEFAULT_CHANGE_ME")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "zoteksolucionesia@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Zotek!SecureAdmin9X$2026")

# DESPUÉS:
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY no definida en variables de entorno")
if not ADMIN_EMAIL:
    raise ValueError("ADMIN_EMAIL no definida en variables de entorno")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD no definida en variables de entorno")
```

**`functions/src/main.py`:**
```python
# ANTES:
SECRET_KEY = os.getenv("SECRET_KEY", "ZOTEK_SECRET_DEFAULT_CHANGE_ME")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "zoteksolucionesia@gmail.com")

# DESPUÉS (mismo patrón: sin fallback, lanzar error si falta):
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY no definida")
if not ADMIN_EMAIL:
    raise ValueError("ADMIN_EMAIL no definida")
```

---

### 1.5 — Rotar SECRET_KEY JWT
**Archivo:** `.env` y `functions/.env`

```bash
# Generar nueva clave (ejecutar en terminal):
python -c "import secrets; print(secrets.token_hex(32))"

# Reemplazar en ambos .env:
SECRET_KEY=<nuevo_valor_64_caracteres_hexadecimales>
```
> ⚠️ Al rotar esta clave, todos los JWT actuales quedan invalidados. Los usuarios activos deberán volver a hacer login.

---

### 1.6 — Activar verificación de firma WhatsApp
**Archivos:** `.env`, `functions/.env`, `functions/src/main.py`

```bash
# Agregar en ambos .env:
WHATSAPP_APP_SECRET=<tu_app_secret_de_meta_developers>
```

**`functions/src/main.py`** — Agregar después de las importaciones, antes del `app = FastAPI()`:
```python
import hmac
import hashlib

WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")

def verify_whatsapp_signature(body: bytes, signature_header: str) -> bool:
    if not WHATSAPP_APP_SECRET:
        raise RuntimeError("WHATSAPP_APP_SECRET no configurada")
    expected = hmac.new(
        WHATSAPP_APP_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    received = signature_header.replace("sha256=", "")
    return hmac.compare_digest(expected, received)
```

Y en el endpoint `POST /webhook`, agregar al inicio:
```python
body = await request.body()
sig = request.headers.get("X-Hub-Signature-256", "")
if not verify_whatsapp_signature(body, sig):
    raise HTTPException(status_code=401, detail="Invalid signature")
```

---

### 1.7 — Deshabilitar debug SMTP en producción
**Archivo:** `src/main.py` línea 428

```python
# ANTES:
server.set_debuglevel(1)

# DESPUÉS:
# línea eliminada completamente
```

---

## FASE 2 — SEMANA 1 (Días 2-7 · Alta prioridad)

### 2.1 — Cifrar datos sensibles en la tabla `clients`
**Archivo:** `src/database.py` (y replicar en `functions/src/database.py`)

Instalar dependencia:
```bash
pip install cryptography
# Agregar a requirements.txt: cryptography>=42.0.0
```

Crear `src/services/encryption_service.py`:
```python
import os
from cryptography.fernet import Fernet

_key = os.getenv("FIELD_ENCRYPTION_KEY")
if not _key:
    raise ValueError("FIELD_ENCRYPTION_KEY no definida")

_fernet = Fernet(_key.encode())

def encrypt(value: str) -> str:
    if not value:
        return value
    return _fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    if not value:
        return value
    return _fernet.decrypt(value.encode()).decode()
```

Campos a cifrar en `clients`:
- `whatsapp_token`
- `stripe_api_key`
- `email_password`
- `clabe`

```bash
# Generar clave de cifrado (guardar en .env):
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# FIELD_ENCRYPTION_KEY=<resultado>
```

> **Plan de migración:** Crear script `scripts/migrate_encrypt_fields.py` que lea todos los registros, cifre los campos y los reescriba. Ejecutar una vez antes de desplegar el nuevo código.

---

### 2.2 — Configurar CORS restrictivo
**Archivos:** `src/main.py` y `functions/src/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://zotek-ia.web.app",
        "https://zotek-ia.firebaseapp.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 2.3 — Migrar códigos 2FA a Firestore
**Archivo:** `functions/src/main.py`

```python
# ANTES (en memoria):
verification_codes = {}

# DESPUÉS (en Firestore con TTL):
import firebase_admin
from firebase_admin import firestore as fs

def save_verification_code(email: str, code: str):
    db = fs.client()
    db.collection("verification_codes").document(email).set({
        "code": code,
        "expiry": datetime.now() + timedelta(minutes=10)
    })

def get_verification_code(email: str) -> dict | None:
    db = fs.client()
    doc = db.collection("verification_codes").document(email).get()
    if doc.exists:
        data = doc.to_dict()
        if data["expiry"] > datetime.now():
            return data
        doc.reference.delete()
    return None
```

---

### 2.4 — Autorización granular por client_id
**Archivo:** `src/main.py` — todos los endpoints `/api/clients/{client_id}/*`

Agregar helper de verificación:
```python
def verify_client_access(client_id: int, current_user: str):
    """Verifica que el usuario tiene acceso al cliente solicitado."""
    # Los admins tienen acceso a todo
    if current_user == ADMIN_EMAIL or current_user in ADMIN_EMAILS:
        return
    # Los clientes solo pueden ver sus propios datos
    client = database.get_client_by_id(client_id)
    if not client or client.get("email") != current_user:
        raise HTTPException(status_code=403, detail="Acceso denegado")
```

Agregar en cada endpoint protegido:
```python
@app.get("/api/clients/{client_id}/leads")
async def get_client_leads(client_id: int, ..., current_user: str = Depends(get_current_user)):
    verify_client_access(client_id, current_user)  # ← agregar esta línea
    ...
```

---

### 2.5 — Validar archivos PDF por MIME type real
**Archivo:** `src/main.py` — endpoint upload-pdf

```bash
pip install python-magic-bin  # Windows
# o python-magic en Linux/Mac
```

```python
import magic

async def upload_pdf(client_id: int, file: UploadFile, ...):
    content = await file.read()
    mime = magic.from_buffer(content[:1024], mime=True)
    if mime != "application/pdf":
        raise HTTPException(400, "El archivo debe ser un PDF válido")
    # ... resto del procesamiento
```

---

### 2.6 — Cerrar conexiones DB con try/finally
**Archivos:** `src/main.py` y `functions/src/main.py` — todos los endpoints que llaman a `database.get_connection()` directamente

```python
# PATRÓN CORRECTO (reemplazar en todos los endpoints):
conn = database.get_connection()
try:
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.commit()
finally:
    conn.close()  # ← se ejecuta siempre, incluso si hay excepción
```

---

### 2.7 — Proteger VAPI webhook con secreto compartido
**Archivo:** `src/main.py` línea 1072

```python
VAPI_WEBHOOK_SECRET = os.getenv("VAPI_WEBHOOK_SECRET")

@app.post("/api/vapi/webhook")
async def vapi_webhook(request: Request):
    # Verificar token secreto de VAPI
    auth = request.headers.get("x-vapi-secret", "")
    if VAPI_WEBHOOK_SECRET and not hmac.compare_digest(auth, VAPI_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")
    ...
```

```bash
# Agregar en .env:
VAPI_WEBHOOK_SECRET=<generar_con_secrets.token_hex(16)>
# Configurar el mismo valor en el dashboard de VAPI
```

---

## FASE 3 — SEMANA 2-3 (Días 8-21 · Media prioridad)

### 3.1 — Connection Pool PostgreSQL
**Archivo:** `src/database.py`

```python
from psycopg2 import pool

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=DATABASE_URL,
            sslmode='require'
        )
    return _pool

def get_connection():
    return get_pool().getconn()

def release_connection(conn):
    get_pool().putconn(conn)
```

---

### 3.2 — Rate limiting distribuido con Firestore
**Archivo:** `functions/src/main.py`

```python
def check_rate_limit_firestore(key: str, max_req: int, window_sec: int) -> bool:
    db = fs.client()
    ref = db.collection("rate_limits").document(key)
    now = datetime.now()
    window_start = now - timedelta(seconds=window_sec)

    @fs.transactional
    def update_in_transaction(transaction, ref):
        doc = ref.get(transaction=transaction)
        data = doc.to_dict() if doc.exists else {"requests": []}
        requests = [t for t in data["requests"] if t > window_start]
        if len(requests) >= max_req:
            return False
        requests.append(now)
        transaction.set(ref, {"requests": requests})
        return True

    return update_in_transaction(fs.client().transaction(), ref)
```

---

### 3.3 — Eliminar errores internos expuestos al cliente
**Archivos:** `src/main.py` y `functions/src/main.py` — todos los `except Exception as e: raise HTTPException(detail=str(e))`

```python
import logging
logger = logging.getLogger(__name__)

# PATRÓN CORRECTO:
except Exception as e:
    logger.error(f"Error en {endpoint_name}: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Error interno del servidor")
```

---

### 3.4 — Reemplazar print() con logging estructurado
**Ambos archivos**

```python
import logging

logging.basicConfig(
    level=logging.DEBUG if not Config.IS_PRODUCTION else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Reemplazar todos los print() con:
logger.debug("...")   # solo en dev
logger.info("...")    # eventos normales
logger.warning("...") # situaciones anómalas
logger.error("...")   # errores recuperables
```

---

### 3.5 — Eliminar SQLAlchemy muerta
**Archivo:** `requirements.txt`

```
# ELIMINAR esta línea:
SQLAlchemy==2.0.30
```

---

### 3.6 — Corregir `init_db()` duplicado
**Archivo:** `src/main.py` línea 122

```python
# ELIMINAR la línea 122:
database.init_db()  # ← borrar, ya se llama en startup_event

# MANTENER solo el startup_event:
@app.on_event("startup")
async def startup_event():
    database.init_db()
    global gemini
    gemini = GeminiEngine(api_key=GEMINI_API_KEY)
```

---

## FASE 4 — MES 2 (Largo plazo · Arquitectura)

### 4.1 — Unificación de codebases

**Estrategia:**
```
functions/
└── main.py          ← Bridge puro (10-20 líneas)
    └── importa src.main:app

src/
└── main.py          ← Única fuente de verdad (toda la lógica)
    ├── routers/
    │   ├── auth.py
    │   ├── clients.py
    │   ├── webhook.py
    │   └── vapi.py
    └── services/
        ├── gemini_service.py
        ├── whatsapp_service.py
        ├── vapi_service.py
        └── encryption_service.py  ← nuevo
```

`functions/main.py` simplificado:
```python
from firebase_functions import https_fn
from src.main import app
import uvicorn

@https_fn.on_request(timeout_sec=120, memory=1024)
def api_handler(req: https_fn.Request) -> https_fn.Response:
    # Firebase convierte la request al formato ASGI de FastAPI
    ...
```

---

### 4.2 — Agregar tests básicos

```bash
pip install pytest pytest-asyncio httpx
```

Estructura mínima:
```
tests/
├── test_auth.py          # login correcto/incorrecto, token expirado, 2FA
├── test_webhook.py       # mensaje válido, firma inválida, rate limit
├── test_clients.py       # CRUD con auth, acceso cruzado entre clientes
└── test_security.py      # endpoints públicos vs protegidos
```

---

### 4.3 — Migrar `@app.on_event("startup")` a lifespan

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database.init_db()
    global gemini
    gemini = GeminiEngine(api_key=Config.GEMINI_API_KEY)
    yield
    # Shutdown (cleanup si es necesario)

app = FastAPI(lifespan=lifespan)
```

---

## Checklist de despliegue por fase

### Fase 1 (antes del próximo deploy)
- [ ] `firestore.rules` actualizado y desplegado
- [ ] `/api/recent_logs` con auth
- [ ] `/debug-paths` eliminado
- [ ] Fallbacks hardcodeados eliminados
- [ ] `SECRET_KEY` rotada (64 chars hex)
- [ ] `WHATSAPP_APP_SECRET` definida y activa
- [ ] `server.set_debuglevel(0)` o eliminado

### Fase 2 (Semana 1)
- [ ] `FIELD_ENCRYPTION_KEY` generada y en .env
- [ ] Script de migración de cifrado ejecutado en DB
- [ ] CORS configurado con origins explícitos
- [ ] 2FA migrado a Firestore
- [ ] `verify_client_access()` en todos los endpoints de cliente
- [ ] Validación MIME en upload de PDF
- [ ] `try/finally` en todos los bloques de DB directa
- [ ] VAPI webhook con secreto compartido

### Fase 3 (Semana 2-3)
- [ ] Connection pool habilitado
- [ ] Rate limiting en Firestore
- [ ] `str(e)` eliminado de respuestas 500
- [ ] `print()` migrado a `logging`
- [ ] SQLAlchemy removido de requirements
- [ ] `init_db()` duplicado corregido

### Fase 4 (Mes 2)
- [ ] Estructura de routers creada en `src/`
- [ ] `functions/main.py` reducido a bridge puro
- [ ] Tests básicos escritos y en CI
- [ ] `lifespan` context manager implementado

---

## Variables de entorno requeridas al terminar

```bash
# Seguridad (CRÍTICAS)
SECRET_KEY=<secrets.token_hex(32)>
ADMIN_EMAIL=zoteksolucionesia@gmail.com
ADMIN_PASSWORD=<password_fuerte>
FIELD_ENCRYPTION_KEY=<Fernet.generate_key()>
WHATSAPP_APP_SECRET=<desde_meta_developers>
VAPI_WEBHOOK_SECRET=<secrets.token_hex(16)>

# Servicios (existentes, mantener)
DATABASE_URL=postgresql://...
GEMINI_API_KEY=...
VAPI_API_KEY=...
VAPI_ASSISTANT_ID=...
VAPI_PHONE_NUMBER_ID=...
EMAIL_APP_PASSWORD=...
VERIFY_TOKEN=...
N8N_WEBHOOK_URL=...
```

---

_claude
