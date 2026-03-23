# 📞 VAPI - Guía de Configuración del Asistente de Voz

## ¿Qué es VAPI? 
VAPI.ai es la plataforma que hace las llamadas de voz con IA. Zotek usará **un solo número** y **un solo asistente** para todos los clientes con plan Pro/Enterprise.

---

## Paso 1: Crear Cuenta y Obtener API Key

1. Ve a → [https://dashboard.vapi.ai](https://dashboard.vapi.ai)
2. Regístrate o inicia sesión
3. Ve a **Account → API Keys**
4. Copia la API Key y pégala en `functions/.env`:
   ```
   VAPI_API_KEY=tu_api_key_aqui
   ```

---

## Paso 2: Comprar un Número de Teléfono

1. En el dashboard de VAPI → **Phone Numbers → Buy Number**
2. Selecciona un número de México (`+52`)
3. Una vez comprado, copia el **Phone Number ID** (no el número en sí, sino el UUID)
4. Pégalo en `functions/.env`:
   ```
   VAPI_PHONE_NUMBER_ID=id_del_numero_aqui
   ```

---

## Paso 3: Crear el Asistente de Voz

1. Ve a **Assistants → Create Assistant**
2. Configura:
   - **Name:** `Zotek Recordatorio`
   - **Model:** GPT-4o-mini (recomendado por costo)
   - **Voice:** Usa una voz en español, ej. `es-MX-JorgeNeural` (ElevenLabs o Azure)

3. En el campo **System Prompt**, usa este script personalizable:
   ```
   Eres un asistente de voz amable de Zotek Soluciones IA que llama para recordar citas médicas.

   Cuando el paciente conteste, di:
   "¡Hola! Habla Sofía en nombre de {{nombre_consultorio}}. 
   Le llamo para recordarle que tiene una cita con {{nombre_profesional}} 
   {{fecha_cita}}.
   ¿Confirma que podrá asistir?"

   Si confirma: Agradece y despídete.
   Si no puede: Pregunta si quiere reagendar y ofrece que les manden un WhatsApp.
   Si no contesta: Deja un mensaje de voz amable.

   Habla siempre en español mexicano, de forma amable y profesional.
   ```

4. En **Assistant Overrides Variables**, asegúrate de que estén definidas:
   - `nombre_paciente`
   - `fecha_cita`
   - `nombre_profesional`
   - `nombre_consultorio`

5. Copia el **Assistant ID** que aparece en la URL o en los detalles del asistente y pégalo en `.env`:
   ```
   VAPI_ASSISTANT_ID=id_del_asistente_aqui
   ```

---

## Paso 4: Configurar el Webhook (para recibir resultado de la llamada)

Para que Zotek sepa si la llamada fue exitosa:

1. En VAPI → **Phone Numbers → Tu número → Server URL**
2. Agrega: `https://us-central1-zotek-ia.cloudfunctions.net/api_handler/api/vapi/webhook`
3. Esto actualizará automáticamente el estado de la cita en la BD.

---

## Paso 5: Probar la Integración

```bash
# Hacer una llamada de prueba a tu propio número
curl -X POST https://us-central1-zotek-ia.cloudfunctions.net/api_handler/api/reminders/test-call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_JWT_TOKEN" \
  -d '{
    "numero": "+5215512345678",
    "nombre_paciente": "Juan Pérez",
    "fecha_cita": "mañana a las 3 de la tarde",
    "nombre_profesional": "la Dra. González",
    "nombre_consultorio": "MenteSana Consultorio"
  }'
```

---

## Paso 6: Activar el CRON Automático (Cloud Scheduler)

Para que las llamadas se disparen automáticamente cada hora:

```bash
gcloud scheduler jobs create http zotek-vapi-reminders \
  --schedule "0 * * * *" \
  --uri "https://us-central1-zotek-ia.cloudfunctions.net/api_handler/api/reminders/run" \
  --http-method POST \
  --location us-central1 \
  --time-zone "America/Mexico_City" \
  --headers "Authorization=Bearer TU_JWT_TOKEN,Content-Type=application/json"
```

---

## Resumen de Endpoints Disponibles

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/reminders/run` | POST | Ejecuta el CRON manualmente |
| `/api/reminders/test-call` | POST | Prueba una llamada sin cita real |
| `/api/vapi/webhook` | POST | Recibe el resultado de VAPI (público) |
| `/api/clients/{id}/appointments` | GET | Lista citas del cliente |
| `/api/clients/{id}/appointments` | POST | Crea una cita nueva |

---

## Flujo Completo (Para la Psicóloga)

```
Paciente escribe por WhatsApp → Bot de Zotek agrega la cita a la BD
                                        ↓
                          24 horas antes de la cita
                                        ↓
                    Cloud Scheduler llama /api/reminders/run
                                        ↓
                    Zotek llama al paciente con número de Zotek
                                        ↓
              IA de voz recuerda la cita en nombre de la Dra.
                                        ↓
              VAPI notifica a Zotek el resultado via webhook
                                        ↓
                    BD actualizada (cita confirmada/fallida)
```

La psicóloga **no necesita configurar nada** en Meta ni comprar un número. Zotek lo gestiona todo.
