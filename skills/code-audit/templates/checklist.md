# ✅ Checklist de Pre-Producción

## Proyecto: _______________________________
## Fecha: _______________________________
## Responsable: _______________________________

---

## 🔒 Seguridad

- [ ] No hay emails hardcodeados en el código
- [ ] No hay API keys expuestas en el frontend
- [ ] No hay contraseñas en el código
- [ ] Variables sensibles en archivo `.env`
- [ ] Archivo `.env` está en `.gitignore`
- [ ] Reglas de Firestore endurecidas
- [ ] Reglas de Storage configuradas
- [ ] Autenticación implementada correctamente
- [ ] localStorage encriptado para datos sensibles

---

## 🐛 Bugs

- [ ] Cero uso de `any` en TypeScript (o justificado con comentario)
- [ ] Console.log removidos en producción
- [ ] Errores validados en catch (usar `unknown`)
- [ ] useEffect con dependencias correctas
- [ ] No hay memory leaks (cleanup en useEffect)
- [ ] No hay estados no inicializados
- [ ] No hay promesas sin manejar

---

## 👃 Calidad de Código

- [ ] Ningún archivo > 500 líneas
- [ ] Componentes < 300 líneas
- [ ] Funciones < 50 líneas
- [ ] No hay código duplicado significativo
- [ ] Nombres de variables descriptivos
- [ ] No hay magic numbers (usar constantes)
- [ ] Comentarios solo donde es necesario

---

## 🎨 Rendimiento

- [ ] Lazy loading en imágenes
- [ ] Code splitting implementado
- [ ] Assets optimizados (imágenes comprimidas)
- [ ] Bundle < 500KB
- [ ] Lighthouse score > 90
- [ ] No hay renders innecesarios
- [ ] useMemo/useCallback donde sea necesario

---

## ♿ Accesibilidad

- [ ] Todas las imágenes tienen `alt`
- [ ] Contraste de colores verificado (WCAG AA)
- [ ] Navegación por teclado funciona
- [ ] ARIA labels donde sea necesario
- [ ] Focus visible en todos los elementos interactivos
- [ ] Formularios con labels asociados

---

## 📱 Responsive

- [ ] Funciona en móvil (< 640px)
- [ ] Funciona en tablet (640px - 1024px)
- [ ] Funciona en desktop (> 1024px)
- [ ] Menú móvil funciona correctamente
- [ ] Imágenes responsive (srcset si es necesario)
- [ ] Touch targets > 44px

---

## 🧪 Tests

- [ ] Tests de componentes críticos
- [ ] Tests de funciones de utilidad
- [ ] Tests de integración Firebase
- [ ] E2E test del flujo principal
- [ ] Cobertura de código > 70%
- [ ] Tests pasan en CI/CD

---

## 📚 Documentación

- [ ] README actualizado
- [ ] Componentes documentados con JSDoc
- [ ] Funciones complejas comentadas
- [ ] CHANGELOG actualizado
- [ ] Instrucciones de instalación claras
- [ ] Variables de entorno documentadas

---

## 🚀 Deploy

- [ ] Build funciona sin errores (`npm run build`)
- [ ] Variables de entorno configuradas en producción
- [ ] Dominio configurado (si aplica)
- [ ] HTTPS habilitado
- [ ] Redirects configurados
- [ ] 404 page personalizada
- [ ] Sitemap generado
- [ ] Robots.txt configurado

---

## 📊 Analytics y Monitoreo

- [ ] Google Analytics instalado (si aplica)
- [ ] Error tracking configurado (Sentry, etc.)
- [ ] Performance monitoring habilitado
- [ ] Uptime monitoring configurado

---

## 🔄 Backup y Recovery

- [ ] Backup de base de datos configurado
- [ ] Plan de rollback definido
- [ ] Procedimiento de recovery documentado
- [ ] Backups probados y funcionando

---

## ✅ Aprobación Final

### Desarrollador
- [ ] Todo el código fue revisado
- [ ] Tests pasan correctamente
- [ ] Documentación completa

**Firma:** _______________________________  
**Fecha:** _______________________________

### QA / Tester
- [ ] Tests manuales completados
- [ ] Bugs críticos resueltos
- [ ] UX/UI aprobado

**Firma:** _______________________________  
**Fecha:** _______________________________

### Project Manager / Cliente
- [ ] Requisitos cumplidos
- [ ] Diseño aprobado
- [ ] Funcionalidad aprobada

**Firma:** _______________________________  
**Fecha:** _______________________________

---

## 📝 Notas Adicionales

_______________________________________________

_______________________________________________

_______________________________________________

---

*Última actualización: Marzo 2026*
