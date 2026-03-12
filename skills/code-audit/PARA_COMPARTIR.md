# 🔍 Skill de Auditoría de Código (Code Audit)

## ¿Qué es esto?

Una herramienta que **audita automáticamente** tu código React/TypeScript en busca de:
- 🐛 Bugs críticos
- 🔒 Problemas de seguridad
- 👃 Code smells (malas prácticas)
- 📊 Métricas de calidad

**Tiempo de auditoría:** 2-5 minutos
**Resultado:** Reporte detallado en `AUDIT_REPORT.md`

---

## 📦 ¿Qué Necesitas?

### Requisitos:
- ✅ Node.js versión 18 o superior
- ✅ Un proyecto React/TypeScript
- ✅ 5 minutos de tiempo

### No necesitas:
- ❌ Instalar dependencias adicionales
- ❌ Configurar nada complejo
- ❌ Conocimientos avanzados

---

## 🚀 Instalación (2 opciones)

### Opción 1: Copiar la Carpeta (Recomendada)

```bash
# 1. Copia la carpeta code-audit a tu proyecto
cp -r /ruta/original/skills/code-audit /tu/proyecto/skills/

# 2. Ve a la raíz de tu proyecto
cd /tu/proyecto/

# 3. Ejecuta la auditoría
node skills/code-audit/audit-script.js ./src
```

---

### Opción 2: Descargar desde GitHub

```bash
# 1. Crea la carpeta
mkdir -p skills/code-audit

# 2. Descarga los archivos
# (Tu compañero te debe pasar los archivos o el repo)

# 3. Ejecuta la auditoría
node skills/code-audit/audit-script.js ./src
```

---

## 📊 Ejecución

### Comando Básico:

```bash
node skills/code-audit/audit-script.js ./src
```

### Salida que verás:

```
🔍 Code Audit Skill v1.0.0
========================
📁 Directorio: ./src

📂 Buscando archivos TypeScript/JavaScript...
✅ 10 archivos encontrados

🔬 Analizando archivos...
   Progreso: 10/10 archivos

📊 Calculando métricas...
📝 Generando reporte...

✅ ¡Auditoría completada!
========================
📄 Reporte guardado en: AUDIT_REPORT.md

📊 Resumen:
   Archivos: 10
   Líneas: 2907
   Issues: 68
   - Críticos: 37
   - Mayores: 29
   - Menores: 2

🚨 ATENCIÓN: Hay issues críticos que deben atenderse de inmediato
```

---

## 📋 ¿Qué Hace el Script?

### Busca Estos Problemas:

#### 🔒 Seguridad (4 reglas):
- Emails hardcodeados en el código
- API keys expuestas
- Contraseñas en el código
- localStorage sin encriptar

#### 🐛 Bugs (4 reglas):
- Uso excesivo de `any` en TypeScript
- Console.log en producción
- Catch blocks sin validación de error
- useEffect sin dependencias claras

#### 👃 Code Smells (2 reglas):
- Archivos muy grandes (> 500 líneas)
- Magic numbers (números sin contexto)

---

## 📄 Resultado: AUDIT_REPORT.md

El reporte incluye:

### 1. Resumen Ejecutivo
```markdown
| Métrica | Valor |
|---------|-------|
| Archivos analizados | 10 |
| Líneas de código | 2907 |
| Issues totales | 68 |
| - Críticos | 37 |
| - Mayores | 29 |
| - Menores | 2 |

Calificación: C (🔴)
```

### 2. Issues por Categoría
```markdown
### 🔒 Seguridad
- SEC-001: Emails hardcodeados en App.tsx:23

### 🐛 Bugs
- BUG-001: Uso de any en Admin.tsx:9

### 👃 Code Smells
- SMELL-001: Archivo muy grande (Admin.tsx: 1261 líneas)
```

### 3. Plan de Acción
```markdown
### Prioridad 1: Seguridad (Esta semana)
- [ ] SEC-001 en src/App.tsx:23 - Emails hardcodeados

### Prioridad 2: Bugs Críticos (Esta semana)
- [ ] BUG-001 en src/Admin.tsx:9 - Uso de any
```

---

## 🎯 Interpretación de Resultados

### Calificaciones:

| Calificación | Issues Críticos | Issues Mayores | Acción |
|--------------|----------------|----------------|--------|
| **A** (🟢) | 0-2 | 0-5 | ✅ Listo para producción |
| **B** (🟡) | 3-5 | 6-15 | ⚠️ Mejoras menores necesarias |
| **C** (🔴) | 5+ | 15+ | 🚨 Mejoras mayores necesarias |
| **D** (🔴) | 10+ | 25+ | 🚨 Refactorización necesaria |
| **F** (🔴) | 20+ | 50+ | 🚨 No usar en producción |

