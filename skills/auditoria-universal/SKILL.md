# 🔍 SKILL: Auditoría Universal de Código

## Descripción
Skill de auditoría de código **multi-lenguaje** que funciona con:
- ✅ JavaScript/TypeScript
- ✅ PHP
- ✅ Python
- ✅ Java
- ✅ C#
- ✅ Ruby
- ✅ Go
- ✅ Y más...

**Filosofía:** "Una skill para auditarlos todos"

**Tiempo de auditoría:** 3-10 minutos (depende del tamaño del proyecto)
**Cobertura:** 80% de problemas comunes en cualquier lenguaje

---

## 📋 Reglas de Auditoría

### 🔒 Seguridad (8 reglas universales)

| ID | Regla | Aplica a | Severidad |
|----|-------|----------|-----------|
| SEC-001 | Credenciales hardcodeadas | Todos | CRÍTICO |
| SEC-002 | API keys expuestas | Todos | CRÍTICO |
| SEC-003 | Contraseñas en código | Todos | CRÍTICO |
| SEC-004 | Tokens de acceso hardcodeados | Todos | CRÍTICO |
| SEC-005 | Datos sensibles en logs | Todos | MAYOR |
| SEC-006 | SQL dinámico sin sanitizar | PHP, JS, Python | CRÍTICO |
| SEC-007 | Eval/execute dinámico | PHP, JS, Python | MAYOR |
| SEC-008 | Rutas con información sensible | Todos | MENOR |

---

### 🐛 Bugs (8 reglas universales)

| ID | Regla | Aplica a | Severidad |
|----|-------|----------|-----------|
| BUG-001 | Variables no inicializadas | Todos | MAYOR |
| BUG-002 | Funciones sin retorno | Todos | MENOR |
| BUG-003 | Catch vacío o sin manejar | Todos | MAYOR |
| BUG-004 | Console.log/print en producción | Todos | MENOR |
| BUG-005 | Código muerto/inaccesible | Todos | MENOR |
| BUG-006 | Imports no utilizados | JS, TS, PHP, Python | MENOR |
| BUG-007 | Variables no utilizadas | Todos | MENOR |
| BUG-008 | Condiciones siempre verdaderas/falsas | Todos | MAYOR |

---

### 👃 Code Smells (8 reglas universales)

| ID | Regla | Aplica a | Severidad |
|----|-------|----------|-----------|
| SMELL-001 | Archivos muy grandes (>500 líneas) | Todos | MAYOR |
| SMELL-002 | Funciones/métodos muy largos (>50 líneas) | Todos | MAYOR |
| SMELL-003 | Clases muy grandes (>300 líneas) | OOP | MAYOR |
| SMELL-004 | Anidamiento excesivo (>4 niveles) | Todos | MENOR |
| SMELL-005 | Magic numbers | Todos | MENOR |
| SMELL-006 | Nombres muy cortos (<2 chars) | Todos | MENOR |
| SMELL-007 | Nombres muy largos (>50 chars) | Todos | MENOR |
| SMELL-008 | Comentarios TODO/FIXME | Todos | MENOR |

---

## 🚀 Inicio Rápido

### Paso 1: Copiar la Skill

```bash
# Copia esta carpeta a tu proyecto
cp -r skills/auditoria-universal /tu/proyecto/
```

### Paso 2: Ejecutar la Auditoría

```bash
# Auditoría completa del proyecto
node skills/auditoria-universal/audit-script.js

# Auditoría de carpeta específica
node skills/auditoria-universal/audit-script.js ./src

# Auditoría de lenguaje específico
node skills/auditoria-universal/audit-script.js --lang=php ./src
node skills/auditoria-universal/audit-script.js --lang=js ./src
```

### Paso 3: Revisar Reporte

```bash
# Ver reporte en terminal
cat AUDIT_REPORT_UNIVERSAL.md

# O abrir en editor
code AUDIT_REPORT_UNIVERSAL.md
```

---

## 📊 Ejemplo de Uso

### Proyecto PHP/CodeIgniter 4:

```bash
cd /var/www/mi-proyecto-ci4
node skills/auditoria-universal/audit-script.js ./app
```

**Salida:**
```
🔍 Auditoría Universal de Código v1.0.0
========================
📁 Directorio: ./app
📝 Lenguajes detectados: PHP

📂 Buscando archivos...
✅ 45 archivos encontrados (35 PHP, 10 JS)

🔬 Analizando archivos...
   Progreso: 45/45 archivos

📊 Calculando métricas...
📝 Generando reporte...

✅ ¡Auditoría completada!
========================
📄 Reporte guardado en: AUDIT_REPORT_UNIVERSAL.md

📊 Resumen:
   Archivos: 45
   Líneas: 8,542
   Issues: 127
   - Críticos: 12
   - Mayores: 45
   - Menores: 70

🚨 ATENCIÓN: Hay issues críticos que deben atenderse
```

---

### Proyecto React/TypeScript:

```bash
cd /home/usuario/mi-app-react
node skills/auditoria-universal/audit-script.js ./src
```

