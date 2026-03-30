# Auditoría de Seguridad & Plan de Ejecución — Zotek Soluciones IA
> Generado: 2026-03-27

---

## RESUMEN EJECUTIVO

El proyecto es un SaaS de agentes de WhatsApp/voz con IA (Gemini), desplegado en Firebase Functions + Cloud Run, con backend FastAPI y PostgreSQL. Se identificaron **6 vulnerabilidades críticas**, **7 altas** y **5 medias**, varias de las cuales representan riesgo inmediato de compromiso total de la plataforma.

---

## VULNERABILIDADES CRÍTICAS (Actuar HOY)

### CRIT-01 — Firestore abierto al público: expira en 5 días
**Archivo:** `firestore.rules`
```javascript
allow read, write: if request.time < timestamp.date(2026, 4, 1);
```
Cualquier persona en internet puede leer y escribir en Firestore hasta el 1 de abril de 2026. En 5 días se cierra automáticamente pero podría ser explotado ahora mismo.

**Fix inmediato:** Reemplazar por reglas basadas en autenticación Firebase Auth.

---

### CRIT-02 — Endpoint `/api/recent_logs` público sin autenticación
**Archivo:** `functions/src/main.py`
Retorna logs internos del sistema (conversaciones, teléfonos, errores) sin ningún token JWT. Filtración directa de datos personales de usuarios finales.

**Fix:** Agregar `Depends(get_current_user)` con rol `admin`.

---

### CRIT-03 — Endpoint `/debug-paths` público
**Archivo:** `src/main.py`
Expone rutas del sistema de archivos del servidor. Facilita reconocimiento para ataques de path traversal.

**Fix:** Eliminar completamente en producción.

---

### CRIT-04 — Credenciales de producción hardcodeadas como fallback
**Archivo:** `src/config.py` (líneas 26-27), `functions/src/main.py` (línea 261)
```python
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Zotek!SecureAdmin9X$2026")
SECRET_KEY = os.getenv("SECRET_KEY", "ZOTEK_SECRET_DEFAULT_CHANGE_ME")
```
Si la variable de entorno falla por cualquier razón, la app arranca con credenciales conocidas. Un atacante que sepa el patrón puede autenticarse.

**Fix:** Lanzar excepción si las variables críticas no están definidas. Nunca usar valores por defecto para secretos.

---

### CRIT-05 — Datos sensibles de clientes en texto plano en la base de datos
**Tabla:** `clients`
Los siguientes campos se almacenan sin cifrar:
- `whatsapp_token` — Token API de Meta/WhatsApp
- `stripe_api_key` — Clave privada de Stripe (acceso a pagos reales)
- `email_password` — Contraseña SMTP del cliente
- `clabe` — Clave bancaria interbancaria

Cualquier acceso no autorizado a la DB compromete **todas** las integraciones de todos los clientes simultáneamente.

**Fix:** Cifrar con `cryptography.fernet` usando una clave maestra separada del `DATABASE_URL`.

---

### CRIT-06 — SECRET_KEY JWT demasiado débil
**Archivo:** `.env`
```
SECRET_KEY=ZotekSeguro2026
```
Solo 14 caracteres, sin entropía aleatoria. Vulnerable a ataques de fuerza bruta offline si un atacante obtiene un token JWT válido. Comprometería la autenticación entera.

**Fix:** Generar con `secrets.token_hex(32)` — 64 caracteres hexadecimales aleatorios.

---

## VULNERABILIDADES ALTAS

### HIGH-01 — Sin CORS configurado
**Archivo:** `src/main.py`, `functions/src/main.py`
No hay `CORSMiddleware`. Cualquier origen puede hacer peticiones cross-origin a la API.

