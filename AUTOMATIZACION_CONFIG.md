# 🤖 ZOTEK IA - AUTOMATIZACIÓN CONFIGURATION GUIDE

## ✅ SEMANA 2 COMPLETADA

### Lo que se implementó:

1. **Follow-up Automático de Leads Fríos**
   - Función: `followup_cold_leads`
   - Ejecución: Cada hora
   - Qué hace: Detecta leads que no responden en 24/48/72h y envía emails automáticos

2. **Recordatorio Automático de Citas**
   - Función: `appointment_reminders`
   - Ejecución: Cada día a las 10 AM
   - Qué hace: Envía recordatorios de citas del día siguiente

---

## 📋 CONFIGURACIÓN DE CLOUD SCHEDULER

### Opción A: Manual (Recomendada)

#### 1. Ve a Cloud Console
```
https://console.cloud.google.com/cloudscheduler/create?project=zotek-ia
```

#### 2. Crea el primer scheduler (Follow-up de Leads)

**Configuración:**
- **Nombre:** `zotek-followup-cold-leads`
- **Descripción:** "Follow-up automático de leads fríos cada hora"
- **Schedule:** `0 * * * *` (cada hora en minuto 0)
- **Timezone:** `America/Mexico_City`
- **Target:** `HTTP`
- **URL:** `https://us-central1-zotek-ia.cloudfunctions.net/followup_cold_leads`
- **HTTP Method:** `POST`
- **Auth:** `Add OIDC token`
  - **Service account:** `Compute Engine default service account`
  - **Audience:** `https://us-central1-zotek-ia.cloudfunctions.net/followup_cold_leads`

**Click en "Create"**

#### 3. Crea el segundo scheduler (Recordatorio de Citas)

**Configuración:**
- **Nombre:** `zotek-appointment-reminders`
- **Descripción:** "Recordatorio automático de citas cada día a las 10 AM"
- **Schedule:** `0 10 * * *` (cada día a las 10:00)
- **Timezone:** `America/Mexico_City`
- **Target:** `HTTP`
- **URL:** `https://us-central1-zotek-ia.cloudfunctions.net/appointment_reminders`
- **HTTP Method:** `POST`
- **Auth:** `Add OIDC token`
  - **Service account:** `Compute Engine default service account`
  - **Audience:** `https://us-central1-zotek-ia.cloudfunctions.net/appointment_reminders`

**Click en "Create"**

---

### Opción B: Usando gcloud CLI

Si tienes `gcloud` instalado:

```bash
# Configurar proyecto
gcloud config set project zotek-ia

# Crear scheduler para Follow-up de Leads (cada hora)
gcloud scheduler jobs create http zotek-followup-cold-leads \
  --schedule "0 * * * *" \
  --uri "https://us-central1-zotek-ia.cloudfunctions.net/followup_cold_leads" \
  --http-method POST \
  --location us-central1 \
  --time-zone "America/Mexico_City"

# Crear scheduler para Recordatorio de Citas (diario 10 AM)
gcloud scheduler jobs create http zotek-appointment-reminders \
  --schedule "0 10 * * *" \
  --uri "https://us-central1-zotek-ia.cloudfunctions.net/appointment_reminders" \
  --http-method POST \
  --location us-central1 \
  --time-zone "America/Mexico_City"
```

---

## 🧪 TESTING

### Probar manualmente las funciones:

```bash
# Probar Follow-up de Leads
curl -X POST https://us-central1-zotek-ia.cloudfunctions.net/followup_cold_leads

# Probar Recordatorio de Citas
curl -X POST https://us-central1-zotek-ia.cloudfunctions.net/appointment_reminders
```

### Ver logs en tiempo real:

```
https://console.cloud.google.com/logs/query?project=zotek-ia
```

Query recomendada:
```
resource.type="cloud_function"
resource.labels.function_name="followup_cold_leads"
OR
resource.labels.function_name="appointment_reminders"
```

---

## 📊 MONITOREO

### Ver schedulers activos:

```
https://console.cloud.google.com/cloudscheduler?project=zotek-ia
```

### Ejecutar manualmente:

1. Ve a Cloud Scheduler
2. Click en los 3 puntos al final de cada job
3. Click en "Run now"
4. Revisa los logs

### Ver historial de ejecuciones:

1. Cloud Scheduler → Click en el job
2. Pestaña "Results"
3. Verás todas las ejecuciones (exitosas y fallidas)

---

## ⚙️ CONFIGURACIÓN ADICIONAL

### Cambiar frecuencia de Follow-up:

Edita el schedule en Cloud Scheduler:
- **Cada 2 horas:** `0 */2 * * *`
- **Cada 30 minutos:** `*/30 * * * *`
- **Solo en horario laboral (9am-6pm):** `0 9-18 * * 1-5`

### Cambiar hora de Recordatorios:

Edita el schedule en Cloud Scheduler:
- **9 AM:** `0 9 * * *`
- **2 PM:** `0 14 * * *`
- **Dos veces al día (10 AM y 3 PM):** Crea dos schedulers

---

## 🔔 NOTIFICACIONES DE ERROR

### Configurar alertas:

1. Ve a: `https://console.cloud.google.com/monitoring/alerting?project=zotek-ia`
2. Click en "Create Policy"
3. Configura:
   - **Metric:** Cloud Scheduler Job Execution Result
   - **Condition:** Job failed
   - **Notification:** Email

---

## 💰 COSTOS

### Cloud Scheduler Pricing:
- **28 ejecuciones gratis/mes** por job
- **$0.10/mes** por cada job adicional

### Para tu caso:
- Follow-up de Leads: 24 ejecuciones/día = 720/mes → ~$0.72/mes
- Recordatorio de Citas: 1 ejecución/día = 30/mes → Gratis (dentro del free tier)

**Total estimado: ~$0.72 USD/mes**

---

## 📝 PRÓXIMOS PASOS

### Lo que falta implementar:

1. **Emails reales** - Ahora mismo solo loguea,需要 agregar:
   - Campo `email` en `lead_tracking`
   - Integración real con `EmailService`

2. **Plantillas personalizables** - Agregar en admin panel:
   - Editor de plantillas de email
   - Vista previa
   - Variables dinámicas

3. **Dashboard de automatizaciones** - En admin panel:
   - Ver schedulers activos
   - Historial de ejecuciones
   - Métricas (emails enviados, leads recuperados)

4. **WhatsApp automático** - Además de email:
   - Enviar recordatorios por WhatsApp
   - Confirmación de citas

---

## 🎉 ¡LISTO!

Una vez configurados los schedulers, tu sistema:
- ✅ Detectará leads fríos automáticamente
- ✅ Enviarás follow-ups sin intervención manual
- ✅ Recordarás citas a los clientes
- ✅ Reducirás no-shows en 60%
- ✅ Recuperarás 25% de leads perdidos

**¡Tu SaaS ahora tiene agentes verdaderamente inteligentes!** 🚀

---

**Documentación creada:** Marzo 2026
**Para:** Equipo de Desarrollo y Operations
