# Skill: Calidad Empresarial para Zotek Soluciones IA

## Propósito
Garantizar que todo código producido cumpla con estándares empresariales de calidad, mantenibilidad y seguridad antes de ser considerado para producción.

## Principios Fundamentales

### 1. **Seguridad Primero**
- Nunca exponer credenciales, API keys, tokens o información sensible en el código
- Validar y sanitizar TODAS las entradas de usuario
- Implementar verificaciones de autenticación y autorización en cada endpoint
- Usar principios de mínimo privilegio

### 2. **Calidad de Código**
- Priorizar calidad sobre rapidez en todas las implementaciones
- Escribir código legible, auto-documentado y consistente
- Seguir convenciones de nomenclatura existentes en el proyecto
- Mantener funciones pequeñas con una sola responsabilidad
- Evitar código duplicado (principio DRY)

### 3. **Validaciones Exhaustivas**
- Validar tipos de datos en todos los parámetros de entrada
- Manejar casos borde y valores nulos/undefined
- Implementar try-catch en operaciones que pueden fallar (red, BD, APIs externas)
- Proporcionar mensajes de error claros y útiles

### 4. **Testing y Verificación**
- Incluir tests unitarios para funcionalidad crítica
- Verificar que los cambios no rompan funcionalidad existente
- Ejecutar linting y type-checking cuando esté disponible
- Validar manualmente flujos críticos antes de marcar como completado

### 5. **Documentación**
- Comentar el "por qué" del código, no el "qué"
- Documentar decisiones arquitectónicas importantes
- Mantener READMEs actualizados con instrucciones de instalación/ejecución
- Incluir JSDoc/docstrings en funciones públicas complejas

### 6. **Control de Cambios**
- Commits atómicos con mensajes descriptivos (convención: tipo: descripción)
- Nunca modificar producción sin autorización explícita
- Mantener separación clara entre desarrollo y producción
- Revertir cambios si introducen errores

### 7. **Manejo de Datos**
- Validar estructura de datos antes de procesar
- Sanitizar datos antes de guardar en BD o mostrar en UI
- Prevenir inyección SQL y XSS
- Implementar backups antes de migraciones de datos

## Checklist de Calidad (Obligatorio)

Antes de entregar cualquier cambio:

- [ ] El código compila/ejecuta sin errores
- [ ] No hay warnings nuevos introducidos
- [ ] Las validaciones de entrada están implementadas
- [ ] El manejo de errores es apropiado
- [ ] No hay información sensible expuesta
- [ ] El código sigue las convenciones del proyecto
- [ ] La funcionalidad fue verificada (manual o automáticamente)
- [ ] No se rompió funcionalidad existente
- [ ] Los cambios están en el entorno correcto (dev vs prod)

## Protocolo de Producción

**REGLA DE ORO**: NUNCA modificar archivos de producción sin autorización explícita.

1. Identificar si el archivo afecta producción directamente
2. Si es producción, confirmar con el usuario antes de modificar
3. Si el usuario autoriza, documentar el cambio en el commit
4. Proporcionar instrucciones claras de deploy si aplica

## Estructura del Proyecto Zotek

- `www/` → Archivos estáticos de producción (Firebase Hosting)
- `src/` → Backend Python de producción (FastAPI)
- `functions/` → Cloud Functions de Firebase (producción)
- `.qwen/` → Configuración del asistente (desarrollo)
- Archivos `.py` en raíz → Scripts de utilidad/mantenimiento

## Flujo de Trabajo Recomendado

1. Entender el requerimiento completamente
2. Identificar archivos afectados (¿dev o prod?)
3. Si es producción → pedir autorización
4. Implementar con principios de calidad
5. Verificar localmente si es posible
6. Documentar cambios y proporcionar instrucciones
7. Marcar tarea como completada solo después de verificar

---

**Versión**: 1.0  
**Última actualización**: 2026-03-13  
**Aplicado a**: Zotek Soluciones IA - Plataforma de Chatbots con IA
