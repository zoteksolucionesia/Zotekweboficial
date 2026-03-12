# 🔍 Reporte de Auditoría de Código

## Proyecto: [NOMBRE_DEL_PROYECTO]
**Fecha:** [FECHA]  
**Auditor:** [NOMBRE]  
**Versión del código:** [VERSIÓN]  
**Herramienta:** Code Audit Skill v1.0.0

---

## 📊 Resumen Ejecutivo

| Métrica | Valor | Calificación |
|---------|-------|--------------|
| Archivos analizados | [X] | - |
| Líneas de código | [X] | - |
| Promedio líneas/archivo | [X] | - |
| Archivo más grande | [nombre] ([X] líneas) | - |
| Cobertura de tipos | [X]% | [🟢/🟡/🔴] |

### Issues Encontrados

| Severidad | Cantidad | Trend |
|-----------|----------|-------|
| 🔴 Crítico | [X] | ⬆️/⬇️/➡️ |
| 🟡 Mayor | [X] | ⬆️/⬇️/➡️ |
| 🟢 Menor | [X] | ⬆️/⬇️/➡️ |
| **Total** | **[X]** | - |

### Por Categoría

| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| 🔒 Seguridad | [X] | [X]% |
| 🐛 Bugs | [X] | [X]% |
| 👃 Code Smells | [X] | [X]% |

**Calificación:** [🟢/🟡/🔴] **[A/B/C/D/F]**

---

## 🎯 Evaluación General

### ✅ Lo que está bien

- [Lista de aspectos positivos encontrados]

### ⚠️ Áreas de mejora

- [Lista de áreas que necesitan atención]

### 🚨 Issues críticos

- [Lista de issues que deben atenderse inmediatamente]

---

## 🚨 Issues Críticos (Detalle)

### [BUG-XXX]: [Nombre del issue]

**Severidad:** CRÍTICO  
**Categoría:** [security/bugs/code-smells]  
**Ubicación:** `archivo.tsx:línea`  
**Estado:** 🔴 Abierto | 🟡 En progreso | 🟢 Cerrado

**Problema:**
[Descripción clara del problema encontrado]

**Código problemático:**
```typescript
// Código actual
const x: any = valor;
```

**Solución recomendada:**
```typescript
// Código corregido
interface MiTipo {
  propiedad: string;
}
const x: MiTipo = valor;
```

**Impacto:**
[Qué pasa si no se corrige]

**Prioridad:** ALTA  
**Tiempo estimado:** [X] horas  
**Asignado a:** [Nombre]

---

## ⚠️ Issues Mayores (Detalle)

### [BUG-XXX]: [Nombre del issue]

**Severidad:** MAYOR  
**Ubicación:** `archivo.tsx:línea`

**Problema:**
[Descripción]

**Solución:**
[Código de ejemplo]

**Prioridad:** MEDIA  
**Tiempo estimado:** [X] horas

---

## ℹ️ Issues Menores (Detalle)

### [SMELL-XXX]: [Nombre del issue]

**Severidad:** MENOR  
**Ubicación:** `archivo.tsx:línea`

**Problema:**
[Descripción]

**Solución:**
[Recomendación]

**Prioridad:** BAJA  
**Tiempo estimado:** [X] minutos

---

## 📈 Métricas de Calidad

### Distribución de Líneas por Archivo

| Archivo | Líneas | Calificación |
|---------|--------|--------------|
| archivo1.tsx | 150 | 🟢 Bueno |
| archivo2.tsx | 450 | 🟡 Aceptable |
| archivo3.tsx | 890 | 🔴 Muy grande |

---

### Complejidad de Funciones

| Función | Archivo | Líneas | Complejidad |
|---------|---------|-------|-------------|
| refreshData() | Admin.tsx | 85 | 🔴 Alta |
| fetchData() | App.tsx | 45 | 🟡 Media |
| handleSubmit() | Form.tsx | 25 | 🟢 Baja |

---

### Evolución de la Deuda Técnica

| Auditoría | Fecha | Issues | Deuda (hrs) | Calificación |
|-----------|-------|--------|-------------|--------------|
| 1ra | Ene 2026 | 120 | 60 | D |
| 2da | Feb 2026 | 85 | 42 | C |
| 3ra | Mar 2026 | 68 | 34 | C |

---

## ✅ Plan de Acción

### Prioridad 1: Seguridad (Esta semana)

| Issue | Archivo | Línea | Responsable | Deadline |
|-------|---------|-------|-------------|----------|
| SEC-001 | config.ts | 15 | [Nombre] | [Fecha] |
| SEC-002 | firebase.ts | 8 | [Nombre] | [Fecha] |

**Estado:** ⬜ Pendiente | 🟡 En progreso | ✅ Completado

---

### Prioridad 2: Bugs Críticos (Esta semana)

| Issue | Archivo | Línea | Responsable | Deadline |
|-------|---------|-------|-------------|----------|
| BUG-001 | App.tsx | 23 | [Nombre] | [Fecha] |
| BUG-001 | Admin.tsx | 9 | [Nombre] | [Fecha] |

**Estado:** ⬜ Pendiente | 🟡 En progreso | ✅ Completado

---

### Prioridad 3: Bugs Mayores (Próxima semana)

| Issue | Archivo | Línea | Responsable | Deadline |
|-------|---------|-------|-------------|----------|
| BUG-002 | utils.ts | 45 | [Nombre] | [Fecha] |

**Estado:** ⬜ Pendiente | 🟡 En progreso | ✅ Completado

---

### Prioridad 4: Code Smells (Este mes)

| Issue | Archivo | Línea | Responsable | Deadline |
|-------|---------|-------|-------------|----------|
| SMELL-001 | Admin.tsx | 1 | [Nombre] | [Fecha] |

**Estado:** ⬜ Pendiente | 🟡 En progreso | ✅ Completado

---

## 📋 Seguimiento

### Revisión 1 - [Fecha]

**Asistentes:** [Nombres]

**Acuerdos:**
1. [Acuerdo 1]
2. [Acuerdo 2]

**Próxima revisión:** [Fecha]

---

### Revisión 2 - [Fecha]

**Asistentes:** [Nombres]

**Acuerdos:**
1. [Acuerdo 1]
2. [Acuerdo 2]

**Próxima revisión:** [Fecha]

---

## 🎯 Criterios de Aceptación

Para cerrar esta auditoría, se debe cumplir:

- [ ] Cero issues críticos
- [ ] Issues menores a 10
- [ ] Cobertura de tipos > 80%
- [ ] Ningún archivo > 500 líneas
- [ ] Tests pasando correctamente
- [ ] Checklist de pre-producción completado

---

## 📝 Apéndices

### A. Herramientas Usadas

- Code Audit Skill v1.0.0
- ESLint v9.x
- TypeScript v5.x
- SonarLint (opcional)

### B. Referencias

- [Guía de estilo TypeScript](link)
- [Best practices React](link)
- [Firebase security rules](link)

### C. Glosario

| Término | Definición |
|---------|------------|
| Code smell | Indicador superficial de un problema más profundo |
| Deuda técnica | Costo de retrabajo causado por elegir solución fácil en lugar de correcta |
| Complexidad ciclomática | Medida de la complejidad de un programa |

---

## ✅ Aprobación

**Auditor:** _______________________________  
**Fecha:** _______________________________

**Líder de proyecto:** _______________________________  
**Fecha:** _______________________________

**Cliente (si aplica):** _______________________________  
**Fecha:** _______________________________

---

*Reporte generado por Code Audit Skill v1.0.0*  
*[Fecha de generación]*
