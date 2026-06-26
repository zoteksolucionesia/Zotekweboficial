# Zotek Project Session Logs

## Session Log: 2026-06-01 (14:05) — SSO con el CRM LiliBauza (login único en el portal)

### Metadata
- **Session Date:** June 1, 2026, 14:05
- **Status:** SSO implementado y verificado E2E. El portal acepta una sesión iniciada desde el CRM LiliBauza sin pedir OTP.
- **Affected Components:** `functions/src/main.py`, `www/portal/portal.js`, `functions/.env`
- **Commit:** `c267561` (rama `feature/admin-client-tabs-ui`)
- **Repo externo relacionado:** LiliBauza-admin (CRM), commit `b9059ea`.

### 1. Contexto
El CRM de terapeutas (`lilibauza-admin.web.app`) embebe el portal Zotek (`zotek-ia.web.app/portal`) dentro de su sección `/admin/citas` mediante un iframe. La gestión de citas/leads/horarios vive 100% en el portal (Supabase `bjtqcnecyknwgieijqgh`); el CRM no almacena nada de citas. Requisito: el terapeuta ya autenticado en el CRM **no debe volver a loguearse** en el portal.

### 2. Implementación del SSO
- **Esquema:** el CRM firma un JWT HS256 de **corta duración (120 s)** con un secreto **COMPARTIDO** `PORTAL_SSO_SECRET` — **distinto** del `SECRET_KEY` interno del portal, para no exponer la firma de sesiones reales. La identidad viaja como **email**.
- **Nuevo endpoint** `POST /api/auth/sso` en `functions/src/main.py`:
  - Lee `PORTAL_SSO_SECRET = os.getenv("PORTAL_SSO_SECRET")` (devuelve 500 si falta).
  - Decodifica el `sso_token` con `jwt.decode(..., algorithms=[ALGORITHM])` (`HS256`); 401 si es inválido/expirado.
  - Resuelve rol: `admin` si el email está en `ADMIN_EMAILS_EXTRA`, si no `client`. Busca el cliente por email (`database.get_client_by_email`); si no existe y no es admin → **403**.
  - Emite el `access_token` interno habitual con `create_access_token(data={"sub": email, "role": role, "client_id": client_id})` y devuelve `{access_token, token_type, role, client_id, client_name, email}`.
- **Frontend** `www/portal/portal.js`: `init()` se hizo `async`. Si detecta `?sso=<token>` en la URL: limpia el query con `history.replaceState`, hace `fetch` a `/api/auth/sso`, guarda `access_token`/`clientData` en `localStorage` y entra directo a `showDashboard()`. Si falla, cae al flujo normal de OTP.

### 3. Configuración / despliegue
- `PORTAL_SSO_SECRET` agregado a `functions/.env` (mismo valor que en el CRM). **Importante:** la línea debe usar fin de línea **LF**; un CRLF en esa línea rompió el parseo del `.env` y devolvió "no configurado".
- Deploy: `firebase deploy --only functions` (api_handler, Python 3.13, 2ª gen / Cloud Run).

### 4. Verificación
- `morentinomar@gmail.com` (presente en `ADMIN_EMAILS_EXTRA`) → entra como **admin**, `access_token` emitido, sin OTP. ✅
- `lilibauza@gmail.com` → **403** (no registrado como cliente en el SaaS). Pendiente: registrarla cuando use su propio email.

### 5. Pendientes
- 🔒 Rotar `PORTAL_SSO_SECRET` (quedó visible en el chat de la sesión); cambiarlo idéntico en el `.env` del portal y del CRM, y redesplegar ambos.
- Dar de alta a `lilibauza@gmail.com` como cliente del portal para que su SSO funcione.
- 🎨 Integración visual del portal embebido → **implementada** (ver entrada 14:14).

---

## Session Log: 2026-06-01 (14:14) — Refresco de marca del portal (violeta-cian + acento heredado del CRM)

### Metadata
- **Session Date:** June 1, 2026, 14:14
- **Status:** Implementado (solo frontend). Pendiente de `firebase deploy --only hosting`.
- **Affected Components:** `www/portal/portal.css`, `www/portal/index.html`, `www/portal/portal.js`
- **Repo externo relacionado:** LiliBauza-admin (CRM), `src/app/admin/citas/page.tsx`.

