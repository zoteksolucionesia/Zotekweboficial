# AGENTS.md — Guía y bitácora para agentes (Zotek Soluciones IA)

> **Este repositorio es público.** No escribas aquí contraseñas, claves, tokens, cadenas de
> conexión, correos personales ni identificadores de proyectos. Los secretos viven en
> `functions/.env` y `.env` (ignorados por git) y en la consola de cada servicio.

Última actualización: 2026-10-28.

---

## 1. Arquitectura (resumen)

| Pieza | Dónde vive | Notas |
|---|---|---|
| Sitio web (landing, admin, portal, citas) | `www/` → **Firebase Hosting**, sitio `zotek-ia` (`https://zotek-ia.web.app`) | Estático. Reglas en `firebase.json` (`/cita`, `/login`, `/admin-control`, `/dashboard`, `/api/**`, `/webhook`). |
| Bot de WhatsApp + API | `functions/src/` (FastAPI) publicado como función de Firebase `api_handler` (corre sobre Cloud Run) | Código principal: `functions/src/main.py`. |
| Backend SaaS | `src/` (FastAPI) con `Dockerfile` para Cloud Run | Segundo despliegue; ambos están en producción. |
| Base de datos | PostgreSQL (Supabase) vía **una sola variable `DATABASE_URL`** (psycopg2) | Se lee de `functions/.env` en el bot. |
| Mensajería | WhatsApp Cloud API (Meta); Instagram en preparación | Número oficial de Zotek. |
| IA | Gemini | Ver notas de modelo en la memoria del proyecto. |

El panel admin **no usa usuarios en la base de datos**: ver sección 3.

---

## 2. Base de datos — estado y migración

**Historia.** El proyecto Supabase original ("ZOTEK AI") se pausó por inactividad (plan gratuito) y
dejó de existir: el pooler responde `tenant/user … not found`. Los datos se rescataron desde el
backup descargado del dashboard (`db_cluster-*.backup.gz`, SQL plano de todo el clúster).

**Nueva base.** Proyecto Supabase nuevo llamado "ZOTEK AI", en una organización nueva, región
`us-east-1`. Se restauró **solo el esquema `public`** (los esquemas internos de Supabase —`auth`,
`storage`, `realtime`, `vault`…— se dejaron fuera porque ya existen en el proyecto nuevo y
ninguna política de `public` depende de `auth.uid()`).

Contenido restaurado (14 tablas, 887 filas, según el backup del 2026-08-06):

| Tabla | Filas | Tabla | Filas |
|---|---|---|---|
| appointments | 36 | email_templates | 12 |
| citas | 13 | knowledge_base | 3 |
| client_chats | 217 | lead_tracking | 0 |
| client_schedules | 32 | message_logs | 140 |
| clients | 8 | sandbox_sessions | 6 |
| consumo_eventos | 0 | tarifas_cliente | 0 |
| conversation_history | 418 | verification_codes | 2 |

Lo ocurrido después del 2026-08-06 no está en el backup.

**Cómo se restauró (repetible).**
1. `psql` 17 instalado con `winget` (solo herramientas de línea de comandos, ruta
   `C:\Program Files\PostgreSQL\17\bin\psql.exe`).
2. Se separaron los bloques `Schema: public` del volcado (cada objeto va precedido de un comentario
   `-- Name: …; Type: …; Schema: …`) y se quitaron los comandos `\restrict`/`\unrestrict`.
3. Se cargó con `psql "<cadena del pooler de sesión, puerto 5432>" -f solo_public.sql` y se
   compararon los conteos por tabla. Errores esperados y inofensivos: `rls_auto_enable already
   exists` y `permission denied to change default privileges` (ALTER DEFAULT PRIVILEGES de roles
   internos).

### ⚠️ PENDIENTE CRÍTICO — cambiar la conexión del backend

`functions/.env` **todavía apunta al proyecto antiguo, que ya no existe**. Mientras no se cambie:
el panel admin no muestra registros y el bot de WhatsApp no puede leer su configuración.

