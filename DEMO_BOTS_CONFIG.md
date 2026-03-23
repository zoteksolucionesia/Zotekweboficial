# 📋 CONFIGURACIÓN DE BOTS DEMO - ZOTEK IA

## ✅ ESTADO ACTUAL

### Bots Demo Configurados en PostgreSQL:

| Bot | Phone ID | ID Numérico | Menú | Token | System Instruction |
|-----|----------|-------------|------|-------|-------------------|
| **GourmetBot 2026** | `demo_restaurant` | 7 | ✅ | ✅ | ✅ |
| **SonrisaPerfecta IA** | `demo_dental` | 5 | ✅ | ✅ | ✅ |
| **MenteSana Bot** | `demo_psychology` | 6 | ✅ | ✅ | ✅ |
| **GlamourBot 2026** | `demo_salon` | 8 | ✅ | ✅ | ✅ |
| **StyleBot 2026** | `demo_retail` | 9 | ✅ | ✅ | ✅ |

---

## 🔧 ENDPOINTS API PARA EL DASHBOARD

### 1. Listar Todos los Clientes (Incluye Demos)
```http
GET /api/clients
Authorization: Bearer {token}
```

**Respuesta:**
```json
[
  {
    "id": 7,
    "name": "Demo GourmetBot 2026",
    "phone_number_id": "demo_restaurant",
    "email": "restaurante@demo.zotek.ia",
    "menu_json": {...},
    ...
  }
]
```

---

### 2. Obtener Menú de un Bot Demo
```http
GET /api/clients/demo_restaurant/menu
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "text": "¡Hola! Bienvenido a *GourmetBot 2026* 🍕...",
  "options": [
    {
      "title": "📅 Hacer Reserva",
      "icon": "📅",
      "response": "¡Excelente elección! 🎉..."
    },
    {
      "title": "🍕 Ver Menú",
      "icon": "🍕",
      "response": "¡Nuestro menú te va a encantar! 😋..."
    },
    {
      "title": "🚚 Pedido a Domicilio",
      "icon": "🚚",
      "response": "¡Te lo llevamos caliente! 🛵..."
    }
  ],
  "fallback_text": "Lo siento, no entendí esa opción..."
}
```

---

### 3. Actualizar Menú de un Bot
```http
POST /api/clients/demo_restaurant/menu
Authorization: Bearer {token}
Content-Type: application/json

{
  "text": "Nuevo texto de bienvenida",
  "options": [...],
  "fallback_text": "..."
}
```

---

### 4. Obtener Cliente Específico
```http
GET /api/clients/demo_restaurant
Authorization: Bearer {token}
```

---

## 🖥️ ADMIN PANEL

### URL de Acceso:
```
https://zotek-ia.web.app/admin-control
```

### Página de Test de Menús:
```
https://zotek-ia.web.app/admin/test-menus.html
```

Esta página permite verificar visualmente que los menús de todos los bots demo se cargan correctamente desde la API.

---

## 📊 ESTRUCTURA DE LA BASE DE DATOS

### Tabla: `clients`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | SERIAL | ID numérico único |
| `name` | TEXT | Nombre del bot |
| `phone_number_id` | TEXT | ID único del bot (ej: demo_restaurant) |
| `whatsapp_token` | TEXT | Token de WhatsApp API |
| `menu_json` | JSONB | Configuración completa del menú |
| `system_instruction` | TEXT | Instrucciones para Gemini AI |
| `email` | TEXT | Email del cliente |
| `plan` | TEXT | Plan (free, pro, enterprise) |
| `is_active` | BOOLEAN | Estado del bot |

---

## 🎯 FLUJO DE FUNCIONAMIENTO

### 1. Usuario escribe en WhatsApp:
```
demo restaurante
```

### 2. El webhook detecta la palabra clave:
- Busca en `demo_keyword_map`
- Encuentra `demo_restaurant`
- Carga el bot desde PostgreSQL

### 3. Obtiene el menú desde PostgreSQL:
```sql
SELECT menu_json FROM clients WHERE phone_number_id = 'demo_restaurant'
```

### 4. Envía el menú con botones por WhatsApp:
```
¡Hola! Bienvenido a *GourmetBot 2026* 🍕

¿Qué te gustaría hacer hoy?

[📅 Hacer Reserva] [🍕 Ver Menú] [🚚 Pedido a Domicilio]
```

### 5. Usuario hace clic en un botón:
- WhatsApp envía el `title` del botón
- El código busca la opción en `menu_json['options']`
- Devuelve la `response` configurada

---

## 🔑 PUNTOS CLAVE

### ✅ 100% Basado en Base de Datos:
- ❌ NO hay menús hardcodeados en el código
- ❌ NO hay respuestas fijas en el código
- ✅ TODO se lee de PostgreSQL

### ✅ Soporte para IDs String y Numéricos:
- Los bots demo usan `phone_number_id` (string): `demo_restaurant`
- Los clientes reales usan `id` (int): `7`
- La API soporta ambos: `/api/clients/demo_restaurant` y `/api/clients/7`

### ✅ Flujos Interactivos:
- Reservas con pasos múltiples (fecha → personas → horario → nombre)
- Sesiones persistentes en `sandbox_sessions`
- Soporte para salir con "salir"

---

## 🛠️ AGREGAR NUEVO BOT DEMO

### Paso 1: Insertar en PostgreSQL
```sql
INSERT INTO clients (
    name, 
    phone_number_id, 
    whatsapp_token, 
    menu_json, 
    system_instruction,
    email,
    plan
) VALUES (
    'Demo Nuevo Bot',
    'demo_nuevo',
    'MISMO_TOKEN_DE_ZOTEK',
    '{
        "text": "¡Hola! Soy el Demo Nuevo Bot...",
        "options": [
            {"title": "Opción 1", "icon": "🎯", "response": "Respuesta 1"},
            {"title": "Opción 2", "icon": "⭐", "response": "Respuesta 2"}
        ],
        "fallback_text": "No entendí..."
    }'::jsonb,
    'Eres el asistente virtual del Demo Nuevo Bot...',
    'nuevo@demo.zotek.ia',
    'free'
);
```

### Paso 2: Agregar palabra clave en el código
En `functions/src/main.py`:
```python
demo_keyword_map = {
    "restaurante": "demo_restaurant",
    "nuevo": "demo_nuevo",  # ← Agregar esta línea
    ...
}
```

### Paso 3: Probar
Enviar WhatsApp: `demo nuevo`

---

## 📝 NOTAS IMPORTANTES

1. **Los bots demo usan el token de WhatsApp de Zotek** para poder enviar mensajes
2. **Las sesiones se guardan en `sandbox_sessions`** con `user_number` y `phone_number_id`
3. **El flujo de reserva usa `session_data['reservation_flow']`** para trackear el paso actual
4. **El comando "salir" limpia la sesión** y devuelve al usuario a Zotek

---

## 🚀 URLs IMPORTANTES

| Recurso | URL |
|---------|-----|
| **Admin Panel** | https://zotek-ia.web.app/admin-control |
| **Test Menús** | https://zotek-ia.web.app/admin/test-menus.html |
| **Firebase Console** | https://console.firebase.google.com/project/zotek-ia |
| **Cloud Run** | https://console.cloud.google.com/run?project=zotek-ia |
| **Meta Developer** | https://developers.facebook.com/apps/ |

---

**Última actualización:** Marzo 2026
**Versión:** 1.0
