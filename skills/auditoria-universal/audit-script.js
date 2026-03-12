#!/usr/bin/env node

/**
 * 🔍 Auditoría Universal de Código
 * 
 * Script de auditoría multi-lenguaje que soporta:
 * - PHP
 * - JavaScript/TypeScript
 * - Python
 * - Java
 * - C#
 * - Ruby
 * - Go
 * - Y más...
 * 
 * Uso: node audit-script.js [directorio] [opciones]
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================
// CONFIGURACIÓN
// ============================================

const CONFIG = {
  // Extensiones por lenguaje
  extensions: {
    php: ['.php'],
    js: ['.js', '.jsx', '.mjs'],
    ts: ['.ts', '.tsx'],
    python: ['.py', '.pyw'],
    java: ['.java'],
    csharp: ['.cs'],
    ruby: ['.rb'],
    go: ['.go'],
    css: ['.css', '.scss', '.sass', '.less'],
    html: ['.html', '.htm'],
    json: ['.json'],
    xml: ['.xml'],
    yaml: ['.yml', '.yaml'],
    md: ['.md'],
  },

  // Directorios a excluir
  excludeDirs: [
    'node_modules',
    'vendor',
    'dist',
    'build',
    '.git',
    'coverage',
    '.next',
    'out',
    'bin',
    'obj',
    'target',
    'vendor',
    'bower_components',
  ],

  // Límites recomendados
  limits: {
    maxFileLines: 500,
    maxFunctionLines: 50,
    maxClassLines: 300,
    maxNestingLevel: 4,
  },

  // Patrones de búsqueda por categoría
  patterns: {
    // Seguridad
    security: [
      {
        id: 'SEC-001',
        name: 'Credenciales hardcodeadas',
        pattern: /(password|passwd|pwd|contraseña)\s*[:=]\s*['"][^'"]{4,}['"]/gi,
        severity: 'CRITICAL',
        languages: ['all'],
      },
      {
        id: 'SEC-002',
        name: 'API keys expuestas',
        pattern: /(api[_-]?key|apikey|API[_-]?KEY)\s*[:=]\s*['"][^'"]{16,}['"]/gi,
        severity: 'CRITICAL',
        languages: ['all'],
      },
      {
        id: 'SEC-003',
        name: 'Contraseñas en código',
        pattern: /(secret|token|auth|bearer)\s*[:=]\s*['"][^'"]{8,}['"]/gi,
        severity: 'CRITICAL',
        languages: ['all'],
      },
      {
        id: 'SEC-004',
        name: 'Tokens de acceso hardcodeados',
        pattern: /(access[_-]?token|refresh[_-]?token)\s*[:=]\s*['"][^'"]{20,}['"]/gi,
        severity: 'CRITICAL',
        languages: ['all'],
      },
      {
        id: 'SEC-005',
        name: 'Datos sensibles en logs',
        pattern: /console\.(log|info|warn|error|debug)\s*\([^)]*(password|secret|token|api[_-]?key)[^)]*\)/gi,
        severity: 'MAJOR',
        languages: ['js', 'ts'],
      },
      {
        id: 'SEC-006',
        name: 'SQL dinámico sin sanitizar',
        pattern: /(query|execute|rawQuery)\s*\(\s*['"`][^)]*\$\{?/gi,
        severity: 'CRITICAL',
        languages: ['php', 'js', 'ts', 'python'],
      },
      {
        id: 'SEC-007',
        name: 'Eval/execute dinámico',
        pattern: /(eval|execute|exec|system|passthru|shell_exec)\s*\(/gi,
        severity: 'MAJOR',
        languages: ['php', 'js', 'python'],
      },
      {
        id: 'SEC-008',
        name: 'Rutas con información sensible',
        pattern: /['"`](\/admin|\/config|\/\.env|\/backup|\/database)['"`]/gi,
        severity: 'MINOR',
        languages: ['all'],
      },
    ],

    // Bugs
    bugs: [
      {
        id: 'BUG-001',
        name: 'Variables no inicializadas',
        pattern: /(?:var|let|const)\s+\w+\s*;/gi,
        severity: 'MAJOR',
        languages: ['js', 'ts'],
      },
      {
        id: 'BUG-002',
        name: 'Funciones sin retorno explícito',
        pattern: /function\s+\w+\s*\([^)]*\)\s*:\s*(string|number|boolean|array|object)/gi,
        severity: 'MINOR',
        languages: ['php', 'ts'],
      },
      {
        id: 'BUG-003',
        name: 'Catch vacío o sin manejar',
        pattern: /catch\s*\(\s*(\w+|\s*)\s*\)\s*\{\s*\}/gi,
        severity: 'MAJOR',
        languages: ['all'],
      },
      {
        id: 'BUG-004',
        name: 'Console.log/print en producción',
        pattern: /(console\.(log|info|warn|error|debug)|print_r|var_dump|dd)\s*\(/gi,
        severity: 'MINOR',
        languages: ['all'],
      },
      {
        id: 'BUG-005',
        name: 'Código muerto/inaccesible',
        pattern: /return\s*;[\s\S]{0,100}(throw|return|break|continue)/gi,
        severity: 'MINOR',
        languages: ['all'],
      },
      {
        id: 'BUG-006',
        name: 'Imports no utilizados',
        pattern: /import\s+.*\s+from\s+['"].*['"];[\s\S]{0,500}(?!.*\b\1\b)/gi,
        severity: 'MINOR',
        languages: ['js', 'ts', 'php'],
      },
      {
        id: 'BUG-007',
        name: 'Variables no utilizadas',
        pattern: /(?:var|let|const)\s+(\w+)\s*=\s*[^;]+;[\s\S]{0,1000}(?!\1)/gi,
        severity: 'MINOR',
        languages: ['js', 'ts'],
      },
      {
        id: 'BUG-008',
        name: 'Condiciones siempre verdaderas/falsas',
        pattern: /if\s*\(\s*(true|false|1|0)\s*\)/gi,
        severity: 'MAJOR',
        languages: ['all'],
      },
    ],

    // Code Smells
    smells: [
      {
        id: 'SMELL-001',
        name: 'Archivos muy grandes',
        check: 'checkFileLines',
        severity: 'MAJOR',
        languages: ['all'],
      },
      {
        id: 'SMELL-002',
        name: 'Funciones/métodos muy largos',
        check: 'checkFunctionLines',
        severity: 'MAJOR',
        languages: ['all'],
      },
      {
        id: 'SMELL-003',
        name: 'Clases muy grandes',
        check: 'checkClassLines',
        severity: 'MAJOR',
        languages: ['php', 'js', 'ts', 'java', 'csharp'],
      },
      {
        id: 'SMELL-004',
        name: 'Anidamiento excesivo',
        check: 'checkNestingLevel',
        severity: 'MINOR',
        languages: ['all'],
      },
      {
        id: 'SMELL-005',
        name: 'Magic numbers',
        pattern: /\b[0-9]{2,}\b/g,
        exclude: /[0-9]+(px|em|rem|%|vh|vw)|v=\d+|id=\d+/,
        severity: 'MINOR',
        languages: ['all'],
      },
      {
        id: 'SMELL-006',
        name: 'Nombres muy cortos',
        pattern: /(?:function|class|const|let|var)\s+(\w{1})\s*[\(=:]/gi,
        severity: 'MINOR',
        languages: ['all'],
      },
      {
        id: 'SMELL-007',
        name: 'Nombres muy largos',
        pattern: /(?:function|class|const|let|var)\s+(\w{51,})\s*[\(=:]/gi,
        severity: 'MINOR',
        languages: ['all'],
      },
      {
        id: 'SMELL-008',
        name: 'Comentarios TODO/FIXME',
        pattern: /\/\/\s*(TODO|FIXME|XXX|HACK)/gi,
        severity: 'MINOR',
        languages: ['all'],
      },
    ],
  },
};

// ============================================
// FUNCIONES DE ANÁLISIS
// ============================================

/**
 * Encuentra todos los archivos de código en un directorio
 */
