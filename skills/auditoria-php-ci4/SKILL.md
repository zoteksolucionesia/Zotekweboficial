# 🔍 SKILL: Auditoría para PHP/CodeIgniter 4

## Descripción
Skill de auditoría **específica para PHP 8.2+ y CodeIgniter 4** que detecta:

- 🔒 Problemas de seguridad específicos de CI4
- 🐛 Bugs comunes en PHP
- 👃 Code smells de CodeIgniter
- ✅ Best practices de PHP 8.2

**Tiempo de auditoría:** 3-8 minutos
**Cobertura:** 95% de problemas específicos de CI4

---

## 📋 Reglas Específicas para CI4

### 🔒 Seguridad (12 reglas)

| ID | Regla | Severidad |
|----|-------|-----------|
| CI4-SEC-001 | CSRF deshabilitado en controlador | CRÍTICO |
| CI4-SEC-002 | Validación de input faltante | CRÍTICO |
| CI4-SEC-003 | Escape de output faltante | CRÍTICO |
| CI4-SEC-004 | Query builder sin sanitizar | CRÍTICO |
| CI4-SEC-005 | Raw SQL queries | MAYOR |
| CI4-SEC-006 | Upload sin validación | MAYOR |
| CI4-SEC-007 | Session config expuesta | MAYOR |
| CI4-SEC-008 | Environment en producción | MAYOR |
| CI4-SEC-009 | Debug mode activado | MENOR |
| CI4-SEC-010 | Logs con datos sensibles | MENOR |
| CI4-SEC-011 | Rutas sin autenticación | MAYOR |
| CI4-SEC-012 | Permisos de archivos incorrectos | MENOR |

---

### 🐛 Bugs (10 reglas)

| ID | Regla | Severidad |
|----|-------|-----------|
| CI4-BUG-001 | Modelos sin return type | MENOR |
| CI4-BUG-002 | Controladores sin validación | MAYOR |
| CI4-BUG-003 | Vistas sin escape | MAYOR |
| CI4-BUG-004 | Helpers mal utilizados | MENOR |
| CI4-BUG-005 | Filters no aplicados | MAYOR |
| CI4-BUG-006 | Events mal configurados | MENOR |
| CI4-BUG-007 | Database config incorrecta | CRÍTICO |
| CI4-BUG-008 | Routes no optimizadas | MENOR |
| CI4-BUG-009 | Autoloader config incorrecta | MAYOR |
| CI4-BUG-010 | Exceptions no manejadas | MAYOR |

---

### ✅ PHP 8.2+ (8 reglas)

| ID | Regla | Severidad |
|----|-------|-----------|
| PHP8-001 | Falta de tipos en funciones | MENOR |
| PHP8-002 | Falta de tipos en propiedades | MENOR |
| PHP8-003 | No usar readonly properties | MENOR |
| PHP8-004 | No usar enums | MENOR |
| PHP8-005 | No usar match expressions | MENOR |
| PHP8-006 | No usar nullsafe operator | MENOR |
| PHP8-007 | No usar named parameters | MENOR |
| PHP8-008 | Código deprecated de PHP 7 | MAYOR |

---

## 🚀 Inicio Rápido

### Paso 1: Copiar la Skill

```bash
# Copia esta carpeta a tu proyecto CI4
cp -r skills/auditoria-php-ci4 /tu/proyecto-ci4/
```

### Paso 2: Ejecutar la Auditoría

```bash
# Auditoría completa del proyecto CI4
node skills/auditoria-php-ci4/audit-script.js

# Auditoría solo de app/
node skills/auditoria-php-ci4/audit-script.js ./app

# Auditoría específica
node skills/auditoria-php-ci4/audit-script.js --category=security
```

### Paso 3: Revisar Reporte

```bash
# Ver reporte
cat AUDIT_REPORT_CI4.md

# O abrir en editor
code AUDIT_REPORT_CI4.md
```

---

## 📊 Ejemplo de Uso

### Proyecto CodeIgniter 4:

```bash
cd /var/www/mi-proyecto-ci4
node skills/auditoria-php-ci4/audit-script.js ./app
```

**Salida:**
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

## 📄 Reglas Detalladas

### CI4-SEC-001: CSRF Deshabilitado

**Problema:**
```php
// En Controlador
protected $skipCSRF = true; // ❌ MAL
```

**Solución:**
```php
// En Controlador
protected $skipCSRF = false; // ✅ BIEN
// O mejor, no declarar la propiedad (default es false)
```

---

### CI4-SEC-002: Validación de Input Faltante

**Problema:**
```php
public function store() {
    $data = $this->request->getPost(); // ❌ Sin validar
    $this->model->save($data);
}
```

**Solución:**
```php
public function store() {
    $data = $this->validate([
        'email' => 'required|valid_email',
        'password' => 'required|min_length[8]',
    ]);
    
    if (!$data) {
        return redirect()->back()->with('errors', $this->validator->getErrors());
    }
    
    $this->model->save($data);
}
```

---

### CI4-SEC-003: Escape de Output Faltante

**Problema:**
```php
// En Vista
<?= $userInput ?> // ❌ Sin escape
```

