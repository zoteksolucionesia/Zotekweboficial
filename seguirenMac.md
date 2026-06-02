# Lo que tienes que hacer en tu Mac

## 1. Clonar/actualizar ambos proyectos

Navega a donde quieras los proyectos (ej: `~/Proyectos`):

```bash
cd ~/Proyectos
```

### CRM
```bash
git clone -b feat/paciente-expediente-fullpage https://github.com/zoteksolucionesia/LiliBauza-admin.git
cd LiliBauza-admin
npm install  # instala dependencias
# (o si ya lo tienes: git pull origin feat/paciente-expediente-fullpage)
```

### Portal (desde ~/ o tu carpeta de proyectos)
```bash
cd ..
git clone -b feature/admin-client-tabs-ui https://github.com/zoteksolucionesia/Zotekweboficial.git
cd Zotekweboficial
# El portal es hosting estático (www/), no tiene npm install
```

---

## 2. Variables de entorno

### CRM (`.env.local` y `.env.production`)
Copia desde tu Windows:
```env
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
AI_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash-lite
ANTHROPIC_API_KEY=... # (opcional)
PORTAL_SSO_SECRET=... # (IMPORTANTE: la que compartiste en Supabase)
FIRMA_SECRET=...
RESEND_API_KEY=... # (opcional)
```

### Portal
No necesita `.env.local` (es estático). Solo verificar credenciales Firebase en `firebase.json` (ya están en el repo).

---

## 3. Desarrollo local (para probar cambios)

### CRM
```bash
cd LiliBauza-admin
npm run dev
# Abre http://localhost:3000
```

### Portal
Es estático. Para "servir" localmente:
```bash
cd Zotekweboficial

# Opción 1: usar Python
python3 -m http.server 8080 --directory www

# Opción 2: usar Node (si tienes http-server instalado)
npx http-server www -p 8080
# Abre http://localhost:8080/portal/
```

---

## 4. Despliegue en producción (cuando quieras subir cambios)

### CRM
```bash
npm run deploy  # Deploy automático con env vars inyectadas en Cloud Run
```

### Portal
```bash
firebase deploy --only hosting --project zotek-ia
```

---

## 5. Pendientes activos

| Proyecto | Pendiente | Comando |
| :--- | :--- | :--- |
| **CRM** | Deploy `npm run deploy` para que el iframe pase accent/theme en producción | `npm run deploy` |
| **Portal** | Ya desplegado (standalone luce Zotek real). Validar en tu Mac: botones/acento/efecto linterna OK | Abre `http://localhost:8080/portal/` en Mac |
| **CRM + Portal** | Probar el SSO end-to-end embebido: abrir CRM en Mac, navegar a `/admin/citas`, verificar que entra al portal sin login | Ambos dev corriendo |

---

## 6. Branches correctas

- **CRM:** `feat/paciente-expediente-fullpage` (la que estás usando)
- **Portal:** `feature/admin-client-tabs-ui` (la del Zotek oficial)

Si necesitas traer cambios del Windows al Mac después:

```bash
git pull origin <rama>
```