### 1. Objetivo
Alinear el portal con la identidad SaaS nueva (violeta-cian del rediseño de `/cita/`) y, cuando se embeba dentro del CRM LiliBauza (`/admin/citas`), que adopte el color de branding del terapeuta. Regla de diseño: **acentos = color del CRM; fondos/degradados = violeta-cian del SaaS**.

> **Corrección (misma sesión):** la primera pasada usó los colores del rediseño de `/cita/`. Al comparar el portal con el **landing** (`zotek-ia.web.app`), no coincidían: la marca real usa **cyan brillante `#00e5ff`** y fondo **slate `#0f172a`**. Se re-alineó el portal a los tokens **exactos del landing** (`www/style.css`). Valores finales abajo.

### 2. Cambios
- **`portal.css`** (alineado a la paleta de marca de `www/style.css`):
  - **Dark:** `--primary: #8b5cf6` (violet, acento interactivo legible con texto blanco), `--accent-cyan: #00e5ff`, `--bg: #0f172a` (slate-900), superficies slate (`#1e293b`/`#334155`), texto `#f1f5f9`/`#94a3b8`.
  - **Light:** `--primary: #7c3aed`, `--accent-cyan: #0891b2`, `--bg: #eef2f7`, superficies `#fff`/`#f1f5f9`.
  - `--brand-gradient`: cyan→violeta (`#00e5ff → #8b5cf6` en dark; `#0891b2 → #7c3aed` en light) — el mismo de "resuelve problemas reales" del landing.
  - `--accent: var(--primary)` (alias para la sección Horarios, que usaba `var(--accent,...)`).
  - Glows de fondo (body + login) con los valores del landing: violeta `rgba(139,92,246,.08)` + cyan `rgba(0,229,255,.08)`.
  - `--primary-dim` ahora se deriva con `color-mix(in srgb, var(--primary) N%, transparent)` → al sobrescribir `--primary` (acento del CRM), el tinte sigue al acento de forma cohesiva.
  - **Fondo SaaS sutil:** radiales violeta/cian de baja opacidad en `html, body` (`background-attachment: fixed`) y un degradado violeta-cian más marcado en la pantalla de login.
  - **Franja de marca** violeta→cian (`::after` de `.sidebar-brand`) bajo el logo.
  - `.btn-upload:hover` pasó de `rgba(108,99,255,.22)` → `var(--primary-dim)`.
- **`index.html`:** los `#6C63FF` inline (envelope-check del login, ícono KPI "citas hoy", ícono brain de "Probar Agente") → `var(--primary)` / `var(--primary-dim)`.
- **`portal.js`:** `init()` lee de la URL `?accent=<hex>` (valida `^#[0-9a-fA-F]{6}$` y hace `setProperty('--primary', ...)`) y `?theme=light|dark` (llama `applyTheme`). Limpia `sso`/`accent`/`theme` del URL con `replaceState`. Si no llegan, el portal usa su paleta violeta-cian por defecto.

### 3. Lado CRM (referencia)
- `src/app/admin/citas/page.tsx`: el iframe añade `accent=<--color-primary>` y `theme=<dark|light>` (según el modo del CRM) tanto al URL con SSO como al de fallback.

### 4. Notas
- `color-mix()` requiere navegador moderno (soportado en Chrome/Edge/Safari/Firefox actuales).
- No toca backend ni el flujo SSO (`/api/auth/sso` intacto).

---

## Session Log: 2026-06-01 (15:32) — Portal alineado al estilo REAL del landing (blobs, acento cyan, botones, efecto linterna)

### Metadata
- **Session Date:** June 1, 2026, 15:32
- **Status:** Implementado y **desplegado** (`firebase deploy --only hosting`, 3 iteraciones).
- **Affected Components:** `www/portal/portal.css`, `www/portal/index.html`, `www/portal/portal.js`
- **Referencia de marca:** `www/style.css` (landing) — fuente de verdad de la identidad Zotek.

