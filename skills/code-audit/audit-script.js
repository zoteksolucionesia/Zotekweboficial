#!/usr/bin/env node

/**
 * 🔍 Script de Auditoría de Código Tipo SonarQube
 * 
 * Analiza automáticamente un proyecto React/TypeScript en busca de:
 * - Bugs críticos
 * - Vulnerabilidades de seguridad
 * - Code smells
 * - Deuda técnica
 * 
 * Uso: node audit-script.js [directorio]
 * Ejemplo: node audit-script.js ./src
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ============================================
// CONFIGURACIÓN
// ============================================

const CONFIG = {
  // Límites recomendados
  MAX_FILE_LINES: 500,
  MAX_FUNCTION_LINES: 50,
  MAX_COMPONENT_LINES: 300,
  MAX_NESTING_LEVEL: 4,
  
  // Archivos a excluir
  EXCLUDE_DIRS: ['node_modules', 'dist', 'build', '.git', 'coverage'],
  EXCLUDE_FILES: ['*.test.ts', '*.test.tsx', '*.spec.ts', '*.spec.tsx'],
  
  // Patrones de búsqueda
  PATTERNS: {
    // Seguridad
    emails: /['"]\w+@\w+\.\w+['"]/g,
    apiKeys: /(apiKey|api_key|API_KEY|apikey)\s*[:=]\s*['"][^'"]+['"]/gi,
    passwords: /(password|passwd|pwd|contraseña)\s*[:=]\s*['"][^'"]+['"]/gi,
    localStorage: /localStorage\.(setItem|getItem)\([^)]+\)/g,
    
    // Bugs
    anyType: /(:\s*any|<any>|as any|any\s*[=:])/g,
    consoleLogs: /console\.(log|error|warn|info|debug)/g,
    catchAny: /catch\s*\(\s*(\w+)\s*:\s*any\s*\)/g,
    useEffectEmpty: /useEffect\s*\(\s*[^,]+,\s*\[\s*\]\s*\)/g,
    
    // Code smells
    magicNumbers: /\b[0-9]{2,}\b/g,
    longFunctions: /function\s+\w+\s*\([^)]*\)\s*\{[\s\S]{1000,}\}/g,
  },
  
  // Excepciones para magic numbers
  MAGIC_NUMBER_EXCLUDE: [
    /[0-9]+px/,
    /[0-9]+%/,
    /[0-9]+em/,
    /[0-9]+rem/,
    /[0-9]+vh/,
    /[0-9]+vw/,
    /v=\d+/, // YouTube IDs
    /id=\d+/,
    /size=\d+/,
  ],
};

// ============================================
// REGLAS DE AUDITORÍA
// ============================================

const RULES = {
  security: [
    {
      id: 'SEC-001',
      name: 'Emails hardcodeados',
      pattern: 'emails',
      severity: 'CRITICAL',
      description: 'Los emails no deben estar hardcodeados en el código',
      solution: 'Mover a variables de entorno o configuración',
    },
    {
      id: 'SEC-002',
      name: 'API keys expuestas',
      pattern: 'apiKeys',
      severity: 'CRITICAL',
      description: 'Las API keys no deben estar visibles en el código',
      solution: 'Usar variables de entorno con prefijo VITE_',
    },
    {
      id: 'SEC-003',
      name: 'Contraseñas hardcodeadas',
      pattern: 'passwords',
      severity: 'CRITICAL',
      description: 'Las contraseñas nunca deben estar en el código',
      solution: 'Usar autenticación segura y variables de entorno',
    },
    {
      id: 'SEC-004',
      name: 'localStorage sin encriptar',
      pattern: 'localStorage',
      severity: 'MINOR',
      description: 'localStorage guarda datos en texto claro',
      solution: 'Encriptar datos sensibles antes de guardar',
    },
  ],
  bugs: [
    {
      id: 'BUG-001',
      name: 'Uso de any en TypeScript',
      pattern: 'anyType',
      severity: 'CRITICAL',
      description: 'El tipo any elimina los beneficios de TypeScript',
      solution: 'Definir interfaces o tipos específicos',
    },
    {
      id: 'BUG-002',
      name: 'Console.log en producción',
      pattern: 'consoleLogs',
      severity: 'MAJOR',
      description: 'Los console.log deben removerse en producción',
      solution: 'Usar un logger condicional o remover',
    },
    {
      id: 'BUG-003',
      name: 'Catch sin validación de error',
      pattern: 'catchAny',
      severity: 'MAJOR',
      description: 'Los errores tipo any no son type-safe',
      solution: 'Usar "unknown" y validar el error',
    },
    {
      id: 'BUG-004',
      name: 'useEffect con dependencias vacías',
      pattern: 'useEffectEmpty',
      severity: 'MINOR',
      description: 'useEffect sin dependencias puede causar bugs',
      solution: 'Agregar dependencias explícitas o justificar []',
    },
  ],
};

// ============================================
// FUNCIONES DE ANÁLISIS
// ============================================

/**
 * Encuentra todos los archivos TypeScript/JavaScript en un directorio
 */
