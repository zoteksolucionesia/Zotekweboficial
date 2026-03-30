# Implementación de Fases — ZotekSolucionesIA

## Fase 4 (Month 2) — Pendiente

### Objetivo General
Unificar arquitectura dual de codebases, agregar cobertura de tests con pytest, modernizar el ciclo de vida de la aplicación FastAPI, y completar la limpieza de logging.

---

### Fix 4.1: Unificar Codebases

**Contexto:**
El proyecto mantiene dos canónicos `main.py`:
- `src/main.py` — SaaS en Cloud Run / Dockerfile
- `functions/src/main.py` — Firebase Functions / Bot vivo de WhatsApp

Comparten lógica pero divergen en:
- Autenticación (SaaS: email/password; Functions: multi-admin en lista)
- Endpoints (SaaS: admin dashboard API; Functions: WhatsApp webhook + agent tools)
- Estado (SaaS: stateless; Functions: sesiones de demo/reserva en PostgreSQL)

**Acción:**
1. Extraer lógica compartida a módulos reutilizables:
   - `src/services/auth_service.py` — JWT, password hashing, verificación 2FA
   - `src/services/webhook_service.py` — Validación de firmas (WhatsApp, VAPI)
   - `src/services/agent_service.py` — Orquestación de tool_calls de Gemini (solo para Functions)

2. Convertir `src/main.py` y `functions/src/main.py` a orquestadores delgados:
   ```python
   # src/main.py (SaaS)
   from src.services.auth_service import create_access_token, verify_jwt
   from src.services.webhook_service import verify_whatsapp_signature

   # functions/src/main.py (Bot)
   from src.services.auth_service import verify_jwt
   from src.services.agent_service import ejecutar_herramientas_agente
   ```

3. Mantener `src/database.py` como singleton compartido (ya usa connection pool desde Fase 3).

4. Resultado esperado:
   - `src/main.py` ~500 líneas (era ~1200)
   - `functions/src/main.py` ~800 líneas (era ~1400)
   - Reutilización de código: 30-40% reducción de duplicación

---

### Fix 4.2: Agregar Cobertura de Tests (pytest)

**Estructura de tests:**

```
tests/
├── conftest.py                  # Fixtures compartidas
├── unit/
│   ├── test_encryption_service.py
│   ├── test_database.py
│   └── test_config.py
├── integration/
│   ├── test_auth_api.py
│   ├── test_clients_api.py
│   ├── test_whatsapp_webhook.py
│   └── test_vapi_webhook.py
└── e2e/
    └── test_bot_flow.py
```

**Casos mínimos requeridos:**

1. **Unit — `test_database.py`** (Connection Pool):
   ```python
   def test_get_connection_returns_pooled_connection():
       # Verificar que get_connection() retorna _PooledConnection
       conn = database.get_connection()
       assert isinstance(conn, database._PooledConnection)
       conn.close()  # Debe retornar a pool sin error

   def test_pool_connection_reuse():
       # Verificar que conexiones se reutilizan
       c1 = database.get_connection()
       id1 = id(c1._conn)
       c1.close()

       c2 = database.get_connection()
       id2 = id(c2._conn)
       # En estatisticamente alto % de los casos, id1 == id2 (reutilización)
   ```

2. **Unit — `test_encryption_service.py`**:
   ```python
   def test_encrypt_decrypt_roundtrip():
       plaintext = "token_secreto_123"
       encrypted = encrypt(plaintext)
       decrypted = decrypt(encrypted)
       assert plaintext == decrypted

   def test_encrypt_different_outputs():
       # Fernet añade IV aleatorio, output debe variar
       t = "same_input"
       assert encrypt(t) != encrypt(t)
   ```

3. **Integration — `test_auth_api.py`**:
   ```python
   def test_login_valid_credentials(client):
       response = client.post("/api/auth/login", json={
           "email": "zoteksolucionesia@gmail.com",
           "password": "Zotek!SecureAdmin9X$2026"
       })
       assert response.status_code == 200
       assert "access_token" in response.json()

   def test_login_invalid_credentials(client):
       response = client.post("/api/auth/login", json={
           "email": "admin@test.com",
           "password": "wrong"
       })
       assert response.status_code == 401
   ```

4. **Integration — `test_whatsapp_webhook.py`**:
   ```python
   def test_webhook_signature_verification(client):
       # Request válido con firma correcta → 200
       # Request con firma inválida → 401
       # Request sin firma cuando WHATSAPP_APP_SECRET está set → 401
   ```

5. **E2E — `test_bot_flow.py`** (simulado, sin llamadas reales a Gemini):
   ```python
   def test_demo_session_flow(client):
       # 1. Webhook recibe "quiero probar la demo de restaurante"
       # 2. Bot guarda sesión demo en DB
       # 3. Webhook recibe "salir"
       # 4. Bot limpia sesión
   ```

**Configuración (pytest.ini / pyproject.toml):**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
addopts = --cov=src --cov-report=html --cov-report=term-ms

# Meta: objetivo ≥70% cobertura en Phase 4
```

**Fixture en conftest.py:**
```python
import pytest
from fastapi.testclient import TestClient
from src.main import app  # o functions/src/main.py

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db(monkeypatch):
    # Mock database.get_connection() para tests sin DB real
    def mock_get_connection():
        ...
    monkeypatch.setattr("src.database.get_connection", mock_get_connection)
