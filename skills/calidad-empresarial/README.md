# 🏗️ Skill: Calidad Empresarial para Proyectos React/TypeScript

## ¿Qué es esta skill?

Una **metodología completa** para desarrollar proyectos React/TypeScript con **énfasis en calidad, seguridad y escalabilidad DESDE EL DÍA 1**.

---

## ⚖️ TRADE-OFF: Calidad vs Velocidad

| Enfoque | Velocidad | Calidad | Seguridad | Escalabilidad |
|---------|-----------|---------|-----------|---------------|
| **Tradicional (IA)** | ⚡ Rápido (2-3 días) | 70-80% | Media | Media |
| **Esta Skill** | 🐢 Lento (6-7 días) | 90-95% | Alta | Alta |

**¿Vale la pena?**
- ✅ **SÍ** si: Es un producto comercial, SaaS, o proyecto a largo plazo
- ❌ **NO** si: Es un prototipo desechable o MVP para validar idea

---

## 🚀 Inicio Rápido

### Paso 1: Copiar la Skill

```bash
# Copia esta carpeta a tu nuevo proyecto
cp -r skills/calidad-empresarial /tu/nuevo/proyecto/
```

### Paso 2: Ejecutar Inicialización

```bash
cd /tu/nuevo/proyecto/
node skills/calidad-empresarial/scripts/init.js
```

### Paso 3: Seguir la Guía

El script te guiará para:
1. Configurar TypeScript estricto
2. Crear estructura de carpetas
3. Definir tipos base
4. Configurar validación
5. Setup de tests

---

## 📋 Fases del Desarrollo

```
Día 1-2: Fundamentos (TypeScript + Estructura + Tipos)
Día 2-3: Seguridad (Validación + Logger)
Día 3-4: Servicios (API tipificada)
Día 4-5: Componentes (UI con tipos)
Día 5-6: Tests (Unitarios + Integración)
```

---

## 📁 Estructura del Proyecto

```
project/
├── src/
│   ├── types/           ← Tipos TypeScript (PRIMERO)
│   ├── utils/           ← Validación + Logger
│   ├── services/        ← Capa de datos
│   ├── components/      ← Componentes UI
│   └── App.tsx
├── tests/               ← Tests desde el inicio
├── .github/workflows/   ← CI/CD
└── docs/                ← Documentación
```

---

## ✅ Checklist de Calidad

### Antes de Cada Commit:
- [ ] TypeScript compila sin errores
- [ ] Tests pasan
- [ ] No hay `any` en el código nuevo
- [ ] No hay `console.log` (usar `logger`)
- [ ] Datos validados antes de usar

### Antes de Producción:
- [ ] Auditoría de seguridad pasa
- [ ] Cobertura de tests > 80%
- [ ] Lighthouse score > 90

---

## 📊 Métricas de Calidad

| Métrica | Objetivo | Mínimo |
|---------|----------|--------|
| Errores TypeScript | 0 | 0 |
| Uso de `any` | 0 | < 5 |
| Cobertura de tests | > 90% | > 80% |
| Lighthouse score | > 95 | > 90 |
| Issues de seguridad | 0 | 0 críticos |

---

## 🎯 ¿Cuándo Usar Esta Skill?

### ✅ Úsala cuando:
- Proyecto comercial o SaaS
- Producto a largo plazo
- Múltiples desarrolladores
- Requisitos de seguridad altos
- Plan de escalar

### ❌ No la uses cuando:
- Prototipo desechable
- MVP para validar idea (1-2 semanas)
- Presupuesto muy limitado
- Timeline muy corto (< 1 semana)

---

## 📚 Documentación Completa

Para la guía detallada, lee:
- **[SKILL.md](./SKILL.md)** - Documentación completa
- **[EJEMPLOS.md](./EJEMPLOS.md)** - Ejemplos de código
- **[CHECKLIST.md](./CHECKLIST.md)** - Checklist imprimible

---

## 💡 Consejos

1. **No saltes fases** - Cada fase construye sobre la anterior
2. **Tipos primero** - Define tipos antes de escribir lógica
3. **Valida todo** - Nunca confíes en datos externos
4. **Tests desde el inicio** - Es más fácil que agregar después
5. **Logger seguro** - Nunca loggees datos sensibles

---

## 🆘 Soporte

¿Problemas con la skill?

1. Revisa `SKILL.md` para detalles
2. Revisa `EJEMPLOS.md` para ejemplos
3. Revisa los tests de ejemplo

---

**Creado:** Marzo 2026  
**Versión:** 1.0.0  
**Filosofía:** Calidad sobre velocidad