function findFiles(dir, extensions = ['.ts', '.tsx', '.js', '.jsx']) {
  let results = [];
  
  try {
    const items = fs.readdirSync(dir);
    
    items.forEach(item => {
      // Excluir directorios
      if (CONFIG.EXCLUDE_DIRS.includes(item)) return;
      
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        results = results.concat(findFiles(fullPath, extensions));
      } else if (extensions.some(ext => item.endsWith(ext))) {
        // Excluir archivos de test
        const isTestFile = CONFIG.EXCLUDE_FILES.some(pattern => {
          if (pattern.includes('*')) {
            const regex = new RegExp(pattern.replace('*', '.*'));
            return regex.test(item);
          }
          return item.includes(pattern);
        });
        
        if (!isTestFile) {
          results.push(fullPath);
        }
      }
    });
  } catch (error) {
    console.error(`Error leyendo directorio ${dir}:`, error.message);
  }
  
  return results;
}

/**
 * Analiza un archivo en busca de issues
 */
function analyzeFile(filePath, fileContent) {
  const issues = [];
  const lines = fileContent.split('\n');
  
  // Verificar longitud del archivo
  if (lines.length > CONFIG.MAX_FILE_LINES) {
    issues.push({
      id: 'SMELL-001',
      category: 'code-smells',
      severity: 'MAJOR',
      name: 'Archivo muy grande',
      file: filePath,
      line: 1,
      message: `Archivo tiene ${lines.length} líneas (máx: ${CONFIG.MAX_FILE_LINES})`,
      solution: 'Dividir en componentes o módulos más pequeños',
    });
  }
  
  // Buscar patrones en cada línea
  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    
    // Seguridad
    RULES.security.forEach(rule => {
      const pattern = CONFIG.PATTERNS[rule.pattern];
      if (!pattern) return;
      
      const matches = line.match(pattern);
      if (matches) {
        matches.forEach(match => {
          // Verificar excepciones para magic numbers
          if (rule.pattern === 'magicNumbers') {
            const isExcluded = CONFIG.MAGIC_NUMBER_EXCLUDE.some(excl => excl.test(line));
            if (isExcluded) return;
          }
          
          issues.push({
            id: rule.id,
            category: 'security',
            severity: rule.severity,
            name: rule.name,
            file: filePath,
            line: lineNumber,
            message: match,
            solution: rule.solution,
          });
        });
      }
    });
    
    // Bugs
    RULES.bugs.forEach(rule => {
      const pattern = CONFIG.PATTERNS[rule.pattern];
      if (!pattern) return;
      
      const matches = line.match(pattern);
      if (matches) {
        matches.forEach(match => {
          issues.push({
            id: rule.id,
            category: 'bugs',
            severity: rule.severity,
            name: rule.name,
            file: filePath,
            line: lineNumber,
            message: match,
            solution: rule.solution,
          });
        });
      }
    });
  });
  
  return issues;
}

/**
 * Calcula métricas del proyecto
 */
function calculateMetrics(files, fileContents) {
  const metrics = {
    totalFiles: files.length,
    totalLines: 0,
    avgFileLines: 0,
    maxFileLines: 0,
    maxFile: '',
    typeCoverage: {
      total: 0,
      withTypes: 0,
      percentage: 0,
    },
  };
  
  files.forEach((file, index) => {
    const content = fileContents[index];
    const lines = content.split('\n').length;
    
    metrics.totalLines += lines;
    
    if (lines > metrics.maxFileLines) {
      metrics.maxFileLines = lines;
      metrics.maxFile = file;
    }
    
    // Estimación básica de cobertura de tipos
    const anyMatches = (content.match(/:\s*any/g) || []).length;
    const explicitTypes = (content.match(/:\s*(string|number|boolean|object|Array|Record|Interface)/g) || []).length;
    
    metrics.typeCoverage.total += anyMatches + explicitTypes;
    metrics.typeCoverage.withTypes += explicitTypes;
  });
  
  metrics.avgFileLines = Math.round(metrics.totalLines / metrics.totalFiles);
  metrics.typeCoverage.percentage = metrics.typeCoverage.total > 0
    ? Math.round((metrics.typeCoverage.withTypes / metrics.typeCoverage.total) * 100)
    : 100;
  
  return metrics;
}