### 1. Problema detectado (feedback del usuario, con capturas)
El portal **no se parecía** al landing `zotek-ia.web.app`. Iterando sobre las capturas se detectó:
1. El usuario seguía viendo los colores viejos → **faltaba desplegar** (los cambios estaban solo en local). Causa raíz de la confusión inicial.
2. La primera paleta usó los tonos de `/cita/` (`#7c3aed`/`#0891b2`), pero la marca real usa **cyan brillante `#00e5ff`** y fondo **slate `#0f172a`**.
3. El fondo del landing tiene un **glow teal/violeta fuerte** que el portal no tenía. Se identificó que NO son `radial-gradient` del `body`, sino **dos "blobs"** (`.bg-blobs > .blob`): un círculo **cyan arriba-izquierda** y uno **violeta abajo-derecha**, con `filter: blur(120px)` y `opacity` (0.5 dark / 0.22 light), sobre **superficies semitransparentes (glassmorphism)** con `backdrop-filter`. Es la técnica usada en TODA la web Zotek (landing, `/admin`, `/login`).
4. **El usuario rechazó los botones violetas** y aclaró la paleta de texto correcta: **cyan, azules, blancos y gris claro**.
5. Pidió el **efecto "linterna"**: una luz que sigue el cursor al pasar sobre los recuadros (en el landing es `.service-card::before` con `radial-gradient` posicionado en `var(--mouse-x/--mouse-y)` + JS `mousemove`).

### 2. Cambios finales aplicados (`portal.css`)
- **Paleta = tokens exactos del landing.** Dark: `--bg: #0f172a`, superficies slate **translúcidas** (`rgba(30,41,59,.55)` / `rgba(51,65,85,.55)`) con `backdrop-filter: blur()` en `.sidebar`, `.card`, `.kpi-card`, `.login-card`. Texto `#f1f5f9` / `#94a3b8`. Light análogo (`--bg: #eef2f7`, superficies blancas translúcidas).
- **Acento `--primary` = CYAN** (`#00e5ff` dark / `#0891b2` light) — NO violeta. Aplica a links, nav activo, foco e iconos. (`--brand-violet` se conserva solo para el blob de fondo.)
- **Botones estilo landing:** `.btn-primary` pasó de violeta a **sólido claro con texto oscuro** (`background: var(--text); color: var(--bg)`), con hover `translateY(-2px)` + sombra. Sin violeta.
- **Blobs de fondo** (`.bg-blobs` + `.blob-1` cyan / `.blob-2` violeta): replican el landing. Tras feedback se **agrandó e intensificó** el blob cyan: `760px`, `top:8% left:-14%`, `--blob-opacity: 0.65` (dark). `blur(120px)`, animación `blob-float` 20s.
- **Efecto linterna:** `.card`/`.kpi-card` con `::before` = `radial-gradient(600px circle at var(--mouse-x) var(--mouse-y), var(--spotlight), transparent 40%)`, `opacity 0 → 1` en hover. `--spotlight: rgba(0,229,255,.10)` (luz cyan). Contenido elevado con `z-index:1`.
- Se eliminaron los `radial-gradient` que había puesto en `html,body` y `#screen-login` (ahora el glow lo dan SOLO los blobs, como en el resto del sitio).

### 3. Cambios en `index.html` y `portal.js`
- **`index.html`:** se insertó el markup `<div class="bg-blobs"><div class="blob blob-1"></div><div class="blob blob-2"></div></div>` tras `<body>`. (Los `#6C63FF` inline ya estaban migrados a `var(--primary)`.)
- **`portal.js`:** listener `mousemove` delegado en `document` que calcula la posición relativa del cursor dentro de `.card`/`.kpi-card` y setea `--mouse-x`/`--mouse-y` (cubre tarjetas dinámicas). Además `init()` ya leía `?accent`/`?theme` para el embed en el CRM.

### 4. Interacción con el embed del CRM
- El acento base es cyan (standalone). Cuando el portal se embebe en el CRM y llega `?accent=<hex>`, ese color **sobrescribe `--primary`** (nav/links/iconos toman el color del terapeuta). Los **blobs y el degradado de marca** usan `--accent-cyan`/`--brand-violet` fijos → el **fondo violeta-cian de Zotek se mantiene** aunque cambie el acento. Los botones ahora son claros (no dependen del acento).

### 5. Despliegue
- `firebase deploy --only hosting --project zotek-ia` (proyecto `zotek-ia`, hosting sirve `www/`). 3 despliegues durante la iteración de afinado.

### 6. Pendiente de validación visual
- Confirmar con el usuario: botones blancos + acento cyan OK, efecto linterna visible, e intensidad del glow de fondo (ajustable vía `--blob-opacity` / tamaño del `.blob-1`).

---

## Session Log: 2026-06-01

