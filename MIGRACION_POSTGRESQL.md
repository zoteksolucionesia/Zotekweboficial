# 🔄 MIGRACIÓN COMPLETADA: Firebase Firestore → PostgreSQL (InsForge)

## 📋 Resumen

El proyecto ha sido migrado exitosamente de Firebase Firestore a PostgreSQL (InsForge). Firebase ahora se usa **exclusivamente para hosting**, no para almacenamiento de datos.

---

## ✅ Cambios Realizados

### 1. **Base de Datos**

| Archivo | Antes | Ahora |
|---------|-------|-------|
| `functions/src/database.py` | Firebase Firestore | PostgreSQL (InsForge) |
| `src/database.py` | PostgreSQL | PostgreSQL (sin cambios) |
| `functions/src/services/whatsapp_service.py` | Logs a Firestore | Sin logs a Firestore |

### 2. **Estructura de Datos**

**Firestore (Antiguo):**
```
clients/{client_id}
  - name
  - whatsapp_token
  - phone_number_id
  └── config/menu (subcolección)
  └── knowledge (subcolección)
  └── chats (subcolección)
```

**PostgreSQL (Nuevo):**
```sql
clients
  - id (SERIAL)
  - name
  - whatsapp_token
  - phone_number_id
  - menu_json (JSONB)
  - is_active
  └── knowledge_base (tabla relacionada)
  └── client_chats (tabla relacionada)
  └── sandbox_sessions (tabla separada)
```

### 3. **Archivos Obsoletos (No Eliminar, No Usar)**

Estos archivos existen pero **NO deben usarse** porque apuntan a Firestore:

- `migrate_to_firestore.py` - Obsoleto
- `migrate_final.py` - Obsoleto
- `query_firestore.py` - Obsoleto
- `fix_firestore_branding.py` - Obsoleto
- `generate_demos_firestore.py` - Obsoleto
- `import_demos_to_firestore.py` - Obsoleto

---

## 🔧 Configuración Requerida

### 1. **Variable de Entorno DATABASE_URL**

Debes configurar `DATABASE_URL` en Firebase Functions:

```bash
# Opción A: Usando Firebase CLI
firebase functions:config:set database.url="postgresql://usuario:password@host.insforge.dev:5432/dbname"

# Opción B: En Firebase Console
# Ir a: https://console.firebase.google.com/project/zotek-ia/functions/settings
# Agregar variable de entorno: DATABASE_URL
```

### 2. **Archivo .env (Desarrollo Local)**

Crea un archivo `.env` en la raíz del proyecto basado en `.env.example`:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales reales:

```env
DATABASE_URL=postgresql://usuario:password@host.insforge.dev:5432/zotek_db
GEMINI_API_KEY=tu_api_key_aqui
VERIFY_TOKEN=zotek_verify_token_2026
SECRET_KEY=ZotekSolucionesIA_SecretKey_2026_CambiaEsto
ADMIN_EMAIL=zoteksolucionesia@gmail.com
ADMIN_PASSWORD=TuContraseñaSegura
EMAIL_APP_PASSWORD=tu_app_password
```

---

## 📊 Tablas en PostgreSQL

El sistema crea automáticamente las siguientes tablas al inicializar:

| Tabla | Descripción |
|-------|-------------|
| `clients` | Información de clientes y bots |
| `knowledge_base` | Base de conocimientos (PDFs, textos) |
| `citas` | Citas agendadas |
| `message_logs` | Logs de mensajes para métricas |
| `conversation_history` | Historial de conversaciones |
| `sandbox_sessions` | Sesiones de demos |
| `client_chats` | Historial de chats por cliente |

---

## 🚀 Deploy a Firebase Functions

1. **Configurar variables de entorno:**
   ```bash
   firebase functions:config:set \
     database.url="postgresql://..." \
     gemini.api_key="..." \
     verify.token="..."
   ```

2. **Deploy:**
   ```bash
   cd functions
   firebase deploy --only functions
   ```

3. **Verificar logs:**
   ```bash
   firebase functions:log
   ```

---

## 🧪 Pruebas de Verificación

### 1. Test de Conexión a PostgreSQL

```bash
cd functions/src
python database.py
```

Debe mostrar:
```
🗄️ Inicializando base de datos PostgreSQL (InsForge)...
✅ Base de datos PostgreSQL inicializada (Tablas verificadas).
```

### 2. Test de WhatsApp

```bash
curl "https://REGION-zotek-ia.cloudfunctions.net/api/test-whatsapp?to=523123173431"
```

### 3. Verificar Clientes en PostgreSQL

```bash
python check_clients.py  # Actualizar para usar PostgreSQL
```

---

## 🔍 Diagnóstico de Problemas

### Los bots no responden

1. **Verificar DATABASE_URL:**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.environ.get('DATABASE_URL'))
   ```

2. **Verificar clientes en PostgreSQL:**
   ```sql
   SELECT id, name, phone_number_id, is_active FROM clients;
   ```

3. **Verificar logs de Firebase Functions:**
   https://console.firebase.google.com/project/zotek-ia/functions/logs

### Error "DATABASE_URL no está configurada"

- Asegúrate de configurar la variable en Firebase Console
- O crea un archivo `.env` para desarrollo local

### Error de conexión SSL

- Asegúrate de usar `sslmode=require` en la conexión
- Verifica que el host de InsForge permita conexiones externas

---

## 📝 Notas Importantes

1. **Firebase Firestore ya no se usa** - Los datos están en PostgreSQL
2. **Firebase Hosting sí se usa** - Para servir el frontend
3. **Firebase Functions sí se usa** - Para el webhook y API
4. **Los scripts `*firestore*.py` son obsoletos** - No eliminarlos pero no usarlos

---

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs en Firebase Console
2. Verifica que DATABASE_URL esté configurada
3. Ejecuta `python database.py` para test de conexión
4. Consulta la documentación de InsForge para problemas de conexión PostgreSQL

---

**Fecha de migración:** Marzo 2026
**Migrado por:** Zotek Soluciones IA Team