**Fix:**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zotek-ia.web.app", "https://zotek-ia.firebaseapp.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### HIGH-02 — Firma de webhook WhatsApp deshabilitada
**Archivo:** `src/main.py` (línea 159)
```python
if not WHATSAPP_APP_SECRET:
    return True  # Skip validation if secret not configured
```
`WHATSAPP_APP_SECRET` no está en el `.env`. Cualquiera puede enviar POST a `/webhook` y el bot responderá. Permite spam, abuso y costos no autorizados de Gemini/VAPI.

**Fix:** Definir `WHATSAPP_APP_SECRET` en `.env` y nunca permitir skip.

---

### HIGH-03 — Rate limiting ineficaz en entorno multi-instancia
**Archivo:** `src/main.py`
El rate limiter es un `defaultdict` en memoria. Firebase Functions escala horizontalmente — cada instancia tiene sus propios contadores. El límite real es `100 req/min × N instancias`.

**Fix:** Usar Redis (Upstash o Firebase Redis) para contadores compartidos.

---

### HIGH-04 — Códigos 2FA en memoria (mismo problema multi-instancia)
**Archivo:** `functions/src/main.py`
```python
verification_codes = {}  # {email: {"code": str, "expiry": datetime}}
```
Un código generado en la instancia A no existe en la instancia B. El login 2FA fallará intermitentemente en producción con múltiples instancias.

**Fix:** Almacenar en Firestore con TTL o en Redis.

---

### HIGH-05 — Sin autorización granular por recurso
**Archivo:** `src/main.py` — todos los endpoints de clientes
`get_current_user` valida el JWT pero no verifica que el usuario tenga permiso para acceder al `client_id` específico. Un cliente autenticado puede acceder a datos de otro cliente si conoce su ID.

**Fix:** Verificar `client_id` contra el JWT en cada endpoint, o implementar middleware de autorización.

---

### HIGH-06 — Validación de archivos subidos solo por extensión
**Archivo:** `src/main.py` — endpoint `/api/clients/{id}/upload-pdf`
Solo valida que el nombre termine en `.pdf`. No verifica el MIME type real del archivo, permitiendo subir ejecutables maliciosos renombrados.

**Fix:**
```python
import magic
mime = magic.from_buffer(await file.read(1024), mime=True)
if mime != "application/pdf":
    raise HTTPException(400, "El archivo no es un PDF válido")
```

---

### HIGH-07 — Sin connection pooling en PostgreSQL
**Archivo:** `src/database.py`
Cada request abre y cierra una conexión nueva a PostgreSQL. Bajo carga, esto agotará las conexiones disponibles y generará latencia alta.

**Fix:** Usar `psycopg2.pool.ThreadedConnectionPool` o migrar a `asyncpg` con pool async.

---

## VULNERABILIDADES MEDIAS

### MED-01 — Dos codebases paralelas con funcionalidades divergentes
`src/main.py` (1179 líneas) y `functions/src/main.py` (≈99KB) son versiones distintas de la misma API con features diferentes, auth diferente y bugs diferentes. Es imposible mantener seguridad coherente en dos versiones.

**Fix:** Unificar en una sola versión. `functions/main.py` debe ser un bridge puro hacia `src/`.

---

### MED-02 — SSRF potencial en endpoint de prueba SMTP
**Endpoint:** `POST /api/clients/{id}/email-test`
El host SMTP viene del cliente sin validación. Un atacante podría configurar `smtp_host=169.254.169.254` para alcanzar metadata de cloud o servicios internos.

**Fix:** Whitelist de hosts SMTP permitidos o validación estricta de IP/hostname.

---

### MED-03 — Datos personales en logs
`logs.json` (2MB) y `recent_logs.json` contienen conversaciones reales con teléfonos de usuarios finales. Estos archivos están en el directorio del proyecto.

**Fix:** Nunca loguear números de teléfono completos. Aplicar `sanitize_phone` también en el logger principal.

---

### MED-04 — Tokens de WhatsApp expiran sin renovación automática
Los `whatsapp_token` de los clientes se almacenan estáticamente. Los tokens de Meta expiran. No hay mecanismo de renovación, lo que causa fallas silenciosas del bot.