Pasos (el usuario edita el secreto; no pegarlo en chats ni en git):
1. En el proyecto nuevo: *Connect → Transaction pooler* (puerto **6543**, igual que el actual;
   funciona con IPv4 desde Cloud Run). Reemplazar la contraseña. Si tiene `$`, `@`, `#`, `/` o
   `:`, codificarlos en porcentaje (`$` → `%24`). **No** añadir `?pgbouncer`.
2. Poner el resultado en la línea `DATABASE_URL=` de `functions/.env`.
3. Probar sin imprimir secretos: `psql "$DB" -c "select count(*) from public.clients"` (esperado: 8).
4. Desplegar: `firebase deploy --only functions --project zotek-ia`.
5. **Trampa conocida:** el tráfico de Cloud Run puede quedar fijado a una revisión vieja y el deploy
   no surte efecto. Comprobar y, si hace falta, `gcloud run services update-traffic <servicio>
   --to-latest --region <región>`.
6. Verificar: login admin → lista de clientes con datos; mensaje de prueba al bot de WhatsApp.
7. Revisar si el servicio de `src/` (Cloud Run) tiene su propia `DATABASE_URL` y actualizarla igual.

### Límites y cuidados de Supabase (plan gratuito)
- Máximo **2 proyectos activos por cuenta** (cuenta todas las organizaciones del usuario).
- Se **pausa tras 7 días sin actividad**; no se puede restaurar pasados ~90 días de pausa.
  → Falta un *keep-alive* (ping periódico) y backups propios con `pg_dump`.
- Alternativas evaluadas: Neon (gratis, no se pausa de forma permanente, pero sin API REST/Auth de
  Supabase y habría que cambiar código), VPS propio, Cloud SQL, Supabase Pro (25 USD/mes).

---

## 3. Acceso de administrador

- Login: `/login` → `POST /api/auth/login`. Redirige a `/admin-control`.
- Las credenciales son **variables de entorno** del backend: `ADMIN_EMAIL`, `ADMIN_EMAILS_EXTRA`
  (lista separada por comas, comparten contraseña) y `ADMIN_PASSWORD`. No hay tabla de usuarios admin.
- Si se olvida la contraseña: leerla en `functions/.env` (o `.env`) en el equipo del propietario, o
  cambiarla ahí y redesplegar las funciones.

---

## 4. Rediseño de interfaz (octubre 2026)

**Rama:** `feature/ui-ux-pro-max` (no está fusionada en `main`; ver estado de despliegue abajo).

**Skill usada:** `.claude/ui-ux-pro-max/` (buscador local de estilos, paletas y guías UX).
Ejecutar **sin** `python -I` (el script importa módulos de su carpeta):
`python ".claude/ui-ux-pro-max/scripts/search.py" "<consulta>" --design-system -p "Zotek Soluciones IA"`.
El `SKILL.md` menciona una ruta de plugin distinta; la real es `.claude/ui-ux-pro-max/scripts/search.py`.

**Sistema de diseño (fuente de verdad):** `design-system/zotek-soluciones-ia/MASTER.md`.

**Decisiones:**
- Estilo AI-Native UI con **Liquid Glass** solo en navegación y controles y **Glassmorphism** en
  tarjetas; necesitan manchas de color detrás para que el desenfoque se note.
- **Paleta tomada del logo:** azul rey `#004080`, azul `#1565C0`, cian `#00BCD4`, rosa `#FF0066`.
  Botones rosa en modo claro usan `#E6005C` (contraste 4.6:1 con texto blanco; `#FF0066` da 3.9:1).
- Tipografía: Space Grotesk (títulos) + DM Sans (texto). Sin emojis como iconos (SVG / Font Awesome).
- Modo claro y oscuro; por defecto sigue la preferencia del sistema (clave `zotek-theme` en
  `localStorage`). Respaldos: `prefers-reduced-transparency`, `@supports not (backdrop-filter)`,
  `prefers-reduced-motion`.

**Archivos por página:**

