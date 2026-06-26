# Árbol de Estructura del Proyecto Zotek SolucionesIA

Generado: 2026-05-18

## Resumen de Directorios Principales

```
ZotekSolucionesIA/
├── .claude/                    # Configuración Claude Code
├── .firebase/                  # Configuración Firebase
├── functions/                  # Cloud Functions (Bot vivo)
├── migrations/                 # Migraciones de base de datos
├── scripts/                    # Scripts utilitarios
├── skills/                     # Auditorías y herramientas de calidad
├── src/                        # Backend SaaS/CloudRun
└── www/                        # Frontend (admin + portal)
```

---

## Estructura Detallada

### Raíz del Proyecto
```
.
├── .claude/                            # Configuración local Claude Code
│   ├── settings.json
│   ├── settings.local.json
│   └── worktrees/
├── .env                               # Variables de entorno
├── .env.example                       # Template de variables
├── .firebase/                         # Configuración Firebase
│   ├── hosting.d3d3.cache
│   └── (config files)
├── .firebaserc                        # Proyecto Firebase activo
├── .git/                              # Repositorio Git
├── .gitignore
├── Dockerfile                         # Containerización
├── firebase.json                      # Configuración Firebase
├── firestore.indexes.json             # Índices Firestore
├── firestore.rules                    # Reglas de seguridad Firestore
├── requirements.txt                   # Dependencias Python (raíz)
└── [Múltiples documentos MD]          # Reportes, guías, auditorías
```

---

### 📦 `/functions/` — Cloud Functions (Bot Vivo)

```
functions/
├── .env                               # Variables de entorno (Cloud)
├── .firebaserc
├── __init__.py
├── __pycache__/
├── main.py                            # Punto de entrada principal
├── requirements.txt                   # Dependencias Python
├── service-account-key.json           # Credenciales Firebase
├── setup_scheduler.py
├── firebase.json
├── venv/                              # Virtual environment local
├── ZotekSolucionesIA.code-workspace
├── data/
│   └── consultorio.db                 # Base de datos SQLite local
├── src/
│   ├── __init__.py
│   ├── __pycache__/
│   ├── main.py                        # Lógica principal del bot
│   ├── database.py                    # Gestión de base de datos
│   ├── migration_v3.py                # Migraciones
│   ├── fix_reservation_flow.py
│   ├── automations/
│   │   ├── __init__.py
│   │   ├── appointment_reminders.py   # Recordatorios de citas
│   │   └── followup_leads.py          # Seguimiento de leads
│   └── services/
│       ├── __init__.py
│       ├── __pycache__/
│       ├── appointment_service.py
│       ├── email_service.py
│       ├── gemini_service.py          # Integración Gemini AI
│       ├── lead_service.py
│       └── whatsapp_service.py
├── update_db.py
├── GUIA_MIGRACION.md                  # Guía de migración Supabase
└── [Archivos de migración/configuración]
```

---

### 🌐 `/src/` — Backend SaaS/CloudRun

```
src/
├── __init__.py
├── __pycache__/
├── config.py                          # Configuración central
├── main.py                            # Punto de entrada SaaS
├── database.py                        # ORM/Base de datos
├── database_sqlite_backup.py
├── services/
│   ├── __pycache__/
│   ├── agent_tools.py                 # Herramientas para agentes
│   ├── calendar_service.py            # Integración calendarios
│   ├── encryption_service.py          # Cifrado de datos
│   ├── gemini_service.py              # Integración Gemini
│   ├── vapi_service.py                # Integración VAPI
│   └── whatsapp_service.py            # Integración WhatsApp
└── [Virtual environment local]
```

---

### 🎨 `/www/` — Frontend

```
www/
├── index.html                         # Landing page principal
├── 404.html
├── style.css
├── script.js
├── Logo-zotek_animado.svg
├── assets/
│   └── logo.svg
├── admin/                             # Dashboard de administración
│   ├── index.html                     # Main admin panel
│   ├── login.html                     # Login admin
│   ├── zotek_v9.css                   # Estilos v9
│   ├── zotek_v9.js                    # Lógica v9
│   ├── automations.js                 # Control de automatizaciones
│   ├── email-leads.js                 # Gestión de leads
│   ├── manage_clients.py              # Backend Python admin
│   ├── process_pdfs.py                # Procesamiento de PDFs
│   ├── chat-manager.html
│   ├── debug_clients.html
│   └── test-menus.html
└── portal/                            # Portal del cliente
    ├── index.html                     # Main portal
    ├── portal.css
    └── portal.js
```