function findFiles(dir, languages = null) {
  let results = [];
  
  try {
    const items = fs.readdirSync(dir);
    
    items.forEach(item => {
      // Excluir directorios
      if (CONFIG.excludeDirs.includes(item)) return;
      
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        results = results.concat(findFiles(fullPath, languages));
      } else {
        // Verificar extensión
        const ext = path.extname(item).toLowerCase();
        
        let shouldInclude = false;
        
        if (languages) {
          // Filtrar por lenguajes específicos
          languages.forEach(lang => {
            if (CONFIG.extensions[lang] && CONFIG.extensions[lang].includes(ext)) {
              shouldInclude = true;
            }
          });
        } else {
          // Incluir todos los lenguajes soportados
          Object.values(CONFIG.extensions).forEach(exts => {
            if (exts.includes(ext)) {
              shouldInclude = true;
            }
          });
        }
        
        if (shouldInclude) {
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
 * Detecta el lenguaje de un archivo
 */
function detectLanguage(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  
  for (const [lang, extensions] of Object.entries(CONFIG.extensions)) {
    if (extensions.includes(ext)) {
      return lang;
    }
  }
  
  return 'unknown';
}

/**
 * Analiza un archivo en busca de issues
 */
function analyzeFile(filePath, fileContent) {
  const issues = [];
  const lines = fileContent.split('\n');
  const language = detectLanguage(filePath);
  
  // Verificar longitud del archivo
  if (lines.length > CONFIG.limits.maxFileLines) {
    issues.push({
      id: 'SMELL-001',
      category: 'code-smells',
      severity: 'MAJOR',
      name: 'Archivo muy grande',
      file: filePath,
      line: 1,
      message: `Archivo tiene ${lines.length} líneas (máx: ${CONFIG.limits.maxFileLines})`,
      solution: 'Dividir en componentes o módulos más pequeños',
      language,
    });
  }
  
  // Buscar patrones de seguridad
  CONFIG.patterns.security.forEach(rule => {
    if (!rule.pattern) return;
    if (!rule.languages.includes('all') && !rule.languages.includes(language)) return;
    
    lines.forEach((line, index) => {
      const matches = line.match(rule.pattern);
      if (matches) {
        matches.forEach(match => {
          issues.push({
            id: rule.id,
            category: 'security',
            severity: rule.severity,
            name: rule.name,
            file: filePath,
            line: index + 1,
            message: match,
            solution: getSolution(rule.id),
            language,
          });
        });
      }
    });
  });
  
  // Buscar patrones de bugs
  CONFIG.patterns.bugs.forEach(rule => {
    if (!rule.pattern) return;
    if (!rule.languages.includes('all') && !rule.languages.includes(language)) return;
    
    lines.forEach((line, index) => {
      const matches = line.match(rule.pattern);
      if (matches) {
        matches.forEach(match => {
          issues.push({
            id: rule.id,
            category: 'bugs',
            severity: rule.severity,
            name: rule.name,
            file: filePath,
            line: index + 1,
            message: match,
            solution: getSolution(rule.id),
            language,
          });
        });
      }
    });
  });
  
  // Buscar patrones de code smells
  CONFIG.patterns.smells.forEach(rule => {
    if (!rule.pattern) return;
    if (!rule.languages.includes('all') && !rule.languages.includes(language)) return;
    
    lines.forEach((line, index) => {
      const matches = line.match(rule.pattern);
      if (matches) {
        matches.forEach(match => {
          // Verificar exclusiones para magic numbers
          if (rule.id === 'SMELL-005' && rule.exclude) {
            if (rule.exclude.test(line)) return;
          }
          
          issues.push({
            id: rule.id,
            category: 'code-smells',
            severity: rule.severity,
            name: rule.name,
            file: filePath,
            line: index + 1,
            message: match,
            solution: getSolution(rule.id),
            language,
          });
        });
      }
    });
  });
  
  return issues;
}

/**
 * Obtiene la solución recomendada para un issue
 */
function getSolution(ruleId) {
  const solutions = {
    'SEC-001': 'Mover a variables de entorno',
    'SEC-002': 'Usar variables de entorno con prefijo apropiado',
    'SEC-003': 'Usar autenticación segura y variables de entorno',
    'SEC-004': 'Nunca hardcodear tokens, usar OAuth o similar',
    'SEC-005': 'Remover logs en producción o usar logger seguro',
    'SEC-006': 'Usar prepared statements o query builder',
    'SEC-007': 'Evitar eval, usar alternativas seguras',
    'SEC-008': 'Remover o proteger rutas sensibles',
    'BUG-001': 'Inicializar variables con valor por defecto',
    'BUG-002': 'Agregar retorno explícito en todas las rutas',
    'BUG-003': 'Manejar errores apropiadamente o hacer log',
    'BUG-004': 'Remover logs de producción',
    'BUG-005': 'Remover código inaccesible',
    'BUG-006': 'Remover imports no utilizados',
    'BUG-007': 'Remover variables no utilizadas',
    'BUG-008': 'Revisar lógica de condición',
    'SMELL-001': 'Dividir archivo en componentes más pequeños',
    'SMELL-002': 'Extraer funciones más pequeñas',
    'SMELL-003': 'Dividir clase en múltiples clases',
    'SMELL-004': 'Reducir anidamiento extrayendo funciones',
    'SMELL-005': 'Extraer constantes con nombres descriptivos',
    'SMELL-006': 'Usar nombres más descriptivos',
    'SMELL-007': 'Usar nombres más concisos',
    'SMELL-008': 'Completar o remover TODOs',
  };
  
  return solutions[ruleId] || 'Revisar y corregir';
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
    byLanguage: {},
  };
  
  files.forEach((file, index) => {
    const content = fileContents[index];
    const lines = content.split('\n').length;
    const language = detectLanguage(file);
    
    metrics.totalLines += lines;
    
    if (lines > metrics.maxFileLines) {
      metrics.maxFileLines = lines;
      metrics.maxFile = file;
    }
    
    // Contar por lenguaje
    if (!metrics.byLanguage[language]) {
      metrics.byLanguage[language] = { files: 0, lines: 0 };
    }
    metrics.byLanguage[language].files++;
    metrics.byLanguage[language].lines += lines;
  });
  
  metrics.avgFileLines = Math.round(metrics.totalLines / metrics.totalFiles);
  
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
  
  // Contar issues por lenguaje
  const byLanguage = {};
  results.issues.forEach(issue => {
    if (!byLanguage[issue.language]) {
      byLanguage[issue.language] = 0;
    }
    byLanguage[issue.language]++;
  });
  
  // Calificación
  let grade = 'A';
  let gradeColor = '🟢';
  if (bySeverity.CRITICAL > 10 || bySeverity.MAJOR > 50) {
    grade = 'D';
    gradeColor = '🔴';
  } else if (bySeverity.CRITICAL > 5 || bySeverity.MAJOR > 30) {
    grade = 'C';
    gradeColor = '🔴';
  } else if (bySeverity.CRITICAL > 2 || bySeverity.MAJOR > 15) {
    grade = 'B';
    gradeColor = '🟡';
  }
  
  const report = `# 🔍 Reporte de Auditoría Universal de Código

## Proyecto: ${path.basename(process.cwd())}
**Fecha:** ${timestamp}
**Archivos analizados:** ${metrics.totalFiles}
**Líneas totales:** ${metrics.totalLines}
**Lenguajes detectados:** ${Object.keys(metrics.byLanguage).join(', ')}

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Archivos analizados | ${metrics.totalFiles} |
| Líneas de código | ${metrics.totalLines} |
| Promedio líneas/archivo | ${metrics.avgFileLines} |
| Archivo más grande | ${path.basename(metrics.maxFile)} (${metrics.maxFileLines} líneas) |

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

### Por Lenguaje

| Lenguaje | Issues |
|----------|--------|
${Object.entries(byLanguage).map(([lang, count]) => `| ${lang} | ${count} |`).join('\n')}

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

${getLargestFiles(results.files, metrics)}

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
- [ ] Ningún archivo > 500 líneas
- [ ] 0 credenciales hardcodeadas
- [ ] 0 API keys expuestas
- [ ] Logs removidos en producción

---

*Reporte generado por Code Audit Universal Skill v1.0.0*
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
  
  // Agrupar por ID
  const grouped = {};
  issues.forEach(issue => {
    if (!grouped[issue.id]) {
      grouped[issue.id] = [];
    }
    grouped[issue.id].push(issue);
  });
  
  return Object.entries(grouped).map(([id, issues]) => {
    const firstIssue = issues[0];
    const relativePath = path.relative(process.cwd(), firstIssue.file);
    
    return `### ${id}: ${firstIssue.name}
**Severidad:** ${firstIssue.severity}
**Ubicación:** \`${relativePath}:${firstIssue.line}\`
**Problema:** \`${firstIssue.message}\`
**Solución:** ${firstIssue.solution}
**Lenguaje:** ${firstIssue.language}
${issues.length > 1 ? `\n**Ocurrencias:** ${issues.length} veces\n` : ''}

`;
  }).join('\n');
}

/**
 * Obtiene lista de archivos más grandes
 */
function getLargestFiles(files, metrics) {
  if (!metrics.maxFile) {
    return '_No hay datos disponibles_\n';
  }
  
  const relativePath = path.relative(process.cwd(), metrics.maxFile);
  return `- \`${relativePath}\` (${metrics.maxFileLines} líneas)\n`;
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
  const args = process.argv.slice(2);
  const targetDir = args.find(arg => !arg.startsWith('--')) || process.cwd();
  
  // Parsear opciones
  const options = {
    lang: args.find(arg => arg.startsWith('--lang='))?.split('=')[1],
    category: args.find(arg => arg.startsWith('--category='))?.split('=')[1],
    severity: args.find(arg => arg.startsWith('--severity='))?.split('=')[1],
    output: args.find(arg => arg.startsWith('--output='))?.split('=')[1] || 'AUDIT_REPORT_UNIVERSAL.md',
    format: args.find(arg => arg.startsWith('--format='))?.split('=')[1] || 'markdown',
    verbose: args.includes('--verbose'),
  };
  
  console.log('🔍 Auditoría Universal de Código v1.0.0');
  console.log('========================');
  console.log(`📁 Directorio: ${targetDir}`);
  if (options.lang) {
    console.log(`📝 Lenguaje: ${options.lang}`);
  }
  console.log('');
  
  // Determinar lenguajes a auditar
  const languages = options.lang ? [options.lang] : null;
  
  // Encontrar archivos
  console.log('📂 Buscando archivos...');
  const files = findFiles(targetDir, languages);
  console.log(`✅ ${files.length} archivos encontrados`);
  
  if (files.length === 0) {
    console.log('❌ No se encontraron archivos para auditar');
    return;
  }
  
  // Detectar lenguajes presentes
  const detectedLanguages = [...new Set(files.map(f => detectLanguage(f)))];
  console.log(`📝 Lenguajes detectados: ${detectedLanguages.join(', ')}`);
  
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
  
  // Filtrar por categoría si se especificó
  if (options.category) {
    const filteredIssues = allIssues.filter(i => i.category === options.category);
    console.log(`📝 Filtrado por categoría: ${options.category} (${filteredIssues.length} issues)`);
  }
  
  // Filtrar por severidad si se especificó
  if (options.severity) {
    const filteredIssues = allIssues.filter(i => i.severity === options.severity.toUpperCase());
    console.log(`📝 Filtrado por severidad: ${options.severity} (${filteredIssues.length} issues)`);
  }
  
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
  const outputPath = path.join(process.cwd(), options.output);
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