| Página | Estilos | Notas |
|---|---|---|
| Landing `www/index.html` | `www/landing.css` (nuevo) | Rediseño completo; logo SVG en línea; demo del chat. |
| Login admin `www/admin/login.html` | usa tokens de `landing.css` | JS de login intacto. |
| Panel admin `www/admin/index.html` | `www/admin/zotek_v9.css` + `www/style.css` (solo fondo) | Cambio por tokens; modo claro propio `body.light-mode`; capa de cristal al final del CSS. |
| Portal `www/portal/` | `www/portal/portal.css` | Respeta `?accent=` y `?theme=` del CRM. |
| Citas `www/cita/index.html` | CSS en línea | Solo modo claro; se conservan nombres `--zotek-*`. |
| 404 | `www/404.html` | Colores de marca. |

**Cómo se verificó:** servidor local (`python -m http.server 8765 --directory www`) + Chrome DevTools
(emulación a 390 y 1440 px, claro/oscuro) con una API simulada inyectada con `initScript` para el
panel, portal y citas. No se probaron flujos reales contra la API (login, crear/cancelar citas,
webhook).

**Pendientes de UI:** emojis dentro de textos que genera `zotek_v9.js`; páginas internas
`admin/chat-manager.html`, `debug_clients.html`, `test-menus.html` sin rediseñar; admin y portal sin
revisar en móvil de 375 px.

---

## 5. Despliegue (Firebase Hosting)

- `firebase.json` ejecuta `npm run minify` como `predeploy`: **minifica `www/` en el sitio**
  (`scripts/minify.js`, incluye `landing.css`). Después de desplegar, ejecutar **`npm run restore`**
  (`git checkout -- www/`) para recuperar el código legible. Antes de desplegar, el árbol debe estar
  limpio o se perdería trabajo sin commit.
- Solo hosting: `firebase deploy --only hosting --project zotek-ia`.
- Solo funciones: `firebase deploy --only functions --project zotek-ia` (ver trampa de Cloud Run en §2).
- Firebase manda `Cache-Control: max-age=3600` en el HTML: tras desplegar, los navegadores pueden
  mostrar la versión anterior hasta 1 hora → **Ctrl + Shift + R** o ventana privada.
- Rollback: consola de Firebase → Hosting → historial → Rollback, o `firebase hosting:rollback`.

**Estado del despliegue (2026-10-28):**
- Desplegado en producción: landing, login admin, panel admin, portal y citas, hasta el commit
  `83f1944`.
- **Sin desplegar** (solo en la rama): `e6076f0` (doble espacio en el botón "Diagnóstico gratis"),
  `38de1c2` (alineación de la lista "Pruébalos ahora en WhatsApp") y `b99b0b7` (efecto cristal en el
  panel admin).
- Producción se desplegó desde la rama, no desde `main`: falta el PR/fusión.

---

## 6. Convenciones y trampas del repositorio

- Commits convencionales (`feat`, `fix`, `chore`, `docs`…). Trabajar en rama, no directo en `main`.
- Remoto activo: `official` (repo `Zotekweboficial`, público, creado por la organización
  `zoteksolucionesia` y compartido con el usuario). El remoto `zoteksolucionesia` ya no existe y se
  quitó. `git push` debe indicar el remoto.
- Los hooks locales (`.claude/hooks/`) bloquean secretos, validan sintaxis y advierten antes de
  desplegar; GateGuard pide declarar petición, efecto y reversión antes de comandos Bash/PowerShell.
- Windows: PowerShell 5.1 sin `&&`; en contraseñas con `$` usar comillas simples en PowerShell.
- `www/style.css` ya **no** lo usa la landing; solo el panel admin (fondo de manchas).
- Memoria del proyecto del agente: carpeta `memory/` de Claude Code (no está en el repo).

---

## 7. Lista de pendientes (por prioridad)

1. **Cambiar `DATABASE_URL`** a la base nueva y redesplegar funciones (§2). Sin esto, el bot y el
   panel no leen datos.
2. Desplegar los 3 commits pendientes del rediseño y abrir el PR de `feature/ui-ux-pro-max` a `main`.
3. Programar un *keep-alive* y backups periódicos (`pg_dump`) de la base.
4. Programar el webhook de Instagram (`object == "instagram"`).
5. Probar los flujos reales con el diseño nuevo (login, citas, webhook de WhatsApp).
6. Terminar la UI pendiente (§4) y revisar admin/portal en móvil.
