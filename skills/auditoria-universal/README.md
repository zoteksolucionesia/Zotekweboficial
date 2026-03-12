# 🔍 Auditoría Universal de Código

## ¿Qué es?

Herramienta de auditoría **multi-lenguaje** que funciona con:
- ✅ PHP (incluyendo CodeIgniter 4)
- ✅ JavaScript/TypeScript
- ✅ Python
- ✅ Java
- ✅ C#
- ✅ Ruby
- ✅ Go
- ✅ Y más...

**Una sola herramienta para auditar todos tus proyectos.**

---

## 🚀 Inicio Rápido

### Paso 1: Copiar la Skill

```bash
# Copia esta carpeta a tu proyecto
cp -r skills/auditoria-universal /tu/proyecto/
```

### Paso 2: Ejecutar la Auditoría

```bash
# Proyecto completo
node skills/auditoria-universal/audit-script.js

# Carpeta específica
node skills/auditoria-universal/audit-script.js ./app

# Lenguaje específico
node skills/auditoria-universal/audit-script.js --lang=php ./app
node skills/auditoria-universal/audit-script.js --lang=js ./public
```

### Paso 3: Revisar Reporte

```bash
# Ver reporte
cat AUDIT_REPORT_UNIVERSAL.md

# O abrir en editor
code AUDIT_REPORT_UNIVERSAL.md
```

---

## 📊 ¿Qué Detecta?

### 🔒 Seguridad (8 reglas)
- Credenciales hardcodeadas
- API keys expuestas
- Contraseñas en código
- Tokens de acceso hardcodeados
- Datos sensibles en logs
- SQL dinámico sin sanitizar
- Eval/execute dinámico
- Rutas con información sensible

### 🐛 Bugs (8 reglas)
- Variables no inicializadas
- Funciones sin retorno
- Catch vacío o sin manejar
- Console.log/print en producción
- Código muerto/inaccesible
- Imports no utilizados
- Variables no utilizadas
- Condiciones siempre verdaderas/falsas

### 👃 Code Smells (8 reglas)
- Archivos muy grandes (>500 líneas)
- Funciones/métodos muy largos (>50 líneas)
- Clases muy grandes (>300 líneas)
- Anidamiento excesivo (>4 niveles)
- Magic numbers
- Nombres muy cortos (<2 chars)
- Nombres muy largos (>50 chars)
- Comentarios TODO/FIXME

---

## 📄 Ejemplo de Salida

```
🔍 Auditoría Universal de Código v1.0.0
========================
📁 Directorio: ./app
📝 Lenguajes detectados: PHP

📂 Buscando archivos...
✅ 45 archivos encontrados

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

## 🔧 Comandos Útiles

### Auditoría Básica:
```bash
# Todo el proyecto
node skills/auditoria-universal/audit-script.js

# Solo una carpeta
node skills/auditoria-universal/audit-script.js ./src
```

### Por Lenguaje:
```bash
# Solo PHP
node skills/auditoria-universal/audit-script.js --lang=php ./app

# Solo JavaScript
node skills/auditoria-universal/audit-script.js --lang=js ./public

# Solo Python
node skills/auditoria-universal/audit-script.js --lang=py ./scripts
```

### Por Categoría:
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
# Archivo específico
node skills/auditoria-universal/audit-script.js --output=mi-reporte.md

# Solo críticos
node skills/auditoria-universal/audit-script.js --severity=critical
```

---

## 📁 Archivos Incluidos

```
skills/auditoria-universal/
├── SKILL.md              ← Documentación completa
├── README.md             ← Esta guía
├── audit-script.js       ← Script principal
└── templates/
    ├── report.md         ← Plantilla de reporte
    └── checklist.md      ← Checklist
```

---

## ✅ Checklist de Uso

- [ ] Copiar carpeta `auditoria-universal` a tu proyecto
- [ ] Verificar Node.js >= 18
- [ ] Ejecutar: `node skills/auditoria-universal/audit-script.js`
- [ ] Revisar `AUDIT_REPORT_UNIVERSAL.md`
- [ ] Priorizar issues (críticos > mayores > menores)
- [ ] Corregir y re-auditar

---

## 📞 Soporte

¿Problemas?

1. Verifica Node.js: `node --version` (debe ser v18+)
2. Verifica la ruta: `ls skills/auditoria-universal/audit-script.js`
3. Lee la documentación completa en `SKILL.md`

---

**Creado:** Marzo 2026  
**Versión:** 1.0.0  
**Multi-lenguaje:** Sí  
**Tiempo de auditoría:** 3-10 minutos