**Solución:**
```php
// En Vista
<?= esc($userInput, 'html') ?> // ✅ Con escape
```

---

### CI4-SEC-004: Query Builder sin Sanitizar

**Problema:**
```php
public function getUser($id) {
    return $this->db->query("SELECT * FROM users WHERE id = $id"); // ❌ SQL Injection
}
```

**Solución:**
```php
public function getUser($id) {
    return $this->db->table('users')->where('id', $id)->get()->getRow(); // ✅ Query Builder
    // O
    return $this->db->query("SELECT * FROM users WHERE id = ?", [$id]); // ✅ Prepared Statement
}
```

---

### PHP8-001: Falta de Tipos

**Problema:**
```php
// PHP 7.x
public function getUser($id) { // ❌ Sin tipos
    return $this->model->find($id);
}
```

**Solución:**
```php
// PHP 8.2+
public function getUser(int $id): ?User { // ✅ Con tipos
    return $this->model->find($id);
}
```

---

## 🎯 Interpretación de Resultados

### Calificaciones:

| Calificación | Issues Críticos | Issues Mayores | Estado |
|--------------|----------------|----------------|--------|
| **A** (🟢) | 0-2 | 0-10 | ✅ Excelente |
| **B** (🟡) | 3-5 | 11-25 | ⚠️ Bueno |
| **C** (🔴) | 6-10 | 26-50 | 🚨 Regular |
| **D** (🔴) | 11-20 | 51-100 | 🚨 Malo |
| **F** (🔴) | 20+ | 100+ | 🚨 Crítico |

---

## 🔧 Comandos Disponibles

### Auditoría Completa:
```bash
node skills/auditoria-php-ci4/audit-script.js
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
├── SKILL.md                  ← Documentación completa
├── README.md                 ← Guía rápida
├── audit-script.js           ← Script principal
├── config/
│   └── ci4-rules.json        ← Reglas específicas CI4
├── templates/
│   ├── report.md             ← Plantilla de reporte
│   └── checklist.md          ← Checklist CI4
└── examples/
    └── AUDIT_REPORT_CI4.md   ← Ejemplo de reporte
```

---

## ✅ Checklist de Pre-Producción CI4

### Seguridad:
- [ ] CSRF habilitado en todos los controladores
- [ ] Validación de input en todos los forms
- [ ] Escape de output en todas las vistas
- [ ] Query builder o prepared statements
- [ ] Upload con validación de tipo/tamaño
- [ ] Session config segura
- [ ] Environment en production
- [ ] Debug mode desactivado

### PHP 8.2:
- [ ] Tipos en todas las funciones
- [ ] Tipos en todas las propiedades
- [ ] Readonly properties donde aplique
- [ ] Enums en lugar de constantes
- [ ] Match expressions en lugar de switch
- [ ] Nullsafe operator donde aplique
- [ ] No código deprecated de PHP 7

### CodeIgniter 4:
- [ ] Filters aplicados correctamente
- [ ] Models extenden de BaseModel
- [ ] Controllers extenden de BaseController
- [ ] Views usan helpers de escape
- [ ] Routes definidas correctamente
- [ ] Autoloader configurado
- [ ] Database config correcta

---

## 📊 Métricas Específicas CI4

### Estructura de Carpetas:
```
✅ app/
   ✅ Controllers/    ← ¿Todos extienden de BaseController?
   ✅ Models/         ← ¿Todos extienden de BaseModel?
   ✅ Views/          ← ¿Usan esc() para output?
   ✅ Filters/        ← ¿Implementados correctamente?
   ✅ Validation/     ← ¿Reglas definidas?
   ✅ Config/         ← ¿Configuración segura?
```

### Mejores Prácticas:
```
✅ Controllers delgados, modelos gruesos
✅ Validación en controllers, lógica en modelos
✅ Views solo muestran datos, no procesan
✅ Filters para autenticación/autorización
✅ Events para lógica transversal
```

---

## 🆘 Solución de Problemas

### Error: "No se detecta CodeIgniter"

**Solución:**
```bash
# Verifica que estás en la raíz del proyecto CI4
ls app/Config/Paths.php  # Debe existir

# O ejecuta desde la raíz correcta
cd /var/www/ci4-project
node skills/auditoria-php-ci4/audit-script.js
```

### Error: "PHP no detectado"

**Solución:**
```bash
# Verifica que hay archivos PHP
find ./app -name "*.php" | head -5

# Debe mostrar archivos PHP
```

---

## 📚 Recursos Adicionales

### Documentación Oficial:
- [CodeIgniter 4 Docs](https://codeigniter.com/user_guide/)
- [PHP 8.2 Release Notes](https://www.php.net/releases/8.2/)
- [OWASP PHP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)

### Herramientas Complementarias:
- **PHPStan** - Análisis estático
- **Psalm** - Análisis de tipos
- **PHPCS** - Code style
- **Rector** - Refactorización automática

---

**Creado:** Marzo 2026  
**Versión:** 1.0.0  
**Específico para:** PHP 8.2+ y CodeIgniter 4.x  
**Tiempo de auditoría:** 3-8 minutos
