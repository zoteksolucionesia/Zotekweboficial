# Notas Zotek SolucionesIA — 20 de Mayo de 2026

**Última actualización:** 2026-05-20  
**Rama:** `feature/admin-client-tabs-ui`

---

## Pieza 2, 3 y módulo WhatsApp HSM — Confirmación de Citas (2026-05-20)

### Resumen
Cuando un usuario agenda una cita desde el widget web, se construye ahora:
1. **Pieza 2** — Mensaje de confirmación formateado con fecha, hora, nombre del negocio y link
2. **Pieza 3** — Página pública `/cita?t=TOKEN` (sin login) con detalles de la cita
3. **Plantilla WhatsApp** — `zotek_confirmacion_cita` enviada a Meta para aprobación

### Archivos implementados
- `www/cita/index.html` — Dark mode con skeleton loader y badges de estado
- `www/cita/cita.js` — Llama `GET /api/appointments/token/{token}`, renderiza en español
- `functions/src/database.py` (~línea 1090) — `get_appointment_by_token()`
- `functions/src/main.py` (~línea 2151) — endpoint `GET /api/appointments/token/{token}`
- `firebase.json` — rewrite `/cita` → `/cita/index.html`

### Plantilla WhatsApp en Meta
**Nombre:** `zotek_confirmacion_cita`  
**Categoría:** UTILITY  
**Idioma:** es_MX  
**Estado:** En revisión por Meta (aprobación típica 24-48h)

```
¡Hola {{1}}! 👋 Tu cita ha sido reservada con éxito.

🏢 *{{2}}*
📅 Fecha: {{3}}
🕐 Hora: {{4}}
🔗 Ver detalles: {{5}}

Si necesitas cancelar o cambiar tu cita, responde a este mensaje.
```

---

## Pieza 4 — Notificaciones proactivas post-cita (WA + Email) · 2026-05-20

### Código implementado

#### Función nueva: `enviar_template_whatsapp()`
**Archivo:** `functions/src/services/whatsapp_service.py` (al final)

```python
def enviar_template_whatsapp(phone_number_id, whatsapp_token, to_phone, template_name, variables, language="es_MX"):
    """Envía plantilla HSM aprobada por Meta para mensajes proactivos."""
    # Valida credenciales, construye payload con type: template, envía a Graph API v22.0
```

#### Integración en widget: Pieza 4A y 4B
**Archivo:** `functions/src/main.py` (handler `registrar_cita` dentro de `widget_chat`, ~línea 2013)

**Pieza 4A — WhatsApp proactivo:**
1. Lee teléfono del usuario (`args["telefono_contacto"]`)
2. Intenta credenciales del cliente (`client_data.whatsapp_token`)
3. Fallback a Zotek si el cliente no tiene WhatsApp: `database.get_client_by_phone_id("980996958435648")`
4. Envía plantilla `zotek_confirmacion_cita` con variables: `[nombre_cliente, business_name, fecha_y_dia, start_time, cita_url]`

**Pieza 4B — Email de confirmación:**
1. Lee email del usuario (`args["email_cliente"]`)
2. Obtiene `EmailService` del cliente (`get_email_service_for_client(client_data)`)
3. Si el cliente tiene SMTP configurado, envía email con detalles de la cita y link

### Flujo cuando está todo activo
```
Usuario agendar cita en widget
  → POST /api/widget/chat → registrar_cita()
    → create_appointment() → token UUID generado
    → Mensaje de confirmación en el chat ✅
    → enviar_template_whatsapp() → Meta API → WhatsApp usuario ✅
    → email_svc.send_email() → SMTP cliente → correo usuario ✅
```

### ⚠️ Estado y próximos pasos

**Bloqueante:** Esperar aprobación de plantilla Meta  
1. **Verificar estado en Meta Business Manager → WhatsApp → Plantillas**
   - Si **Activa**: proceder al paso 2
   - Si **En revisión**: esperar 24-48h
   - Si **Rechazada**: revisar motivo, ajustar texto, reenviar
2. **Deploy cuando esté Activa:**
   ```bash
   firebase deploy --only functions
   ```
3. **Prueba:**
   - Agendar cita en lilibauza.web.app con nombre, teléfono y correo
   - Verificar WhatsApp del usuario
   - Verificar correo (solo si lilibauza tiene SMTP configurado)
   - Abrir link `/cita?t=TOKEN`

---

## Resumen de estado del proyecto (últimas 4 semanas)

### ✅ Completado y desplegado

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-04-28 | Fix imports rotos en producción (ModuleNotFoundError) | ✅ Deployado |
| 2026-04-28 | Fix filtro "Todos los estados" en portal de citas | ✅ Deployado |
| 2026-04-28 | Mapeo de campos Supabase en portal.js | ✅ Deployado |
| 2026-04-28 | Dropdown de estado de citas (Pieza 1) | ✅ Deployado |
| 2026-05-08 | Pestaña Citas en admin (replicando portal) | ✅ Deployado v2.24 |
| 2026-05-12 | Bug Demo Bots mostraban menú de Zotek | ✅ Resuelto (sandbox_sessions UNIQUE) |
| 2026-05-19 | Fix schedules — BookingModal sin horarios | ✅ Resuelto |
| 2026-05-20 | Pieza 2, 3 — Página pública de cita + confirmación | ✅ Código hecho, no deployado |

### ⏳ En proceso

| Tarea | Bloqueado por | Próximo paso |
|---|---|---|
| Pieza 4A/4B — Notificaciones post-cita | Meta aprobación plantilla | Deploy cuando apruebe |
| Email fallback desde Zotek | Decisión | Opcional para cobertura completa |
| Recordatorio 24h antes de cita | Decisión | Futuro (Cloud Scheduler) |

### 📋 Rama actual
- **Nombre:** `feature/admin-client-tabs-ui`
- **Cambios:** Pieza 2, 3, 4 código implementado y validado
- **Pendiente:** Deploy de functions cuando Meta apruebe la plantilla

---

## Notas para la siguiente sesión

### Checklist al iniciar
- [ ] Verificar aprobación de `zotek_confirmacion_cita` en Meta
- [ ] Si aprobada: `firebase deploy --only functions`
- [ ] Si aún en revisión: esperar
- [ ] Si rechazada: leer motivo, ajustar, reenviar

### Documentación en NotebookLM
- Nota: "Módulo Confirmación de Citas — Pieza 2, 3 y WhatsApp HSM"
- Nota: "Pieza 4 — Notificaciones proactivas post-cita"

Ambas notas tienen:
- Código exacto implementado
- Variables de plantilla mapeadas
- Próximos pasos ordenados
- Referencias a archivos modificados

---

**Git user:** ZurdOmar  
**Correo:** morentinomar@gmail.com  
**Proyecto:** zotek-ia (Firebase + Cloud Run)