/**
 * Genera reporte en formato Markdown
 */
function generateReport(results, metrics) {
  const timestamp = new Date().toISOString().split('T')[0];
  
  // Contar issues por severidad
  const bySeverity = {
    CRITICAL: results.issues.filter(i => i.severity === 'CRITICAL').length,
    MAJOR: results.issues.filter(i => i.severity === 'MAJOR').length,
    MINOR: results.issues.filter(i => i.severity === 'MINOR').length,
  };
  
  // Contar issues por categoría
  const byCategory = {
    security: results.issues.filter(i => i.category === 'security').length,
    bugs: results.issues.filter(i => i.category === 'bugs').length,
    'code-smells': results.issues.filter(i => i.category === 'code-smells').length,
  };
  
  // Calificación
  let grade = 'A';
  let gradeColor = '🟢';
  if (bySeverity.CRITICAL > 5 || bySeverity.MAJOR > 20) {
    grade = 'C';
    gradeColor = '🔴';
  } else if (bySeverity.CRITICAL > 2 || bySeverity.MAJOR > 10) {
    grade = 'B';
    gradeColor = '🟡';
  }
  
  const report = `# 🔍 Reporte de Auditoría de Código

## Proyecto: ${path.basename(process.cwd())}
**Fecha:** ${timestamp}
**Archivos analizados:** ${metrics.totalFiles}
**Líneas totales:** ${metrics.totalLines}

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Archivos analizados | ${metrics.totalFiles} |
| Líneas de código | ${metrics.totalLines} |
| Promedio líneas/archivo | ${metrics.avgFileLines} |
| Archivo más grande | ${path.basename(metrics.maxFile)} (${metrics.maxFileLines} líneas) |
| Cobertura de tipos | ${metrics.typeCoverage.percentage}% |

### Issues Encontrados

| Severidad | Cantidad |
|-----------|----------|
| 🔴 Crítico | ${bySeverity.CRITICAL} |
| 🟡 Mayor | ${bySeverity.MAJOR} |
| 🟢 Menor | ${bySeverity.MINOR} |
| **Total** | **${results.issues.length}** |

### Por Categoría

| Categoría | Cantidad |
|-----------|----------|
| 🔒 Seguridad | ${byCategory.security} |
| 🐛 Bugs | ${byCategory.bugs} |
| 👃 Code Smells | ${byCategory['code-smells']} |

**Calificación:** ${gradeColor} **${grade}**

---

## 🚨 Issues Críticos

${formatIssues(results.issues.filter(i => i.severity === 'CRITICAL'))}

## ⚠️ Issues Mayores

${formatIssues(results.issues.filter(i => i.severity === 'MAJOR'))}

## ℹ️ Issues Menores

${formatIssues(results.issues.filter(i => i.severity === 'MINOR'))}

---

## 📈 Archivos Más Grandes

${getLargestFiles(results.files)}

## ✅ Plan de Acción Recomendado

### Prioridad 1: Seguridad (Esta semana)
${getActionPlan(results.issues, 'security')}

### Prioridad 2: Bugs Críticos (Esta semana)
${getActionPlan(results.issues, 'bugs', 'CRITICAL')}

### Prioridad 3: Bugs Mayores (Próxima semana)
${getActionPlan(results.issues, 'bugs', 'MAJOR')}

### Prioridad 4: Code Smells (Este mes)
${getActionPlan(results.issues, 'code-smells')}

---

## 📋 Checklist de Pre-Producción

- [ ] Todos los issues críticos resueltos
- [ ] Issues mayores resueltos o justificados
- [ ] Cobertura de tipos > 80%
- [ ] Ningún archivo > 500 líneas
- [ ] Console.log removidos en producción
- [ ] Variables sensibles en .env

---

*Reporte generado por Code Audit Skill v1.0.0*
*${new Date().toISOString()}*
`;

  return report;
}