### Metadata
- **Session Date:** June 1, 2026
- **Status:** 
  - Code: Webhook logs cleaned, frontend token parser fixed, and public appointment status page redesigned (Well.Be light-themed layout) and deployed.
  - WhatsApp: Message delivery functionality restored under the new month's free conversation allowance.
- **Affected Components:** `www/cita/cita.js`, `www/cita/index.html`, `functions/src/main.py`, `functions/src/database.py`, `functions/src/services/whatsapp_service.py`

### 1. Context & Testing
- **WhatsApp Cuota Reset:** Al iniciar el mes de junio, se restableció el límite gratuito mensual de Meta, permitiendo realizar pruebas exitosas sin necesidad de saldo.
- **Flujo de Citas:** Las citas de prueba se están generando actualmente desde el proyecto de **Lili Bauza Web**.
- **Prueba Realizada:** Se envió exitosamente el template `zotek_confirmacion_cita_v2` al número de pruebas `+52 312 317 3431`, confirmando la recepción física del mensaje en el dispositivo.
- **Verificación E2E Exitosa:** Se agendó una cita de prueba en producción desde `lilibauza.web.app`, se recibió el mensaje de confirmación por WhatsApp en el dispositivo, y al hacer clic en "Ver cita", el portal cargó de manera correcta mostrando el horario programado a las 12:00 PM local (resolviendo la URL de Meta y la zona horaria). Posteriormente, se canceló la cita desde el portal de usuario, y el horario quedó disponible nuevamente en la landing page del negocio, validando el ciclo completo.

### 2. Implementations & Code Changes
- **Corrección de URL Redundante (Frontend):**
  - **Archivos:** `www/cita/cita.js` y `www/cita/index.html`
  - **Incidencia:** La URL base configurada en Meta incluye el literal `{TOKEN}` (ej: `https://zotek-ia.web.app/cita/?t={TOKEN}`). Al concatenar el sufijo de cita `cita?t={token}`, la URL final resultaba en `.../cita/?t={TOKEN}cita?t=TOKEN_REAL`, rompiendo la carga de la cita.
  - **Solución:** Se actualizó `getToken()` en el frontend para extraer robustamente el token real al final de la URL en caso de haber redundancia o concatenaciones con placeholders de Meta. Adicionalmente, se integró un parámetro de versión (`?v=2.0.1`) como cache-buster en la importación del script en `index.html` para obligar a los navegadores a invalidar su copia en caché.
  - **Despliegue:** Se realizó deploy de hosting exitoso (`firebase deploy --only hosting`).
- **Corrección de Desfase de Zona Horaria (Backend):**
  - **Archivo:** `functions/src/main.py`
  - **Incidencia:** La columna `date_time` en la tabla `appointments` es de tipo `timestamp without time zone` y almacena las fechas en UTC (ej: las 12:00 PM local de CDMX se guarda como 18:00:00). Al consultarla por API, el backend retornaba un datetime naive `2026-06-02T18:00:00` sin offset. El navegador del cliente interpretaba esto como hora local nativa y mostraba las "6:00 PM" en lugar de las "12:00 PM".
  - **Solución:** Se ajustó el serializador de `/api/appointments/token/{token}` para dotar de zona horaria UTC al objeto datetime si es naive, y luego convertirlo explícitamente a la zona del negocio (`America/Mexico_City`) antes de exportarlo a string. Esto genera la hora local correcta con el offset correspondiente (ej: `2026-06-02T12:00:00-06:00`), haciendo que el navegador renderice las 12:00 PM exactas elegidas por el usuario.
  - **Despliegue:** Se realizó deploy de las funciones con éxito (`firebase deploy --only functions`).
- **Limpieza de Logs de Depuración (Backend):**
  - **Archivos:** `functions/src/main.py` y `functions/src/services/whatsapp_service.py`
  - **Acción:** Se removieron los prints de depuración temporales (`[WEBHOOK RAW]`, `[WEBHOOK VALUE]` y prints del payload/response de WhatsApp) para limpiar la deuda técnica, consolidando los estados del webhook bajo `logger.info`.
