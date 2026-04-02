# ToDo Calendario & Mejoras Pendientes — Zotek IA

## 📅 SISTEMA DE HORARIOS (Prioridad Alta)

- [ ] **Horarios partidos por día** — Permitir configurar múltiples franjas por día (ej. 10:00-14:00 y 17:00-20:00). Modelo: tabla `client_schedules` con columnas `client_id`, `day_of_week`, `start_time`, `end_time`.
- [ ] **Vista de calendario tipo cal.com en el dashboard** — Mostrar slots ocupados/libres visualmente por semana. Citas ocupadas en color distinto.
- [ ] **Copiar horario de un día a otros días** — Botón "Copiar a..." que permita replicar las franjas de un día seleccionado a uno o varios días.
- [ ] **Mostrar slots ocupados en WhatsApp** — Cuando el bot muestre horarios, marcar visualmente cuáles ya están tomados (ej. ~~Jue 2 Abr 10:00~~ OCUPADO).
- [ ] **Zona horaria por cliente** — Configurar zona horaria del consultorio para evitar confusiones con horarios.

## 🤖 AGENTE / BOT (Prioridad Alta)

- [ ] **Google Calendar sync** — Al registrar una cita, crear evento en Google Calendar del cliente. Requiere OAuth2 Service Account setup.
- [ ] **Confirmación de cita por WhatsApp al paciente** — Mensaje automático al paciente con detalles de la cita tras registrarla (ya parcialmente implementado, verificar flujo completo).
- [ ] **Cancelación/reprogramación por WhatsApp** — El paciente puede cancelar o cambiar su cita respondiendo al bot.
- [ ] **Recordatorio 24h por WhatsApp** — Además de la llamada Twilio, enviar mensaje de texto recordatorio el día anterior.

## 🗄️ BASE DE DATOS (Prioridad Media)

- [ ] **Migrar tabla `citas` a esquema unificado** — Existe tabla legacy `citas` y referencias a tabla `appointments` (AppointmentService). Unificar en una sola.
- [ ] **Tabla `client_schedules`** — Reemplazar columnas `schedule_start/end` de clients por tabla dedicada que soporte múltiples franjas horarias por día.
- [ ] **Índice en `conversation_history`** — Agregar índice en `(phone_number, created_at)` para mejorar performance del historial.

## 🖥️ DASHBOARD (Prioridad Media)

- [ ] **Sección de Citas en el dashboard** — Vista de agenda semanal/mensual con todas las citas de todos los bots. Actualmente solo existe en `email-leads.js` con funcionalidad limitada.
- [ ] **Notificación en tiempo real de nueva cita** — Badge o toast cuando el bot registra una cita nueva.
- [ ] **Exportar citas a CSV** — Botón para descargar citas de un rango de fechas.

## 🔒 SEGURIDAD (Prioridad Media)

- [ ] **Rotar credenciales expuestas** — El `.env` actual tiene credenciales reales (tokens WhatsApp, DB, Twilio). Evaluar uso de Secret Manager para producción.
- [ ] **Verificación de firma WhatsApp en dev** — `WHATSAPP_APP_SECRET` solo se verifica en producción. Agregar opción para habilitarlo en dev.

## 📦 INFRAESTRUCTURA (Prioridad Baja)

- [ ] **Migrar a Railway.app** — El servidor actual corre en Firebase Functions (SQLite, código viejo). El nuevo stack (FastAPI + PostgreSQL InsForge + Gemini Agent + Twilio) debe desplegarse en Railway para tener servidor siempre encendido, sin cold starts, deploy automático con git push, y URL pública fija para el webhook de WhatsApp. Costo estimado: $5-10/mes. Ver `railway.toml` cuando se implemente.
- [ ] **Actualizar Python 3.9 → 3.11+** — Python 3.9 llegó a end-of-life. Google Auth y otras librerías muestran warnings. Migrar a 3.11 o 3.12.
- [ ] **Cron job para recordatorios Twilio** — El endpoint `/api/reminders/process` existe pero no hay scheduler que lo llame automáticamente en local/producción.
- [ ] **Deploy automático** — Actualmente el servidor corre manual. Configurar PM2 o systemd para que se reinicie automáticamente.
- [ ] **Rate limiting por bot** — Actualmente el rate limit es global (100/min). Hacerlo por `phone_number_id` para aislar bots.

## ✅ COMPLETADO

- [x] Servidor FastAPI local corriendo con hot-reload
- [x] Conexión a PostgreSQL (InsForge)
- [x] Autenticación JWT con 2FA por email
- [x] Subida de PDFs como base de conocimiento por bot
- [x] Historial de conversación con reset de sesión (30 min)
- [x] Herramienta `registrar_cita` — guarda cita y manda confirmación por WhatsApp
- [x] Herramienta `llamar_ahora` — llamada inmediata vía Twilio
- [x] Botones interactivos de WhatsApp (≤3 = botones, >3 = lista)
- [x] Herramienta `mostrar_horarios` — genera slots disponibles como botones
- [x] Configuración de horario por cliente desde dashboard (hora inicio/fin, duración, días laborales)
- [x] Asistente VAPI actualizado a voz Dalia (es-MX) y prompt en español