**Fix:** Implementar refresh automático o alertas de expiración.

---

### MED-05 — `service-account-key.json` duplicado en dos ubicaciones
Existen dos archivos de credenciales Firebase diferentes en `/` y en `functions/`. Aumenta la superficie de exposición accidental y dificulta la rotación de claves.

**Fix:** Un único archivo referenciado por variable de entorno `GOOGLE_APPLICATION_CREDENTIALS`.

---

## PLAN DE EJECUCIÓN

### FASE 1 — EMERGENCIA (Hoy, antes de las 24h)
> Riesgo de explotación activa si se ignora

| # | Tarea | Archivo | Prioridad |
|---|---|---|---|
| 1.1 | Actualizar `firestore.rules` con autenticación real | `firestore.rules` | CRÍTICO |
| 1.2 | Agregar auth a `/api/recent_logs` | `functions/src/main.py` | CRÍTICO |
| 1.3 | Eliminar endpoint `/debug-paths` | `src/main.py` | CRÍTICO |
| 1.4 | Eliminar fallbacks de credenciales hardcodeadas | `src/config.py`, `functions/src/main.py` | CRÍTICO |
| 1.5 | Rotar `SECRET_KEY` JWT con `secrets.token_hex(32)` | `.env` | CRÍTICO |
| 1.6 | Definir `WHATSAPP_APP_SECRET` y activar validación de firma | `.env`, `src/main.py` | ALTO |

---

### FASE 2 — SEMANA 1 (Días 2-7)
> Protección de datos y arquitectura de seguridad base

| # | Tarea | Archivo | Prioridad |
|---|---|---|---|
| 2.1 | Cifrar campos sensibles en tabla `clients` con Fernet | `src/database.py` | CRÍTICO |
| 2.2 | Configurar CORS restrictivo | `src/main.py`, `functions/src/main.py` | ALTO |
| 2.3 | Migrar códigos 2FA a Firestore con TTL | `functions/src/main.py` | ALTO |
| 2.4 | Implementar autorización granular por `client_id` | `src/main.py` | ALTO |
| 2.5 | Validar archivos por MIME type real | `src/main.py` | ALTO |
| 2.6 | Consolidar `service-account-key.json` en una sola ubicación | Raíz + `functions/` | MEDIO |

---

### FASE 3 — SEMANA 2-3 (Días 8-21)
> Performance, observabilidad y hardening

| # | Tarea | Archivo | Prioridad |
|---|---|---|---|
| 3.1 | Implementar connection pool PostgreSQL | `src/database.py` | ALTO |
| 3.2 | Migrar rate limiting a Redis/Firestore | `src/main.py` | ALTO |
| 3.3 | Validar SSRF en configuración SMTP | `src/main.py` | MEDIO |
| 3.4 | Purgar datos personales de archivos de log | `logs.json`, `recent_logs.json` | MEDIO |
| 3.5 | Unificar `src/main.py` y `functions/src/main.py` | Ambos | MEDIO |

---

### FASE 4 — MES 2 (Largo plazo)
> Madurez de seguridad

| # | Tarea |
|---|---|
| 4.1 | Implementar renovación automática de tokens WhatsApp |
| 4.2 | Agregar auditoría de acceso (quién accedió a qué y cuándo) |
| 4.3 | Implementar tests de seguridad automatizados en CI |
| 4.4 | Documentar política de rotación de secretos |
| 4.5 | Considerar WAF (Web Application Firewall) frente a Firebase Functions |

---

## MÉTRICAS DE RIESGO ACTUAL

| Categoría | Puntuación | Estado |
|---|---|---|
| Confidencialidad de datos | 3/10 | CRÍTICO |
| Integridad del sistema | 5/10 | ALTO |
| Disponibilidad | 6/10 | MEDIO |
| Autenticación | 5/10 | ALTO |
| Autorización | 4/10 | CRÍTICO |
| **Score Global** | **4.6/10** | **ALTO RIESGO** |

---

_claude