- **Rediseño Estético y Funcional del Portal de Citas (Frontend & Backend):**
  - **Archivos:** `www/cita/index.html`, `www/cita/cita.js`, `functions/src/database.py`, `functions/src/main.py`
  - **Requerimiento:** Modernizar el portal de visualización de citas públicas `/cita/` para alinearlo con el diseño premium de Well.Be en tonos claros y utilizar los colores de Zotek SaaS (degradados violeta/cian).
  - **Solución Backend:**
    - Se agregaron campos `c.system_instruction`, `c.vapi_professional_phone`, `c.email_user`, `c.calendly_url` al query en `database.py`.
    - Se implementó un parser con expresiones regulares en `main.py` para extraer la ubicación física (`business_address`), el teléfono (`business_phone`), el enlace directo a WhatsApp (`business_whatsapp`), el email de contacto (`business_email`) y el rubro/especialidad (`business_subtitle`) directamente de las instrucciones del prompt (`system_instruction`) del cliente de manera dinámica.
    - Se eliminan por seguridad los campos internos del JSON de respuesta antes de retornarlo al cliente para evitar fugas del prompt.
  - **Solución Frontend:**
    - Se rediseñó por completo `index.html` usando vanilla CSS para crear una cuadrícula responsiva de dos columnas (Cita y Negocio) en modo claro premium.
    - Se rediseñó `cita.js` para renderizar el nuevo diseño, añadir animaciones y skeletons de carga, crear un link dinámico de "Agregar a Google Calendar", incrustar un mapa interactivo dinámico de Google Maps en un iframe usando la dirección física extraída y añadir un botón flotante verde para contactar por WhatsApp.

### 3. Walkthrough & Verification (Rediseño de Cita)
- **Validación del Backend:**
  - Se realizó una consulta directa al endpoint de producción `https://zotek-ia.web.app/api/appointments/token/c7b412cf-f08f-4e56-ba42-725dc88968c8`.
  - El JSON devuelto contiene correctamente todos los campos parsed:
    - `business_address`: "Ceiba 105, Colonia Leandro Valle, Villa de Álvarez, Colima"
    - `business_phone`: "312 145 6877"
    - `business_whatsapp`: "https://wa.me/523121456877"
    - `business_subtitle`: "Trauma y conducta compulsiva"
    - `business_email`: "lilibauza@gmail.com"
  - La propiedad `system_instruction` fue eliminada de la respuesta por seguridad de manera exitosa.
- **Validación del Frontend:**
  - El portal carga correctamente en la URL pública: `https://zotek-ia.web.app/cita/?t=c7b412cf-f08f-4e56-ba42-725dc88968c8`.
  - Se visualizan las dos columnas (detalles de la cita a la izquierda con banner en degradado violeta/cian y mapa dinámico + detalles del profesional a la derecha).
  - El mapa de Google Maps interactivo se renderiza correctamente incrustando la dirección física mediante un iframe.
  - El botón de Google Calendar redirige a la plantilla de creación de eventos con la fecha/hora y ubicación precargadas en formato UTC.
  - El botón verde de WhatsApp redirige a `https://wa.me/523121456877` para establecer contacto directo.
  - El botón de "Cancelar Cita" se muestra y funciona llamando al modal de confirmación correspondiente.

---

## Session Log: 2026-05-25 (Zotek Project)

### Metadata
- **Session Date:** May 25, 2026
- **Status at Session Close:** 
  - Code: 100% correct, functional, and verified.
  - Blocker: Blocked by Meta pending payment approval.
- **Affected Components:** `P-04`, `P-04A`, `P-04B`, `P-06`, `INF-05`, `INF-06`, `WA-01`

## 1. Implementations & Code Changes

### Components: `P-04` / `WA-01` — Template `zotek_confirmacion_cita_v2`
The template was approved by Meta with a structural change from version 1:
- **Body:** 4 sequential variables (`nombre_cliente`, `business_name`, `fecha_larga`, `hora`). It **no longer** contains a URL in the body text.
- **Dynamic URL Button:** "Ver cita" mapping to a dynamic suffix: `cita?t={token}`.

### Codebase Modifications

#### File: `functions/src/services/whatsapp_service.py`
- Refactored function: `enviar_template_whatsapp`
- Added input parameter: `url_suffix=None`
- **Logic Added:** If `url_suffix` is provided, inject the following component block to specify the dynamic URL button parameter:
  ```json
  {
    "type": "button",
    "sub_type": "url",
    "index": "0",
    "parameters": [
      {
        "type": "text",
        "text": "url_suffix_value"
      }
    ]
  }
  ```
  *Note: Meta automatically concatenates this suffix with the base URL configured in the template dashboard.*