/**
 * Formatea una lista de issues en Markdown
 */
function formatIssues(issues) {
  if (issues.length === 0) {
    return '✅ No se encontraron issues en esta categoría.\n';
  }
  
  return issues.map(issue => {
    const relativePath = path.relative(process.cwd(), issue.file);
    return `### ${issue.id}: ${issue.name}
**Severidad:** ${issue.severity}
**Ubicación:** \`${relativePath}:${issue.line}\`
**Problema:** \`${issue.message}\`
**Solución:** ${issue.solution}

`;
  }).join('\n');
}

/**
 * Obtiene lista de archivos más grandes
 */
function getLargestFiles(files) {
  // Esta función se mejoraría pasando los contenidos
  return '_Ver sección de métricas para detalles_\n';
}

/**
 * Genera plan de acción basado en issues
 */
function getActionPlan(issues, category, severity = null) {
  const filtered = issues.filter(i => {
    if (i.category !== category) return false;
    if (severity && i.severity !== severity) return false;
    return true;
  });
  
  if (filtered.length === 0) {
    return '- ✅ No hay acciones pendientes en esta categoría';
  }
  
  return filtered.slice(0, 5).map(issue => {
    const relativePath = path.relative(process.cwd(), issue.file);
    return `- [ ] **${issue.id}** en \`${relativePath}:${issue.line}\` - ${issue.name}`;
  }).join('\n');
}

// ============================================
// FUNCIÓN PRINCIPAL
// ============================================

function main() {
  const targetDir = process.argv[2] || process.cwd();
  
  console.log('🔍 Code Audit Skill v1.0.0');
  console.log('========================');
  console.log(`📁 Directorio: ${targetDir}`);
  console.log('');
  
  // Encontrar archivos
  console.log('📂 Buscando archivos TypeScript/JavaScript...');
  const files = findFiles(targetDir);
  console.log(`✅ ${files.length} archivos encontrados`);
  
  if (files.length === 0) {
    console.log('❌ No se encontraron archivos para auditar');
    return;
  }
  
  // Analizar archivos
  console.log('🔬 Analizando archivos...');
  const allIssues = [];
  const fileContents = [];
  
  files.forEach((file, index) => {
    try {
      const content = fs.readFileSync(file, 'utf-8');
      fileContents.push(content);
      
      const issues = analyzeFile(file, content);
      allIssues.push(...issues);
      
      // Progreso
      if ((index + 1) % 10 === 0) {
        console.log(`   Progreso: ${index + 1}/${files.length} archivos`);
      }
    } catch (error) {
      console.error(`   Error analizando ${file}:`, error.message);
    }
  });
  
  // Calcular métricas
  console.log('📊 Calculando métricas...');
  const metrics = calculateMetrics(files, fileContents);
  
  // Generar resultados
  const results = {
    files,
    issues: allIssues,
    metrics,
  };
  
  // Generar reporte
  console.log('📝 Generando reporte...');
  const report = generateReport(results, metrics);
  
  // Guardar reporte
  const outputPath = path.join(process.cwd(), 'AUDIT_REPORT.md');
  fs.writeFileSync(outputPath, report);
  
  // Resumen en consola
  console.log('');
  console.log('✅ ¡Auditoría completada!');
  console.log('========================');
  console.log(`📄 Reporte guardado en: ${outputPath}`);
  console.log('');
  console.log('📊 Resumen:');
  console.log(`   Archivos: ${metrics.totalFiles}`);
  console.log(`   Líneas: ${metrics.totalLines}`);
  console.log(`   Issues: ${allIssues.length}`);
  console.log(`   - Críticos: ${allIssues.filter(i => i.severity === 'CRITICAL').length}`);
  console.log(`   - Mayores: ${allIssues.filter(i => i.severity === 'MAJOR').length}`);
  console.log(`   - Menores: ${allIssues.filter(i => i.severity === 'MINOR').length}`);
  console.log('');
  
  // Recomendación
  const criticalCount = allIssues.filter(i => i.severity === 'CRITICAL').length;
  if (criticalCount > 0) {
    console.log('🚨 ATENCIÓN: Hay issues críticos que deben atenderse de inmediato');
  } else {
    console.log('✅ ¡Bien! No hay issues críticos');
  }
}

// Ejecutar
main();
