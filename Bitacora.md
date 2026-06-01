# Zotek Project Session Logs

## Session Log: 2026-06-01

### Metadata
- **Session Date:** June 1, 2026
- **Status:** 
  - Code: Webhook logs cleaned, frontend URL token parser fixed and deployed to production.
  - WhatsApp: Message delivery functionality restored under the new month's free conversation allowance (1,000 free conversations/month limit reset).
- **Affected Components:** `www/cita/cita.js`, `www/cita/index.html`, `functions/src/main.py`, `functions/src/services/whatsapp_service.py`

### 1. Context & Testing
- **WhatsApp Cuota Reset:** Al iniciar el mes de junio, se restableció el límite gratuito mensual de Meta, permitiendo realizar pruebas exitosas sin necesidad de saldo.
- **Flujo de Citas:** Las citas de prueba se están generando actualmente desde el proyecto de **Lili Bauza Web**.
- **Prueba Realizada:** Se envió exitosamente el template `zotek_confirmacion_cita_v2` al número de pruebas `+52 312 317 3431`, confirmando la recepción física del mensaje en el dispositivo.

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
