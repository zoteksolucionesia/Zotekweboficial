# 📧 Plantilla para Compartir la Skill

---

## Opción 1: Email Formal

**Asunto:** Herramienta de Auditoría de Código - Instrucciones de Uso

---

Hola [Nombre del compañero],

Te comparto una herramienta de **auditoría automática de código** que desarrollé. Analiza proyectos React/TypeScript en busca de bugs, problemas de seguridad y malas prácticas.

## ¿Qué hace?

- 🔍 Escanea tu código en 2-5 minutos
- 📊 Genera reporte detallado de issues
- 🚨 Identifica problemas críticos, mayores y menores
- ✅ Te da una calificación de calidad (A-F)

## ¿Cómo usarla?

### Paso 1: Copiar la carpeta

```bash
# Copia esta carpeta a tu proyecto
cp -r skills/code-audit /tu/proyecto/
```

### Paso 2: Ejecutar la auditoría

```bash
cd /tu/proyecto/
node skills/code-audit/audit-script.js ./src
```

### Paso 3: Revisar el reporte

Se generará un archivo `AUDIT_REPORT.md` con todos los issues encontrados.

## Requisitos

- Node.js versión 18 o superior
- Un proyecto React/TypeScript
- 5 minutos de tiempo

## Resultado Esperado

Verás algo como esto:

```
✅ ¡Auditoría completada!
📊 Resumen:
   Archivos: 10
   Líneas: 2907
   Issues: 68
   - Críticos: 37
   - Mayores: 29
   - Menores: 2

🚨 ATENCIÓN: Hay issues críticos que deben atenderse
```

## Documentación Completa

En la carpeta `skills/code-audit/` encontrarás:
- `PARA_COMPARTIR.md` - Guía rápida de uso
- `README.md` - Documentación completa
- `SKILL.md` - Detalles técnicos

## ¿Tienes dudas?

Avísame y te ayudo a configurarlo en tu proyecto.

Saludos,
[Tu Nombre]

---

## Opción 2: Mensaje Casual (WhatsApp/Slack)

---

Hey [Nombre]! 👋

Te paso una herramienta que hice para auditar código React/TypeScript automáticamente:

**Qué hace:**
- Escanea tu código en 5 min
- Te dice cuántos bugs y problemas de seguridad tienes
- Te da un reporte con todo detallado

**Cómo usarla:**
```bash
# Copia la carpeta code-audit a tu proyecto
node skills/code-audit/audit-script.js ./src
```

**Requisitos:**
- Node.js 18+
- Proyecto React/TypeScript

Te va a generar un `AUDIT_REPORT.md` con todos los issues.

La carpeta está aquí: `/ruta/a/skills/code-audit/`

Cualquier duda me avisas! 🚀

---

## Opción 3: Mensaje Técnico (GitHub Issues/PR)

---

## Code Audit Tool

### Overview
Automated code auditing tool for React/TypeScript projects.

### What it detects:
- 🔒 Security issues (hardcoded emails, exposed API keys)
- 🐛 Bugs (any usage, console.log, unhandled errors)
- 👃 Code smells (large files, magic numbers)

### Usage:
```bash
node skills/code-audit/audit-script.js ./src
```

### Output:
Generates `AUDIT_REPORT.md` with:
- Executive summary
- Issues by severity
- Action plan

### Requirements:
- Node.js >= 18
- TypeScript/React project

### Documentation:
See `skills/code-audit/PARA_COMPARTIR.md` for complete guide.

---

## Opción 4: Instrucciones para README del Proyecto

---

## 🔍 Code Audit Tool

This project includes an automated code audit tool.

### Run Audit:

```bash
node skills/code-audit/audit-script.js ./src
```

### View Report:

```bash
cat AUDIT_REPORT.md
```

### Fix Issues:

1. Review critical issues first
2. Fix major issues
3. Re-run audit to verify improvements

For complete instructions, see `skills/code-audit/PARA_COMPARTIR.md`

---

## 📋 Checklist para Compartir

### Antes de Enviar:

- [ ] Verifica que la carpeta `code-audit` existe completa
- [ ] Asegúrate de que `audit-script.js` es ejecutable
- [ ] Prueba el script en tu proyecto para confirmar que funciona
- [ ] Prepara la ruta completa para compartir

### Al Enviar:

- [ ] Copia la carpeta completa (no solo archivos sueltos)
- [ ] Incluye el mensaje/email con instrucciones
- [ ] Menciona los requisitos (Node.js 18+)
- [ ] Ofrece ayuda si tiene problemas

### Después de Enviar:

- [ ] Confirma que recibió los archivos
- [ ] Ofrece una llamada rápida para configurar
- [ ] Pide feedback después de que la use

---

## 🎯 Lo Más Importante

**Dile esto a tu compañero:**

> "Solo necesitas copiar la carpeta `code-audit` a tu proyecto y ejecutar un comando. El resto es automático."

**Comando mágico:**
```bash
node skills/code-audit/audit-script.js ./src
```

**Eso es todo.** El script hace todo el trabajo y te da un reporte listo para revisar.

---

*Elige la opción que mejor se adapte a tu estilo y envíasela!*
