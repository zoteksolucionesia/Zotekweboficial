# 🔍 Auditoría PHP/CodeIgniter 4

## ¿Qué es?

Herramienta de auditoría **específica para PHP 8.2+ y CodeIgniter 4** que detecta:

- 🔒 Problemas de seguridad específicos de CI4
- 🐛 Bugs comunes en PHP
- 👃 Code smells de CodeIgniter
- ✅ Best practices de PHP 8.2

**Especializada para tus proyectos CI4.**

---

## 🚀 Inicio Rápido

### Paso 1: Copiar la Skill

```bash
# Copia esta carpeta a tu proyecto CI4
cp -r skills/auditoria-php-ci4 /tu/proyecto-ci4/
```

### Paso 2: Ejecutar la Auditoría

```bash
# Proyecto completo
node skills/auditoria-php-ci4/audit-script.js

# Solo app/
node skills/auditoria-php-ci4/audit-script.js ./app

# Solo controladores
node skills/auditoria-php-ci4/audit-script.js ./app/Controllers
```

### Paso 3: Revisar Reporte

```bash
# Ver reporte
cat AUDIT_REPORT_CI4.md

# O abrir en editor
code AUDIT_REPORT_CI4.md
```

---

## 📊 ¿Qué Detecta?

### 🔒 Seguridad CI4 (12 reglas)
- CSRF deshabilitado
- Validación de input faltante
- Escape de output faltante
- Query builder sin sanitizar
- Raw SQL queries
- Upload sin validación
- Session config expuesta
- Environment en producción
- Debug mode activado
- Logs con datos sensibles
- Rutas sin autenticación
- Permisos de archivos incorrectos

### 🐛 Bugs CI4 (10 reglas)
- Modelos sin return type
- Controladores sin validación
- Vistas sin escape
- Helpers mal utilizados
- Filters no aplicados
- Events mal configurados
- Database config incorrecta
- Routes no optimizadas
- Autoloader config incorrecta
- Exceptions no manejadas

### ✅ PHP 8.2+ (8 reglas)
- Falta de tipos en funciones
- Falta de tipos en propiedades
- No usar readonly properties
- No usar enums
- No usar match expressions
- No usar nullsafe operator
- No usar named parameters
- Código deprecated de PHP 7

---

## 📄 Ejemplo de Salida

```
🔍 Auditoría PHP/CodeIgniter 4 v1.0.0
========================
📁 Directorio: ./app
📝 Framework detectado: CodeIgniter 4

📂 Buscando archivos PHP...
✅ 45 archivos encontrados

🔬 Analizando archivos...
   Progreso: 45/45 archivos

📊 Calculando métricas...
📝 Generando reporte...

✅ ¡Auditoría completada!
========================
📄 Reporte guardado en: AUDIT_REPORT_CI4.md

📊 Resumen:
   Archivos: 45
   Líneas: 8,542
   Issues: 89
   - Críticos: 8
   - Mayores: 35
   - Menores: 46

🚨 ATENCIÓN: Hay issues críticos que deben atenderse
```

---

## 🔧 Comandos Útiles

### Auditoría Básica:
```bash
# Todo el proyecto
node skills/auditoria-php-ci4/audit-script.js

# Solo app/
node skills/auditoria-php-ci4/audit-script.js ./app
```

### Por Categoría:
```bash
# Solo seguridad
node skills/auditoria-php-ci4/audit-script.js --category=security

# Solo bugs
node skills/auditoria-php-ci4/audit-script.js --category=bugs

# Solo PHP 8.2
node skills/auditoria-php-ci4/audit-script.js --category=php8
```

### Por Carpeta:
```bash
# Solo controladores
node skills/auditoria-php-ci4/audit-script.js ./app/Controllers

# Solo modelos
node skills/auditoria-php-ci4/audit-script.js ./app/Models

# Solo vistas
node skills/auditoria-php-ci4/audit-script.js ./app/Views
```

---

## 📁 Archivos Incluidos

```
skills/auditoria-php-ci4/
├── SKILL.md              ← Documentación completa
├── README.md             ← Esta guía
├── audit-script.js       ← Script principal
└── templates/
    ├── report.md         ← Plantilla de reporte
    └── checklist.md      ← Checklist CI4
```

---

## ✅ Checklist de Uso

- [ ] Copiar carpeta `auditoria-php-ci4` a tu proyecto CI4
- [ ] Verificar Node.js >= 18
- [ ] Ejecutar: `node skills/auditoria-php-ci4/audit-script.js`
- [ ] Revisar `AUDIT_REPORT_CI4.md`
- [ ] Priorizar issues (críticos > mayores > menores)
- [ ] Corregir y re-auditar

---

## 📞 Soporte

¿Problemas?

1. Verifica Node.js: `node --version` (debe ser v18+)
2. Verifica que es proyecto CI4: `ls app/Config/Paths.php`
3. Lee la documentación completa en `SKILL.md`

---

**Creado:** Marzo 2026  
**Versión:** 1.0.0  
**Específico para:** PHP 8.2+ y CodeIgniter 4  
**Tiempo de auditoría:** 3-8 minutos