**Salida:**
```
🔍 Auditoría Universal de Código v1.0.0
========================
📁 Directorio: ./src
📝 Lenguajes detectados: TypeScript, JavaScript

📂 Buscando archivos...
✅ 28 archivos encontrados (25 TS, 3 JS)

🔬 Analizando archivos...
📊 Calculando métricas...
📝 Generando reporte...

✅ ¡Auditoría completada!
========================
📄 Reporte guardado en: AUDIT_REPORT_UNIVERSAL.md

📊 Resumen:
   Archivos: 28
   Líneas: 4,230
   Issues: 56
   - Críticos: 8
   - Mayores: 28
   - Menores: 20
```

---

### Proyecto Python/Django:

```bash
cd /opt/django-project
node skills/auditoria-universal/audit-script.js ./myapp
```

**Salida:**
```
🔍 Auditoría Universal de Código v1.0.0
========================
📁 Directorio: ./myapp
📝 Lenguajes detectados: Python

📂 Buscando archivos...
✅ 18 archivos encontrados

🔬 Analizando archivos...
📊 Calculando métricas...
📝 Generando reporte...

✅ ¡Auditoría completada!
========================
📊 Resumen:
   Issues: 34
   - Críticos: 5
   - Mayores: 15
   - Menores: 14
```

---

## 🔧 Configuración Avanzada

### Archivo de Configuración

Crea `.auditrc.json` en la raíz del proyecto:

```json
{
  "languages": ["php", "js", "ts", "py"],
  "exclude": [
    "node_modules",
    "vendor",
    "dist",
    "build",
    ".git",
    "tests",
    "*.test.js",
    "*.spec.ts"
  ],
  "limits": {
    "maxFileLines": 500,
    "maxFunctionLines": 50,
    "maxClassLines": 300,
    "maxNestingLevel": 4
  },
  "rules": {
    "SEC-001": "error",
    "SEC-002": "error",
    "BUG-001": "warn",
    "SMELL-001": "warn"
  },
  "output": {
    "format": "markdown",
    "file": "AUDIT_REPORT.md"
  }
}
```

---

## 📄 Estructura del Reporte

El reporte generado incluye:

### 1. Resumen Ejecutivo
```markdown
## Resumen

| Métrica | Valor |
|---------|-------|
| Archivos analizados | 45 |
| Líneas de código | 8,542 |
| Issues totales | 127 |
| - Críticos | 12 |
| - Mayores | 45 |
| - Menores | 70 |

Calificación: C (🔴)
```

### 2. Issues por Categoría
```markdown
## 🔒 Seguridad

### SEC-001: Credenciales hardcodeadas
**Ubicación:** `app/Config/Database.php:25`
**Problema:** `password = "mi_password_123"`
**Solución:** Usar variables de entorno
```

### 3. Issues por Lenguaje
```markdown
## PHP

| Issue | Cantidad |
|-------|----------|
| Seguridad | 8 |
| Bugs | 25 |
| Code Smells | 40 |

## JavaScript

| Issue | Cantidad |
|-------|----------|
| Seguridad | 4 |
| Bugs | 20 |
| Code Smells | 30 |
```

### 4. Plan de Acción
```markdown
## Plan de Acción

### Prioridad 1: Críticos (Esta semana)
- [ ] SEC-001 en app/Config/Database.php:25
- [ ] SEC-002 en app/Controllers/Auth.php:45

### Prioridad 2: Mayores (Próxima semana)
- [ ] BUG-001 en app/Models/User.php:78

### Prioridad 3: Menores (Este mes)
- [ ] SMELL-001 en app/Controllers/Admin.php
```

---

## 🎯 Interpretación de Resultados

### Calificaciones:

| Calificación | Issues Críticos | Issues Mayores | Estado |
|--------------|----------------|----------------|--------|
| **A** (🟢) | 0-2 | 0-10 | ✅ Excelente |
| **B** (🟡) | 3-5 | 11-30 | ⚠️ Bueno |
| **C** (🔴) | 6-10 | 31-50 | 🚨 Regular |
| **D** (🔴) | 11-20 | 51-100 | 🚨 Malo |
| **F** (🔴) | 20+ | 100+ | 🚨 Crítico |

---

## 📊 Métricas Adicionales

### Distribución por Lenguaje:
```
PHP:      6,230 líneas (73%)
JavaScript: 1,542 líneas (18%)
CSS:        770 líneas (9%)
```

### Archivos Más Grandes:
```
1. Admin.php           - 1,245 líneas 🔴
2. UserController.php  - 892 líneas  🔴
3. Database.php        - 654 líneas  🟡
4. app.js              - 542 líneas  🟡
5. Helper.php          - 423 líneas  🟢
```

### Complejidad Promedio:
```
Complejidad Ciclomática: 4.2 (🟢 Bueno)
Mantenibilidad: 75/100 (🟡 Aceptable)
```

---

## 🔧 Comandos Disponibles