---

## ✅ Flujo de Trabajo Recomendado

### Paso 1: Ejecutar Auditoría

```bash
node skills/code-audit/audit-script.js ./src
```

### Paso 2: Revisar Reporte

```bash
# Abre el reporte
code AUDIT_REPORT.md
# O
notepad AUDIT_REPORT.md
```

### Paso 3: Priorizar Issues

**Críticos (arreglar YA):**
- Emails hardcodeados
- API keys expuestas
- Uso de `any` en tipos importantes

**Mayores (arreglar esta semana):**
- Console.log en producción
- Catch blocks sin validar

**Menores (arreglar cuando haya tiempo):**
- Magic numbers
- Archivos grandes

### Paso 4: Corregir y Re-auditar

```bash
# Después de corregir, ejecuta de nuevo
node skills/code-audit/audit-script.js ./src

# Compara con el reporte anterior
```

---

## 📊 Ejemplo Real

### Antes de Corregir:
```
Archivos: 10
Líneas: 2907
Issues: 68
- Críticos: 37
- Mayores: 29
Calificación: C (🔴)
```

### Después de Corregir:
```
Archivos: 12
Líneas: 3264
Issues: 50
- Críticos: 24
- Mayores: 24
Calificación: B (🟡)
```

**Mejora:** 26% menos issues, calificación subió de C a B

---

## 🛠️ Comandos Útiles

### Auditoría Completa:
```bash
node skills/code-audit/audit-script.js ./src
```

### Auditoría de una Carpeta Específica:
```bash
node skills/code-audit/audit-script.js ./src/components
```

### Auditoría de Todo el Proyecto:
```bash
node skills/code-audit/audit-script.js
```

---

## ❓ Preguntas Frecuentes

### ¿Necesito instalar algo?
**No.** Solo necesitas Node.js 18+. El script no tiene dependencias externas.

### ¿Funciona con JavaScript?
**Sí.** Soporta `.ts`, `.tsx`, `.js`, `.jsx`.

### ¿Puedo agregar reglas personalizadas?
**Sí.** Edita `skills/code-audit/audit-script.js` y agrega reglas en la sección `RULES`.

### ¿Cuánto tarda?
**2-5 minutos** para proyectos promedio (10-50 archivos).

### ¿El reporte se puede compartir?
**Sí.** El `AUDIT_REPORT.md` es un archivo Markdown que puedes enviar por email, subir a GitHub, etc.

### ¿Funciona en Windows/Mac/Linux?
**Sí.** Es compatible con todos los sistemas operativos.

---

## 🎯 Consejos

### Para Mejor Resultado:

1. **Ejecuta antes de cada commit:**
   ```bash
   node skills/code-audit/audit-script.js ./src
   ```

2. **Guarda los reportes:**
   ```bash
   cp AUDIT_REPORT.md reports/audit-$(date +%Y-%m-%d).md
   ```

3. **Compara evolución:**
   ```bash
   # Ejecuta semanalmente y compara
   diff reports/audit-week1.md reports/audit-week2.md
   ```

4. **Integra en CI/CD:**
   ```yaml
   # .github/workflows/audit.yml
   - name: Code Audit
     run: node skills/code-audit/audit-script.js ./src
   ```

---

## 📞 Soporte

### Si tienes problemas:

1. **Verifica Node.js:**
   ```bash
   node --version  # Debe ser v18+
   ```

2. **Verifica la ruta:**
   ```bash
   ls skills/code-audit/audit-script.js
   ```

3. **Revisa permisos:**
   ```bash
   chmod +x skills/code-audit/audit-script.js
   ```

4. **Revisa el error:**
   - La mayoría de errores son de ruta o versión de Node.js

---

## 📚 Archivos Incluidos

```
skills/code-audit/
├── SKILL.md              ← Documentación completa
├── README.md             ← Esta guía
├── audit-script.js       ← Script de auditoría
└── templates/
    ├── audit-report.md   ← Plantilla de reporte
    └── checklist.md      ← Checklist de pre-producción
```

---

## ✅ Checklist de Uso

- [ ] Copiar carpeta `code-audit` a tu proyecto
- [ ] Verificar Node.js >= 18
- [ ] Ejecutar: `node skills/code-audit/audit-script.js ./src`
- [ ] Revisar `AUDIT_REPORT.md`
- [ ] Priorizar issues (críticos > mayores > menores)
- [ ] Corregir issues críticos
- [ ] Re-ejecutar auditoría
- [ ] Compartir reporte con el equipo

---

**Creado:** Marzo 2026  
**Versión:** 1.0.0  
**Tiempo de uso:** 5 minutos  
**Dificultad:** Fácil

---

*¿Listo para auditar tu código? ¡Ejecuta el script ahora!*
