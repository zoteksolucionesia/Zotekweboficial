# Code Review — Zotek Soluciones IA
> Metodología: [obra/superpowers code-reviewer](https://github.com/obra/superpowers/blob/main/agents/code-reviewer.md)
> Revisor Sénior · Fecha: 2026-03-27

---

## Reconocimiento de logros

Antes de los hallazgos, vale resaltar lo que está bien construido:

- **Arquitectura de servicios limpia:** `gemini_service`, `vapi_service`, `whatsapp_service`, `calendar_service` correctamente separados en `src/services/`.
- **Config centralizado:** `Config` class en `src/config.py` como fuente única de verdad para constantes.
- **Consultas SQL parametrizadas:** 100% con `%s` — protegidas contra SQL injection.
- **SSL habilitado en PostgreSQL:** `sslmode='require'` correcto para base de datos cloud.
- **Comparación de firma HMAC timing-safe:** uso correcto de `hmac.compare_digest()`.
- **Docstrings consistentes** en la mayoría de endpoints con Args/Returns documentados.
- **Sistema de planes definido:** estructura `CLIENT_PLANS` con límites claros por tier.

---

## CRITERIO 1 — Alineación con el Plan

### ¿Qué se planeó?
SaaS multi-tenant de agentes de WhatsApp + IA (Gemini) + voz (VAPI) + pagos (Stripe), con panel admin, base de conocimiento por PDF y sistema de citas.

### Desviaciones detectadas

**D-01 — Pagos Stripe: referenciado pero no implementado**
La columna `stripe_api_key` existe en la tabla `clients` y `stripe` aparece en `requirements.txt`, pero no existe ningún endpoint de pagos, webhooks de Stripe ni lógica de billing real. El sistema de planes (`free`, `basic`, `pro`, `enterprise`) con precios no está conectado a ningún procesador de pagos.

**D-02 — Dos versiones del mismo servidor corriendo en producción**
`src/main.py` (versión desarrollada localmente) y `functions/src/main.py` (versión desplegada en Firebase) divergieron significativamente:
- `functions/src/main.py` tiene 2FA por código de email, múltiples admins, `/api/recent_logs`
- `src/main.py` tiene login directo, un solo admin, endpoints VAPI avanzados
No hay un plan claro de qué versión es "canónica". Esto representa deuda técnica crítica.

**D-03 — Google Calendar: integración parcial**
`calendar_service.py` existe y `google_calendar_id` está en la DB, pero la integración real de escritura en calendarios está incompleta según la exploración del código.

**D-04 — SQLAlchemy importado pero no usado**
`requirements.txt` incluye `SQLAlchemy==2.0.30` pero toda la capa de datos usa `psycopg2` directo. Dead dependency que agrega peso y superficie de ataque sin valor.

---

## CRITERIO 2 — Calidad del Código

### 2.1 Manejo de Errores

**PROBLEMA: Excepciones silenciadas con `pass`** — `src/database.py` líneas 62-66
```python
for col, col_type in [...]:
    try:
        cursor.execute(f'ALTER TABLE clients ADD COLUMN IF NOT EXISTS {col} {col_type}')
    except Exception:
        pass  # ← silencia errores de migración sin loguear
```
Una migración fallida pasa desapercibida. Usar al mínimo `except Exception as e: print(e)`.

**PROBLEMA: Error interno expuesto al cliente** — `src/main.py` línea 818
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```
`str(e)` puede exponer trazas internas, nombres de tablas, o mensajes de PostgreSQL a clientes. Loguear internamente y retornar mensaje genérico.

**PROBLEMA: Recursos de DB no liberados en caso de error**
```python
conn = database.get_connection()
cursor = conn.cursor(cursor_factory=RealDictCursor)
# ... código que puede lanzar excepción ...
cursor.close()
conn.close()  # ← nunca se ejecuta si hay excepción
```
Patrón repetido en múltiples endpoints. Debe usarse `with conn:` o `try/finally`.

**POSITIVO: `send_security_code` maneja correctamente el fallo de email** retornando `False` en lugar de propagar la excepción.

---

### 2.2 Tipado

**PROBLEMA: `client_id` acepta `str` y `int` sin consistencia**
```python
# src/main.py línea 576
async def duplicate_client(client_id: str, ...):
    try:
        client_id_int = int(client_id)
    except (ValueError, TypeError):
        client_id_int = client_id  # ← puede quedar como str y pasar a la DB
```
Todos los demás endpoints usan `client_id: int` directamente (FastAPI lo valida automáticamente). Este endpoint hace conversión manual innecesaria y deja un camino sin validar.

**PROBLEMA: `limit` en query sin validación de rango** — línea 790
```python
async def get_client_leads(client_id: int, status: str = None, limit: int = 50, ...):
```
Un cliente puede enviar `limit=1000000` y hacer una query masiva. Agregar `limit: int = Query(50, ge=1, le=500)`.

---

### 2.3 Convenciones de Nombres

**Inconsistencia en idioma:** mezcla de español/inglés en el mismo módulo.
- Funciones: `get_client_leads`, `list_clients` (inglés) vs `activar_demo`, `registrar_cita` (español)
- Variables: `numero_paciente`, `fecha_cita` (español) vs `call_id`, `status`, `end_reason` (inglés)
- Comentarios: algunos en inglés (`# Skip validation if secret not configured`), otros en español

**Recomendación:** Elegir un idioma para el código (español para dominio del negocio es válido) y aplicarlo consistentemente.

---

### 2.4 Tests

**No existe ningún archivo de test en el proyecto.** No hay directorio `tests/`, `test_*.py` ni configuración de pytest/unittest. Para un SaaS en producción esto es un riesgo alto — cualquier refactor puede romper comportamiento sin detectarse.

Mínimo necesario:
- Tests de autenticación (login correcto, login incorrecto, token expirado)
- Tests de webhook WhatsApp (mensaje válido, firma inválida)
- Tests de rate limiting
- Tests de CRUD de clientes

---

### 2.5 Vulnerabilidades de Código

**V-01 — CRÍTICO: Inyección SQL en migración de schema** — `src/database.py` línea 64
```python
cursor.execute(f'ALTER TABLE clients ADD COLUMN IF NOT EXISTS {col} {col_type}')
```
`col` y `col_type` vienen de una lista hardcodeada en este caso, pero el patrón de f-string con `execute()` es peligroso. Si esta función evoluciona para aceptar input externo, será SQL injection directa. Usar siempre `psycopg2.sql` para identificadores dinámicos.

**V-02 — CRÍTICO: Debug activo en SMTP en producción** — línea 428
```python
server.set_debuglevel(1)  # Extra verbosity in logs
```
Esto imprime en logs el contenido de todos los emails enviados, incluyendo las contraseñas durante la autenticación SMTP (`AUTH LOGIN`). Remover en producción.

**V-03 — ALTO: Endpoint `/api/vapi/webhook` sin autenticación**
El webhook de VAPI actualiza estados de citas en la DB sin verificar firma ni token. Cualquiera puede enviar POST a `/api/vapi/webhook` con un `call_id` y cambiar el estado de cualquier cita.

**V-04 — ALTO: Información de autenticación en logs**
```python
print(f"DEBUG: Enviando desde {ADMIN_EMAIL} (Pass length: {len(EMAIL_PASSWORD)})")
print(f"📩 Login attempt: Email={email}")
```
Los logs de intentos de login facilitan enumeración de usuarios y timing attacks.

**V-05 — MEDIO: `server.set_debuglevel` expone credenciales SMTP en logs**
Ver V-02 — la salida de debug incluye los comandos SMTP raw, incluyendo `AUTH LOGIN base64(password)`.

**V-06 — MEDIO: Validación de email sin formato en `/api/auth/request-code`**
No se valida que el email tenga formato válido antes de enviarlo a `send_security_code`. Un atacante puede usar esto para probing de usuarios válidos por timing diferencial.

---

## CRITERIO 3 — Revisión Arquitectónica

### 3.1 Principios SOLID

**S — Single Responsibility: VIOLADO en `src/main.py`**
El archivo tiene 1179 líneas y mezcla:
- Configuración de app y middlewares
- Lógica de autenticación (JWT, 2FA, email)
- Rate limiting
- Métricas en memoria
- 20+ endpoints de dominio de negocio (clientes, leads, citas, VAPI, email)
- Lógica de negocio inline (en lugar de en servicios)

`src/main.py` debería ser solo el router. La lógica debe estar en `src/routers/` y `src/services/`.

**O — Open/Closed: BIEN** — El sistema de planes en `Config.CLIENT_PLANS` permite agregar nuevos planes sin modificar código de negocio.

**D — Dependency Inversion: PARCIAL** — `GeminiEngine` recibe `api_key` en constructor (bien), pero los endpoints hacen `database.get_connection()` directamente en lugar de usar inyección de dependencias de FastAPI.

---

### 3.2 Separación de Responsabilidades

**PROBLEMA: Lógica de negocio en endpoints**
```python
# src/main.py línea 503-516
for client in clients:
    monthly_count = database.get_monthly_message_count(client['id'])
    plan = client.get('plan', 'free')
    allowed, message = database.check_message_limit(client['id'], plan)
    usage_data.append({...})
```
Esta lógica debería estar en una capa de servicio (`src/services/billing_service.py`), no en el endpoint directamente.

**PROBLEMA: SQL inline en endpoints** — líneas 1093-1098
```python
conn = database.get_connection()
cursor = conn.cursor()
cursor.execute("UPDATE citas SET reminder_status = %s WHERE vapi_call_id = %s", ...)
```
Los endpoints del webhook de VAPI ejecutan SQL directamente, saltándose la capa `database.py`. Rompe el patrón establecido y duplica responsabilidades.

---

### 3.3 Escalabilidad

**PROBLEMA CRÍTICO: Estado en memoria en entorno stateless**

| Estado en memoria | Archivo | Impacto en multi-instancia |
|---|---|---|
| `verification_codes = {}` | `main.py:45` | 2FA falla intermitentemente |
| `rate_limiter = RateLimiter()` | `main.py:90` | Rate limit ineficaz |
| `metrics = {...}` | `main.py:95` | Métricas incorrectas |
| `PROCESSED_MESSAGES = deque()` | `main.py:142` | Deduplicación de webhooks falla |

Firebase Functions escala horizontalmente. Ninguna de estas estructuras sobrevive entre instancias o reinicios.

**PROBLEMA: N+1 queries sin batching** — línea 500-515
```python
for client in clients:
    monthly_count = database.get_monthly_message_count(client['id'])  # 1 query por cliente
```
Con 100 clientes = 101 queries. Agregar un método `get_all_monthly_counts()` que use `GROUP BY client_id`.

---

### 3.4 Integración Sistémica

**PROBLEMA: `init_db()` llamado dos veces en startup**
```python
# main.py línea 122
database.init_db()

# main.py línea 186 (startup_event)
@app.on_event("startup")
async def startup_event():
    if not os.environ.get('K_SERVICE'):
        database.init_db()
```
`init_db()` se ejecuta siempre en línea 122 y condicionalmente de nuevo en 186. Condición invertida: en producción (`K_SERVICE` existe), solo corre la primera vez. En desarrollo, corre dos veces.

---

## CRITERIO 4 — Documentación y Estándares

### 4.1 Documentación de funciones

**BIEN:** La mayoría de endpoints tienen docstrings con descripción y Args básicos.

**MAL:** Las funciones de `database.py` carecen de docstrings. `get_connection()`, `init_db()`, `list_clients()` no documentan qué retornan ni qué excepciones lanzan — crítico para la capa más importante del sistema.

### 4.2 Comentarios de debug en producción

Hay múltiples `print()` con emojis y mensajes de debug que irán a los logs de producción:
```python
print(f"--- SERVER STARTUP DIAGNOSTICS ---")
print(f"BASE_DIR: {BASE_DIR}")  # Expone estructura del filesystem
print(f"📥 PUT /api/clients/{client_id} called")
print(f"📦 Request data keys: {list(data.keys())}")
print(f"🔄 Converting 'menu' to 'menu_json'...")
```
Estos deben reemplazarse con `logging.debug()` deshabilitado en producción.

### 4.3 Código muerto

```python
# main.py línea 1
# Deploy Trigger: Force redeploy to fix persistent NameError in production.
# SaaS Improvements: Security, caching, metrics, conversation history
```
Comentarios de commit en el código fuente. Deben estar en git, no en el archivo.

```python
# main.py línea 420
import smtplib  # ← ya importado en línea 6
```
Import duplicado dentro de una función.

### 4.4 Encabezados de archivo

Ningún archivo en `src/` tiene encabezado con propósito, autor o versión. Para un equipo en crecimiento, agregar al menos una línea de descripción al inicio.

---

## CRITERIO 5 — Problemas Identificados y Recomendaciones

### 🔴 CRÍTICOS

| ID | Problema | Archivo:Línea | Acción requerida |
|---|---|---|---|
| C-01 | Firestore abierto hasta 1 abril 2026 | `firestore.rules:15` | Reemplazar con reglas de auth hoy |
| C-02 | `/api/recent_logs` sin auth | `functions/src/main.py` | Agregar `Depends(get_current_user)` |
| C-03 | `/debug-paths` expone filesystem | `main.py:521` | Eliminar endpoint |
| C-04 | `ADMIN_PASSWORD` hardcodeado como fallback | `config.py:26` | Lanzar `ValueError` si no está definido |
| C-05 | `SECRET_KEY` débil (14 chars) | `.env` | `secrets.token_hex(32)` |
| C-06 | Datos sensibles en texto plano en DB | `database.py:34-55` | Cifrar con Fernet |
| C-07 | Debug SMTP en producción expone passwords | `main.py:428` | `server.set_debuglevel(0)` |
| C-08 | VAPI webhook sin autenticación | `main.py:1072` | Verificar firma VAPI o token secreto |

### 🟠 IMPORTANTES

| ID | Problema | Archivo:Línea | Acción requerida |
|---|---|---|---|
| I-01 | Sin CORS middleware | `main.py:119` | Agregar `CORSMiddleware` con origins explícitos |
| I-02 | Firma WhatsApp deshabilitada | `main.py:159` | Definir `WHATSAPP_APP_SECRET` en `.env` |
| I-03 | Estado en memoria en entorno stateless | `main.py:45,90,95,142` | Migrar a Firestore/Redis |
| I-04 | Recursos de DB sin liberar en errores | Múltiples endpoints | Usar `try/finally` o context managers |
| I-05 | Error interno expuesto al cliente | `main.py:818` | Retornar mensaje genérico, loguear internamente |
| I-06 | N+1 queries en `/api/metrics/usage` | `main.py:500-516` | Batch query con `GROUP BY` |
| I-07 | Sin autorización granular por cliente | Todos los endpoints | Verificar ownership en cada request |
| I-08 | `init_db()` llamado dos veces | `main.py:122,186` | Eliminar llamada duplicada en línea 122 |
| I-09 | Dos codebases divergentes | `src/` vs `functions/src/` | Unificar — `functions/main.py` solo como bridge |
| I-10 | Sin connection pooling | `database.py:14` | Implementar `ThreadedConnectionPool` |
| I-11 | Sin tests unitarios ni de integración | Todo el proyecto | Agregar pytest con casos básicos de auth y webhook |
| I-12 | Validación de PDF solo por extensión | `main.py` upload endpoint | Validar MIME type real con `python-magic` |

### 🟡 SUGERENCIAS

| ID | Problema | Acción sugerida |
|---|---|---|
| S-01 | `SQLAlchemy` en requirements sin uso | Remover — reduce superficie de ataque |
| S-02 | Mezcla de idiomas en código | Elegir español o inglés y estandarizar |
| S-03 | `print()` en lugar de `logging` | Configurar `logging` con niveles y deshabilitar debug en prod |
| S-04 | `client_id: str` vs `client_id: int` inconsistente | Usar `int` en todos los endpoints (FastAPI valida automáticamente) |
| S-05 | Lógica de negocio inline en endpoints | Extraer a `src/services/` |
| S-06 | Sin encabezados de archivo | Agregar descripción de una línea al inicio de cada módulo |
| S-07 | `limit` en queries sin cota máxima | `limit: int = Query(50, ge=1, le=500)` |
| S-08 | Imports duplicados (`smtplib`) | Mover a top-level, eliminar imports dentro de funciones |
| S-09 | Comentarios de commit en el código | Mover a git history |
| S-10 | `@app.on_event("startup")` deprecado | Migrar a `lifespan` context manager (FastAPI moderno) |

---

## Resumen Ejecutivo

| Criterio | Puntuación | Notas |
|---|---|---|
| Alineación con plan | 6/10 | Stripe no implementado, dos codebases divergentes |
| Calidad de código | 5/10 | Manejo de errores inconsistente, sin tests, debug en prod |
| Arquitectura | 5/10 | `main.py` monolítico, estado en memoria en entorno stateless |
| Documentación | 6/10 | Endpoints documentados, DB layer sin docs |
| Seguridad | 4/10 | Múltiples vulnerabilidades críticas activas |
| **TOTAL** | **5.2/10** | **Requiere trabajo prioritario antes de escalar** |

---

## Siguiente paso recomendado

Confirmar con el equipo si la versión canónica del backend es `src/main.py` o `functions/src/main.py`, ya que **esta decisión desbloquea toda la Fase 1 del plan de seguridad**. Actualmente hay correcciones de seguridad que deben aplicarse en ambos archivos, duplicando el esfuerzo y el riesgo de inconsistencia.

---

_claude