### Auditoría Básica:
```bash
# Proyecto completo
node skills/auditoria-universal/audit-script.js

# Carpeta específica
node skills/auditoria-universal/audit-script.js ./src
```

### Auditoría por Lenguaje:
```bash
# Solo PHP
node skills/auditoria-universal/audit-script.js --lang=php ./app

# Solo JavaScript
node skills/auditoria-universal/audit-script.js --lang=js ./public

# Solo Python
node skills/auditoria-universal/audit-script.js --lang=py ./scripts
```

### Auditoría Específica:
```bash
# Solo seguridad
node skills/auditoria-universal/audit-script.js --category=security

# Solo bugs
node skills/auditoria-universal/audit-script.js --category=bugs

# Solo code smells
node skills/auditoria-universal/audit-script.js --category=smells
```

### Output Personalizado:
```bash
# Guardar en archivo específico
node skills/auditoria-universal/audit-script.js --output=mi-reporte.md

# Formato JSON
node skills/auditoria-universal/audit-script.js --format=json

# Solo mostrar críticos
node skills/auditoria-universal/audit-script.js --severity=critical
```

---

## 📁 Archivos Incluidos

```
skills/auditoria-universal/
├── SKILL.md                  ← Esta documentación
├── README.md                 ← Guía rápida
├── audit-script.js           ← Script principal
├── config/
│   ├── default.json          ← Configuración por defecto
│   └── languages.json        ← Configuración por lenguaje
├── rules/
│   ├── security.json         ← Reglas de seguridad
│   ├── bugs.json             ← Reglas de bugs
│   └── smells.json           ← Reglas de code smells
├── templates/
│   ├── report.md             ← Plantilla de reporte
│   └── checklist.md          ← Checklist
└── examples/
    └── AUDIT_REPORT.md       ← Ejemplo de reporte
```

---

## 🆘 Solución de Problemas

### Error: "Cannot find module"
```bash
# Verifica que Node.js está instalado
node --version  # Debe ser v18+

# Verifica la ruta del script
ls skills/auditoria-universal/audit-script.js
```

### Error: "Permission denied"
```bash
# Da permisos de ejecución
chmod +x skills/auditoria-universal/audit-script.js
```

### Error: "No files found"
```bash
# Verifica que estás en la carpeta correcta
pwd

# Verifica que hay archivos del lenguaje
find . -name "*.php"  # Para PHP
find . -name "*.js"   # Para JavaScript
```

### Reporte vacío
```bash
# Ejecuta con verbose para debug
node skills/auditoria-universal/audit-script.js --verbose

# Verifica la configuración
cat .auditrc.json
```

---

## 📈 Integración con CI/CD

### GitHub Actions:

```yaml
# .github/workflows/audit.yml
name: Code Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Run Code Audit
        run: node skills/auditoria-universal/audit-script.js
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: audit-report
          path: AUDIT_REPORT_UNIVERSAL.md
      
      - name: Check Critical Issues
        run: |
          if grep -q "CRITICAL" AUDIT_REPORT_UNIVERSAL.md; then
            echo "❌ Critical issues found!"
            exit 1
          fi
```

### GitLab CI:

```yaml
# .gitlab-ci.yml
code-audit:
  stage: test
  script:
    - node skills/auditoria-universal/audit-script.js
  artifacts:
    reports:
      code_quality: AUDIT_REPORT_UNIVERSAL.md
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## 🎯 Mejores Prácticas

### 1. Ejecuta Frecuentemente
```bash
# Antes de cada commit
node skills/auditoria-universal/audit-script.js

# O integra en pre-commit hook
git config core.hooksPath .githooks
```

### 2. Guarda el Historial
```bash
# Crea carpeta de reportes
mkdir -p reports/audit

# Guarda con fecha
cp AUDIT_REPORT_UNIVERSAL.md reports/audit/$(date +%Y-%m-%d).md
```

### 3. Compara Evolución
```bash
# Compara con reporte anterior
diff reports/audit/2026-03-01.md reports/audit/2026-03-12.md
```

### 4. Establece Metas
```markdown
## Metas de Calidad

### Mes 1:
- Reducir críticos de 12 a 5
- Reducir mayores de 45 a 30

### Mes 2:
- 0 críticos
- Reducir mayores a 15
- Calificación B (🟡)

### Mes 3:
- 0 críticos
- 0 mayores
- Calificación A (🟢)
```

---

## 📚 Recursos Adicionales

### Documentación:
- `SKILL.md` - Guía completa
- `README.md` - Inicio rápido
- `config/` - Configuración detallada
- `rules/` - Reglas detalladas

### Herramientas Complementarias:
- **PHP:** PHPStan, Psalm, PHPCS
- **JavaScript:** ESLint, Prettier
- **Python:** pylint, black, flake8
- **General:** SonarQube, CodeClimate

---

**Creado:** Marzo 2026  
**Versión:** 1.0.0  
**Multi-lenguaje:** PHP, JS, TS, Python, Java, C#, Ruby, Go  
**Cobertura:** 80% de problemas comunes