```

---

### Fix 4.3: Migrar `@app.on_event("startup")` → `lifespan`

**Contexto:**
`@app.on_event()` está deprecado en FastAPI ≥0.93. El patrón moderno es `lifespan` context manager.

**Cambio en `src/main.py`:**

```python
# Antes (Fase 3):
@app.on_event("startup")
async def startup_event():
    database.init_db()
    global gemini
    gemini = GeminiEngine(api_key=GEMINI_API_KEY)

# Después (Fase 4):
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    database.init_db()
    global gemini
    gemini = GeminiEngine(api_key=GEMINI_API_KEY)
    logger.info("Server startup complete")
    yield
    # Shutdown
    logger.info("Shutting down...")
    # Cleanup: close pool, flush logs, etc.
    if _pool := database._pool:
        _pool.closeall()

app = FastAPI(lifespan=lifespan)
```

**Aplica a ambos:**
- `src/main.py`
- `functions/src/main.py`

**Beneficios:**
- Ciclo de vida explícito (startup + shutdown en un bloque)
- Compatible con FastAPI 0.93+
- Permite cleanup en shutdown (cerrar pool, flush de logs)

---

### Fix 4.4: Limpiar Debug Prints Restantes en functions/src/main.py

**Estado actual:**
- ~50 `print(...); sys.stdout.flush()` en lógica del bot (demo sessions, reservations, menu interactions)
- Todos son debug prints del flujo de conversación

**Acción:**
Convertir los ~50 prints en lógica de bot a:
```python
# Antes:
print(f"[Demo] Iniciando sesión de demo para {numero_usuario} modo: {tipo_demo}"); sys.stdout.flush()

# Después:
logger.info(f"[Demo] Iniciando sesión de demo para {numero_usuario} modo: {tipo_demo}")
```

**Categorización:**
- Demo session flow: `logger.info()` (importante para seguimiento)
- Reservation flow: `logger.info()` (importante para auditoría)
- Menu parsing: `logger.debug()` (detalle, opcional)
- Error handling: `logger.error()`

**Resultado:**
- 100% logging estructurado en ambos `main.py`
- Cero `print()` o `sys.stdout.flush()` en código de producción
- Logs parseables por Cloud Logging / Cloud Run

---

### Fix 4.5: Documentar Architecture (README o ARCHITECTURE.md)

**Crear `ARCHITECTURE.md` con:**

1. **Dual Codebase:**
   ```
   src/main.py (SaaS)
   ├── Admin Dashboard API
   ├── Client Management
   └── Metrics & Webhooks

   functions/src/main.py (Bot)
   ├── WhatsApp Webhook Handler
   ├── Demo & Reservation Flows
   └── Agent Tool Execution

   Shared:
   └── src/{database,services,config}.py
   ```

2. **Deployment:**
   - Cloud Run: `gcloud run deploy zotek --source . --region us-central1`
   - Firebase Functions: `firebase deploy --only functions`

3. **Security Layers:**
   - JWT auth + 2FA (email codes)
   - WhatsApp/VAPI signature verification
   - Field encryption at rest (Fernet)
   - Rate limiting (in-memory Cloud Run, Firestore-based for Functions future)
   - CORS restricted to Firebase domains

4. **Database Schema:**
   - PostgreSQL (InsForge cloud)
   - Connection pool: ThreadedConnectionPool(min=2, max=10)
   - Tables: clients, citas, message_logs, conversation_history, verification_codes, lead_tracking, appointments, knowledge_base, sandbox_sessions

5. **Third-party Integrations:**
   - Gemini 2.0 Flash (AI engine)
   - WhatsApp Business API (messaging)
   - VAPI.ai (voice reminders)
   - n8n webhooks (automation)
   - Google Calendar (appointment sync)
   - Stripe (payments)
   - Firebase Firestore (security rules)

---

### Checklist de Entrega Fase 4

- [ ] Extraer servicios compartidos → `src/services/{auth,webhook,agent}_service.py`
- [ ] Refactor ambos `main.py` para usar servicios
- [ ] Crear estructura `tests/` con conftest.py
- [ ] Implementar tests unit (encryption, database, config)
- [ ] Implementar tests integration (auth, webhook)
- [ ] Agregar `@asynccontextmanager lifespan` a ambos main.py
- [ ] Convertir ~50 prints en `functions/src/main.py` a logger calls
- [ ] Ejecutar `pytest` con ≥70% cobertura (`pytest --cov`)
- [ ] Crear `ARCHITECTURE.md` con diagrama de flujo
- [ ] Actualizar CI/CD (GitHub Actions / Cloud Build) para correr tests en cada PR
- [ ] Merge a `main` branch

---

## Resumen General (Fases 1-4)

| Fase | Duración Est. | Impacto | Estado |
|------|--------------|---------|--------|
| 1 | Semana 1 | Seguridad crítica (6 vuln. críticas) | ✅ Completado |
| 2 | Semana 1 | Seguridad + arquitectura (12 fixes) | ✅ Completado |
| 3 | Semana 2 | Escalabilidad + observabilidad (pool, logging) | ✅ Completado |
| 4 | Semana 4 | Mantenibilidad + testabilidad | ⏳ **PENDIENTE** |

**Después de Fase 4:**
- Sistema production-ready con ≥70% test coverage
- Arquitectura unificada, fácil de mantener
- Logging estructurado para observabilidad
- Cumplimiento con buenas prácticas FastAPI

---

**Última actualización:** 27 Mar 2026
**Responsable:** Claude Code (claude-opus-4-6)