#### File: `functions/src/main.py`
Updated two distinct call sites to route the new payload schema:
1. **Call Site 1 (`P-04A` ~L2033):** Inside the bot flow. Passes variables `[nombre_cliente, business_name, dia_long, start_time]` and keyword argument `url_suffix=f"cita?t={token}"`.
2. **Call Site 2 (`P-04B` ~L2245):** Inside the REST API endpoint. Passes matching variables and the exact same `url_suffix` pattern.

---

## 2. Debugging & Root Cause Analysis

### Issue Definition
- **Symptom:** Meta API returns HTTP `200` with `message_status: "accepted"`, but the end-user (patient) device never receives the message.

### Step-by-Step Diagnostic Path
1. **Payload Verification:** Checked Cloud Run runtime logs. Outbound payload structure to Meta was confirmed correct:
   ```json
   {
     "to": "523123173431",
     "template": {
       "name": "zotek_confirmacion_cita_v2",
       "components": [
         {
           "type": "body",
           "parameters": [/* 4 text parameters */]
         },
         {
           "type": "button",
           "sub_type": "url",
           "index": "0",
           "parameters": [
             {
               "type": "text",
               "text": "cita?t=UUID"
             }
          ]
         }
       ]
     }
   }
   ```
2. **Webhook Telemetry Visibility:** Delivery status webhooks were absent from standard outputs. Discovered they were locked behind `logger.debug` levels, which are hidden in production Cloud Run environments. 
   - *Action taken:* Upgraded target lines to `logger.info` and embedded strategic diagnostic print statements into the webhook handler.
3. **Webhook Response Capture:** Captured Meta's asynchronous callback payload (emitted ~8 seconds post-dispatch). The raw payload revealed the core failure vector:
   ```python
   [WEBHOOK STATUS] status=failed
   errors=[{
     'code': 131042,
     'title': 'Business eligibility payment issue',
     'message': 'Message failed to send because there were one or more errors related to your payment method.'
   }]
   ```

### Root Cause
- **Error Code:** `131042` (Meta Billing Exception).
- **Explanation:** The WhatsApp Business Account (WABA) for Zotek had no active payment method linked. While standard text messages within the 24-hour window are free, HSM Templates carry costs. The standard free tier allocation (1,000 conversations/month per WABA) was exhausted during testing in this session.

---

## 3. Resolution & Financial Actions

### Target Meta Entities
- **Billing Account ID:** ZOBotek (`1575472160399413`)
- **WABA ID:** ZOBotek (`1859208218027456`)

### Mitigation Executed
- Linked a Mastercard ending in `···· 2725`.
- Meta generated an initial funding transaction requirement of **MX$400**.
- **Current State:** The transaction is flagged as "Pending" inside Meta's Billing Hub, awaiting banking network authorization.

---

## 4. Meta Billing Model Specifications (`BIZ-03`)
- **Session Types:** Inbound text conversations (within 24 hours) are free. Outbound templates (business-initiated sessions) incur charges per conversation.
- **Limits:** Free allowance tier covers 1,000 conversations per month per number. Beyond this, an active payment account is mandatory.
- **Model Type:** Prepaid wallet. Current balance is `MX$0`. Minimum top-up baseline is `MX$400`.
- **Projection:** For typical early-stage client usage (e.g., Lili Bauza handling ~50-100 appointments/month), a single MX$400 deposit is projected to sustain several months of notifications.

---

## 5. SaaS Business Model Confirmations (`BIZ-01` to `BIZ-05`)
- **Number Architecture (`BIZ-01`):** Shared infrastructure model. All clients route through the primary Zotek business number. Clients do not need individual WhatsApp setups.
- **Interaction Flow:** Notifications are explicitly one-way templates embedded with the "Ver cita" web URL action link redirecting to `zotek-ia.web.app/cita?t=TOKEN`.
- **Bot Behavior:** This channel operates as an informational/notification system, not a conversational chatbot. Cancellation requests are handled on the landing page via web interface (`P-05`).
- **Pricing Strategy (`BIZ-02`):** Flat rate of `~$500 MXN/month` per client. Meta conversation fees are absorbed as infrastructure overhead.
- **Extensibility Planning (`BIZ-04`):** The relational database architecture already contains pre-provisioned data fields (`wa_token`, `phone_number_id`) to support isolated, dedicated customer numbers in future updates.

---

## 6. Deployment Ledger
The following modifications were shipped in this session:


| # | Change Identifier | Result / Verification |
|---|-------------------|-----------------------|
| 1 | Template v2 Payload Integration | Meta API accepts payload signature natively (HTTP 200) ✅ |
| 2 | Telemetry Payload/Response Logging | `whatsapp_service.py` outputs correct JSON structure ✅ |
| 3 | Webhook Severity Escalation | Migrated `logger.debug` -> `logger.info` for deployment visibility ✅ |
| 4 | Diagnostic Print Insertion | Temporary diagnostic lines exposed Error Code `131042` ✅ |

---

## 7. Next Session Backlog & Tasks

### [ ] Step 1: Verification of Meta Payment Processing
- Review the Meta Billing Hub to verify that the balance state migrated from "Pending" to cleared funds.

### [ ] Step 2: Live Delivery E2E Testing
- Trigger a test appointment lifecycle in staging/prod.
- Verify cloud logger output explicitly traces: `[WEBHOOK STATUS] status=sent` or `status=delivered` (and confirms the absence of `status=failed`).

### [ ] Step 3: Codebase Clean-up & Technical Debt Reduction
- **File:** `functions/src/main.py`
  - Remove temporary print log: `[WEBHOOK RAW]`
  - Remove temporary print log: `[WEBHOOK VALUE]`
  - Standardize `[WEBHOOK STATUS]` log line as a permanent production `logger.info` instruction.
- **File:** `functions/src/services/whatsapp_service.py`
  - Remove production verbose print log: `[WA TEMPLATE] Payload:`
  - Remove production verbose print log: `[WA TEMPLATE] Response ...:`

### [ ] Step 4: Source Control Commit
- Execute a comprehensive Git commit encapsulating all updates from this session:
  - Template v2 logic (`P-04`)
  - Public cancellation endpoints (`P-05`)
  - Diagnostic logging architecture (`P-06`)

---

## Session Log: 2026-06-02 (11:30) — Anti-FOUC: Eliminar flash de login en portal embebido

### Metadata
- **Session Date:** June 2, 2026, 11:30
- **Status:** Implementado y desplegado en producción.
- **Affected Components:** `www/portal/index.html`, `www/portal/portal.js`
- **Commit:** `152575e` (rama `feature/admin-client-tabs-ui`)

### 1. Problema Identificado
El usuario reportó que al dar clic en **Citas** dentro del CRM LiliBauza (`/admin/citas`), el portal embebido mostraba la pantalla de login por 1-2 segundos antes de cargar el dashboard. Causa raíz: el HTML se renderiza completo (con login visible por defecto) mientras el JavaScript ejecuta `init()` y procesa el token SSO.

### 2. Solución: Anti-FOUC con Spinner
Se implementó un patrón de "Anti-FOUC" (Flash of Unstyled Content) con spinner minimalista:

**Cambios en `index.html`:**
- Agregar `<style>` inline en `<head>` que oculta el body inicialmente: `body { visibility: hidden; }`
- Crear un div `#sso-loading` con spinner centrado y fondo opaco que cubre la pantalla
- El spinner muestra un icono FontAwesome de carga + texto "Autenticando..."

**Cambios en `portal.js`:**
- Nueva función `hideSSOMLoadingSpinner()` que:
  - Oculta el div `#sso-loading` con `display: none`
  - Restaura visibilidad del body con `visibility: visible`
- Llamar `hideSSOMLoadingSpinner()` en **todos los caminos** de `init()`:
  - Al completar SSO exitosamente
  - Si hay sesión en localStorage (usuario ya autenticado)
  - En el flujo de fallback (mostrar login manual)

### 3. UX Resultado
- **Antes:** Parpadeo inicial de login → pausa de 1-2s → dashboard aparece
- **Después:** Spinner elegante "Autenticando..." → dashboard carga sin interrupciones visuales

El spinner usa colores de la marca (`--bg` para fondo, `--primary` para spinner) → se integra con el branding del portal.

### 4. Despliegue
- Commit a rama `feature/admin-client-tabs-ui` + push a GitHub (`official` remote)
- Deploy: `firebase deploy --only hosting --project zotek-ia` ✅ completado en ~30s
- Hosting URL: `https://zotek-ia.web.app` (portal disponible en producción)

### 5. Validación
- Pendiente: usuario valida que el embed en `/admin/citas` del CRM cargue sin flash (será visible después del deploy del CRM con `npm run deploy`)