---

### 📚 `/skills/` — Herramientas de Auditoría y Calidad

```
skills/
├── RESUMEN_SKILLS.md                  # Resumen de skills disponibles
├── auditoria-php-ci4/                 # Auditoría PHP CI4
│   ├── SKILL.md
│   └── README.md
├── auditoria-universal/               # Auditoría universal JavaScript
│   ├── SKILL.md
│   ├── README.md
│   └── audit-script.js
├── calidad-empresarial/               # Auditoría calidad empresarial
│   ├── SKILL.md
│   ├── README.md
│   ├── RESUMEN.md
│   ├── scripts/
│   │   └── init.js
│   └── REPORTE_HALLAZGOS_2026-03-13.md
└── code-audit/                        # Auditoría de código genérica
    ├── SKILL.md
    ├── README.md
    ├── audit-script.js
    ├── PARA_COMPARTIR.md
    ├── EMAIL_PARA_COMPARTIR.md
    └── templates/
        ├── audit-report.md
        └── checklist.md
```

---

### 📂 `/migrations/` — Migraciones de BD

```
migrations/
└── add_email_and_lead_tracking.sql    # Migración de campos
```

---

### 🛠️ `/scripts/` — Scripts Utilitarios

```
scripts/
├── diagnose_auth_state.py             # Diagnóstico de autenticación
├── fix_sequences.py                   # Reparar secuencias BD
├── migrate_encrypt_fields.py          # Migración de campos cifrados
├── smoke_test_supabase.py             # Test de Supabase
├── test_direct_connection.py          # Test de conexión
├── [Otros scripts de migración]
```

---

## Archivos de Documentación Notable

```
Raíz del Proyecto:
├── AGENTES_VS_BOTS.md                 # Diferenciación arquitectura
├── AUDIT_REPORT.md                    # Auditoría general
├── AUDIT_REPORT_FOCALIZADO.md         # Auditoría específica
├── AUTOMATIZACION_CONFIG.md           # Configuración automatizaciones
├── CORRECCIONES_REALIZADAS.md         # Historial de correcciones
├── DEMO_BOTS_CONFIG.md                # Configuración demo
├── EXECUTION_PLAN_claude.md           # Plan de ejecución
├── MIGRACION_POSTGRESQL.md            # Guía migración PostgreSQL
├── SAAS_IMPROVEMENTS.md               # Mejoras SaaS
├── SECURITY_AUDIT_claude.md           # Auditoría seguridad
├── SEMANA_2_RESUMEN.md                # Resumen semanal
├── TODO.md                            # Tareas pendientes
├── VAPI_CONFIG_GUIDE.md               # Guía configuración VAPI
└── Guia — Agentes 2026.pdf            # PDF de guía de agentes
```

---

## Configuración Localizada

Archivos que pueden variar entre ambientes:
- `.env` / `.env.example` — Variables de entorno
- `.firebaserc` — Proyecto Firebase activo
- `functions/.env` — Env específico para Cloud Functions
- `.claude/settings.local.json` — Configuración local Claude Code

---

## Tecnología Stack

| Componente | Tecnología |
|-----------|-----------|
| **Backend Cloud Functions** | Python + Firebase Functions |
| **Backend SaaS** | Python + CloudRun |
| **Frontend** | HTML/CSS/JavaScript Vanilla |
| **Base de Datos** | Supabase (PostgreSQL) + SQLite local |
| **IA** | Google Gemini API |
| **Comunicación** | WhatsApp + Email |
| **Hosting** | Firebase Hosting |
| **Voz** | VAPI |

---

## Nota sobre Arquitectura Dual

Este proyecto mantiene **dos aplicaciones principales en producción**:
1. **`functions/`** — Bot vivo (Cloud Functions)
2. **`src/`** — SaaS/CloudRun (Interfaz web + APIs)

Ambos tienen su propio `main.py` y pueden operar independientemente.

---

Fecha de generación: 2026-05-18
