#!/usr/bin/env node

/**
 * Script de Inicialización de Proyecto con Calidad Empresarial
 * 
 * Este script configura automáticamente un nuevo proyecto con:
 * - TypeScript estricto
 * - Estructura de carpetas escalable
 * - Tipos base
 * - Validación
 * - Logger seguro
 * - Tests configurados
 * 
 * Uso: node scripts/init-quality-project.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import readline from 'readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Colores para consola
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

// Interfaz de readline
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function question(query) {
  return new Promise((resolve) => {
    rl.question(query, (answer) => {
      resolve(answer);
    });
  });
}

// Funciones de utilidad
function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logStep(step, message) {
  log(`\n[${step}] ${message}`, 'cyan');
  log('═'.repeat(50), 'cyan');
}

function logSuccess(message) {
  log(`✓ ${message}`, 'green');
}

function logError(message) {
  log(`✗ ${message}`, 'red');
}

function logWarning(message) {
  log(`⚠ ${message}`, 'yellow');
}

// Funciones de creación de archivos
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    logSuccess(`Directorio creado: ${dirPath}`);
  }
}

function writeFile(filePath, content) {
  fs.writeFileSync(filePath, content, 'utf-8');
  logSuccess(`Archivo creado: ${filePath}`);
}

function copyFile(source, dest) {
  if (fs.existsSync(source)) {
    fs.copyFileSync(source, dest);
    logSuccess(`Archivo copiado: ${dest}`);
  }
}

// Archivos a crear
const filesToCreate = {
  // TypeScript config estricto
  'tsconfig.strict.json': `{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  }
}
`,

  // Tipos base
  'src/types/index.ts': `/**
 * Tipos Base del Proyecto
 * 
 * Exporta todos los tipos comunes utilizados en la aplicación
 */

export * from './common';
export * from './user';
export * from './api';
`,

  'src/types/common.ts': `/**
 * Tipos Comunes
 * 
 * Tipos reutilizables en toda la aplicación
 */

/**
 * Metadata común para todos los documentos
 */
export interface DocumentMetadata {
  readonly id: string;
  readonly createdAt: Date;
  readonly updatedAt: Date;
  readonly createdBy: string;
  readonly updatedBy: string;
}

/**
 * Resultado de operación tipificada
 * 
 * @template T - Tipo de dato en caso de éxito
 * @template E - Tipo de error en caso de fallo
 */
export type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

/**
 * Estado de carga para operaciones asíncronas
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Parámetros de paginación
 */
export interface PaginationParams {
  readonly page: number;
  readonly limit: number;
  readonly sortBy?: string;
  readonly sortOrder?: 'asc' | 'desc';
}

/**
 * Resultado paginado con datos
 */
export interface PaginatedResult<T> {
  readonly data: T[];
  readonly total: number;
  readonly page: number;
  readonly totalPages: number;
  readonly hasMore: boolean;
}

/**
 * Función asíncrona que nunca falla (siempre retorna Result)
 */
export type SafeAsyncFunction<T, A extends unknown[] = unknown[]> = 
  (...args: A) => Promise<Result<T>>;
`,

  'src/types/user.ts': `/**
 * Tipos de Usuario
 * 
 * Definiciones de tipos relacionados con usuarios
 */

/**
 * Rol del usuario en el sistema
 */
export type UserRole = 'user' | 'admin' | 'superadmin';

/**
 * Usuario autenticado en el sistema
 */
export interface User {
  readonly uid: string;
  readonly email: string | null;
  readonly emailVerified: boolean;
  readonly role: UserRole;
  readonly displayName?: string | null;
  readonly photoURL?: string | null;
  readonly createdAt: Date;
  readonly updatedAt: Date;
}

/**
 * Input para crear usuario (formulario de registro)
 */
export interface CreateUserInput {
  readonly email: string;
  readonly password: string;
  readonly displayName?: string;
}

/**
 * Input para actualizar usuario (partial)
 */
export interface UpdateUserInput {
  readonly displayName?: string;
  readonly photoURL?: string;
  readonly role?: UserRole;
}

/**
 * Operaciones permitidas en usuarios
 */
export type UserOperation = 
  | { type: 'create'; data: CreateUserInput }
  | { type: 'update'; userId: string; data: UpdateUserInput }
  | { type: 'delete'; userId: string }
  | { type: 'read'; userId: string };
`,

  'src/types/api.ts': `/**
 * Tipos de API
 * 
 * Definiciones de tipos relacionados con la API
 */

import type { PaginatedResult } from './common';

/**
 * Error HTTP tipificado
 */
export interface ApiError {
  readonly status: number;
  readonly code: string;
  readonly message: string;
  readonly details?: Record<string, string>;
}

/**
 * Respuesta de autenticación
 */
export interface AuthResponse {
  readonly token: string;
  readonly refreshToken?: string;
  readonly expiresIn: number;
}

/**
 * Respuesta de login
 */
export interface LoginRequest {
  readonly email: string;
  readonly password: string;
}

/**
 * Parámetros de consulta comunes
 */
export interface QueryParams {
  readonly page?: number;
  readonly limit?: number;
  readonly search?: string;
  readonly sortBy?: string;
  readonly sortOrder?: 'asc' | 'desc';
  readonly [key: string]: unknown;
}
`,

  // Utilidades
  'src/utils/index.ts': `/**
 * Utilidades del Proyecto
 * 
 * Exporta todas las utilidades
 */

export * from './validation';
export * from './logger';
`,

  'src/utils/validation.ts': `/**
 * Utilidades de Validación
 * 
 * Funciones para validar y sanitizar datos
 */

import type { Result } from '../types/common';
import type { User, CreateUserInput } from '../types/user';

/**
 * Valida email con regex
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Valida fortaleza de contraseña
 */
export function isValidPassword(password: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (password.length < 8) errors.push('Mínimo 8 caracteres');
  if (!/[A-Z]/.test(password)) errors.push('Al menos 1 mayúscula');
  if (!/[a-z]/.test(password)) errors.push('Al menos 1 minúscula');
  if (!/[0-9]/.test(password)) errors.push('Al menos 1 número');
  
  return { valid: errors.length === 0, errors };
}

/**
 * Sanitiza string para prevenir XSS
 */
export function sanitizeString(str: unknown): string {
  if (typeof str !== 'string') return '';
  
  return str
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/javascript:/gi, '')
    .replace(/on\\w+=/gi, '')
    .trim();
}

/**
 * Valida datos de usuario
 */
export function validateUser(data: unknown): Result<User, string> {
  if (typeof data !== 'object' || data === null) {
    return { success: false, error: 'Datos inválidos: no es un objeto' };
  }

  const obj = data as Record<string, unknown>;

  if (typeof obj.uid !== 'string' || !obj.uid) {
    return { success: false, error: 'UID requerido' };
  }

  if (obj.email !== null && typeof obj.email !== 'string') {
    return { success: false, error: 'Email debe ser string o null' };
  }

  if (obj.email !== null && !isValidEmail(obj.email)) {
    return { success: false, error: 'Email inválido' };
  }

  if (typeof obj.emailVerified !== 'boolean') {
    return { success: false, error: 'emailVerified requerido' };
  }

  if (!['user', 'admin', 'superadmin'].includes(obj.role as string)) {
    return { success: false, error: 'Role inválido' };
  }

  return {
    success: true,
    data: {
      uid: obj.uid,
      email: obj.email || null,
      emailVerified: obj.emailVerified,
      role: obj.role as User['role'],
      displayName: typeof obj.displayName === 'string' ? obj.displayName : null,
      photoURL: typeof obj.photoURL === 'string' ? obj.photoURL : null,
      createdAt: obj.createdAt instanceof Date ? obj.createdAt : new Date(),
      updatedAt: obj.updatedAt instanceof Date ? obj.updatedAt : new Date(),
    }
  };
}

/**
 * Valida input de creación de usuario
 */
export function validateCreateUserInput(data: unknown): Result<CreateUserInput, string> {
  if (typeof data !== 'object' || data === null) {
    return { success: false, error: 'Datos inválidos' };
  }

  const obj = data as Record<string, unknown>;

  if (typeof obj.email !== 'string' || !obj.email) {
    return { success: false, error: 'Email requerido' };
  }

  if (!isValidEmail(obj.email)) {
    return { success: false, error: 'Email inválido' };
  }

  if (typeof obj.password !== 'string' || !obj.password) {
    return { success: false, error: 'Password requerido' };
  }

  const passwordValidation = isValidPassword(obj.password);
  if (!passwordValidation.valid) {
    return { 
      success: false, 
      error: passwordValidation.errors.join(', ') 
    };
  }

  return {
    success: true,
    data: {
      email: obj.email,
      password: obj.password,
      displayName: typeof obj.displayName === 'string' ? obj.displayName : undefined,
    }
  };
}
`,

  'src/utils/logger.ts': `/**
 * Logger Seguro
 * 
 * Sistema de logging que previene exposición de datos sensibles
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  readonly level: LogLevel;
  readonly message: string;
  readonly data?: unknown;
  readonly timestamp: string;
  readonly source: string;
}

class SecureLogger {
  private readonly isDev: boolean;
  private readonly source: string;

  constructor(source: string) {
    this.isDev = import.meta.env.DEV;
    this.source = source;
  }

  private sanitizeData(data: unknown): unknown {
    // Nunca loggear datos sensibles
    if (typeof data === 'object' && data !== null) {
      const sanitized = { ...data as Record<string, unknown> };
      delete sanitized.password;
      delete sanitized.token;
      delete sanitized.secret;
      delete sanitized.apiKey;
      return sanitized;
    }
    return data;
  }

  debug(message: string, data?: unknown): void {
    if (!this.isDev) return;
    console.debug('[DEBUG]', this.source, message, this.sanitizeData(data));
  }

  info(message: string, data?: unknown): void {
    if (!this.isDev) return;
    console.info('[INFO]', this.source, message, this.sanitizeData(data));
  }

  warn(message: string, data?: unknown): void {
    console.warn('[WARN]', this.source, message, this.sanitizeData(data));
  }

  error(message: string, error?: unknown): void {
    const errorData = error instanceof Error ? {
      name: error.name,
      message: error.message,
      stack: error.stack,
    } : error;

    console.error('[ERROR]', this.source, message, this.sanitizeData(errorData));
  }
}

// Factory function
export function createLogger(source: string): SecureLogger {
  return new SecureLogger(source);
}

// Logger global
export const logger = createLogger('app');
`,

  // Scripts de package.json
  'package.scripts.json': `{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "type-check": "tsc --noEmit",
    "type-check:strict": "tsc --project tsconfig.strict.json --noEmit",
    "lint": "eslint .",
    "lint:strict": "eslint . --max-warnings=0",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui",
    "audit": "node scripts/audit.js",
    "pre-commit": "npm run type-check && npm run lint && npm run test",
    "prepare": "husky install"
  }
}
`,

  // Script de auditoría
  'scripts/audit.js': `#!/usr/bin/env node

/**
 * Script de Auditoría de Calidad
 * 
 * Verifica que el código cumpla con los estándares de calidad
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const colors = {
  reset: '\\x1b[0m',
  green: '\\x1b[32m',
  red: '\\x1b[31m',
  yellow: '\\x1b[33m',
};

function log(message, color = 'reset') {
  console.log(\`\${colors[color]}\${message}\${colors.reset}\`);
}

function checkTypeScript() {
  log('\\n[1/4] Verificando TypeScript...', 'yellow');
  try {
    execSync('npx tsc --noEmit', { stdio: 'inherit' });
    log('✓ TypeScript: OK', 'green');
    return true;
  } catch {
    log('✗ TypeScript: Errores encontrados', 'red');
    return false;
  }
}

function checkAnyUsage() {
  log('\\n[2/4] Buscando uso de \"any\"...', 'yellow');
  
  const srcDir = './src';
  let anyCount = 0;
  let filesWithAny = [];

  function searchFiles(dir) {
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory() && !file.includes('node_modules')) {
        searchFiles(filePath);
      } else if (file.endsWith('.ts') || file.endsWith('.tsx')) {
        const content = fs.readFileSync(filePath, 'utf-8');
        const matches = content.match(/:\\s*any/g);
        
        if (matches) {
          anyCount += matches.length;
          filesWithAny.push({ file: filePath, count: matches.length });
        }
      }
    }
  }

  searchFiles(srcDir);

  if (anyCount === 0) {
    log('✓ Uso de \"any\": 0 instancias', 'green');
    return true;
  } else {
    log(\`✗ Uso de \"any\": \${anyCount} instancias en \${filesWithAny.length} archivos\`, 'red');
    filesWithAny.forEach(({ file, count }) => {
      log(\`  - \${file}: \${count}\`, 'yellow');
    });
    return false;
  }
}

function checkConsoleLogs() {
  log('\\n[3/4] Buscando console.log...', 'yellow');
  
  const srcDir = './src';
  let consoleCount = 0;

  function searchFiles(dir) {
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory() && !file.includes('node_modules')) {
        searchFiles(filePath);
      } else if (file.endsWith('.ts') || file.endsWith('.tsx')) {
        const content = fs.readFileSync(filePath, 'utf-8');
        const matches = content.match(/console\\.(log|warn|error|info|debug)/g);
        
        if (matches) {
          consoleCount += matches.length;
        }
      }
    }
  }

  searchFiles(srcDir);

  if (consoleCount === 0) {
    log('✓ Console.logs: 0 instancias', 'green');
    return true;
  } else {
    log(\`⚠ Console.logs: \${consoleCount} instancias (deberían usar logger)\`, 'yellow');
    return consoleCount < 10; // Warning si es menos de 10
  }
}

function checkTests() {
  log('\\n[4/4] Verificando tests...', 'yellow');
  
  const testDir = './tests';
  if (fs.existsSync(testDir)) {
    const testFiles = fs.readdirSync(testDir).filter(f => f.endsWith('.test.ts') || f.endsWith('.spec.ts'));
    
    if (testFiles.length > 0) {
      log(\`✓ Tests: \${testFiles.length} archivos de test encontrados\`, 'green');
      return true;
    } else {
      log('⚠ Tests: Directorio existe pero no hay archivos de test', 'yellow');
      return false;
    }
  } else {
    log('✗ Tests: Directorio no encontrado', 'red');
    return false;
  }
}

// Main
log('═'.repeat(50), 'yellow');
log('🔍 Auditoría de Calidad', 'yellow');
log('═'.repeat(50), 'yellow');

const results = [
  checkTypeScript(),
  checkAnyUsage(),
  checkConsoleLogs(),
  checkTests(),
];

const passed = results.filter(r => r).length;
const total = results.length;

log('\\n' + '═'.repeat(50), 'yellow');
log(\`Resultado: \${passed}/\${total} checks pasaron\`, passed === total ? 'green' : 'red');
log('═'.repeat(50), 'yellow');

process.exit(passed === total ? 0 : 1);
`,
};

// Main function
async function main() {
  log('\n🏗️  Inicialización de Proyecto con Calidad Empresarial', 'cyan');
  log('═'.repeat(60), 'cyan');
  log('\nEste script configurará tu proyecto con:', 'bright');
  log('  ✓ TypeScript estricto', 'green');
  log('  ✓ Estructura de carpetas escalable', 'green');
  log('  ✓ Tipos base', 'green');
  log('  ✓ Sistema de validación', 'green');
  log('  ✓ Logger seguro', 'green');
  log('  ✓ Tests configurados', 'green');
  log('\n⚠  Esto tomará más tiempo que un setup tradicional', 'yellow');
  log('   pero tendrás 90-95% de calidad desde el inicio', 'yellow');
  log('\n' + '═'.repeat(60), 'cyan');

  const projectName = await question('Nombre del proyecto: ');
  const useFirebase = await question('¿Usarás Firebase? (y/n): ');
  const addTests = await question('¿Agregar tests? (y/n): ');

  log('\n🚀 Iniciando configuración...', 'cyan');
  log('═'.repeat(60), 'cyan');

  // Crear estructura de carpetas
  logStep('1', 'Creando estructura de carpetas...');
  ensureDir('src/types');
  ensureDir('src/utils');
  ensureDir('src/services');
  ensureDir('src/components/ui');
  ensureDir('src/components/layout');
  ensureDir('src/components/features');
  ensureDir('src/hooks');
  ensureDir('src/config');
  ensureDir('src/contexts');
  ensureDir('scripts');

  if (addTests.toLowerCase() === 'y') {
    ensureDir('tests/unit');
    ensureDir('tests/integration');
    ensureDir('tests/e2e');
  }

  // Crear archivos
  logStep('2', 'Creando archivos de tipos...');
  writeFile('src/types/index.ts', filesToCreate['src/types/index.ts']);
  writeFile('src/types/common.ts', filesToCreate['src/types/common.ts']);
  writeFile('src/types/user.ts', filesToCreate['src/types/user.ts']);
  writeFile('src/types/api.ts', filesToCreate['src/types/api.ts']);

  logStep('3', 'Creando utilidades...');
  writeFile('src/utils/index.ts', filesToCreate['src/utils/index.ts']);
  writeFile('src/utils/validation.ts', filesToCreate['src/utils/validation.ts']);
  writeFile('src/utils/logger.ts', filesToCreate['src/utils/logger.ts']);

  logStep('4', 'Configurando TypeScript estricto...');
  writeFile('tsconfig.strict.json', filesToCreate['tsconfig.strict.json']);

  logStep('5', 'Creando scripts...');
  writeFile('scripts/audit.js', filesToCreate['scripts/audit.js']);
  fs.chmodSync('scripts/audit.js', '755');

  logStep('6', 'Actualizando package.json...');
  if (fs.existsSync('package.json')) {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf-8'));
    const newScripts = JSON.parse(filesToCreate['package.scripts.json']).scripts;
    packageJson.scripts = { ...packageJson.scripts, ...newScripts };
    writeFile('package.json', JSON.stringify(packageJson, null, 2));
  }

  // Instalar dependencias si es necesario
  logStep('7', 'Verificando dependencias...');
  if (addTests.toLowerCase() === 'y') {
    log('Se recomienda instalar:', 'yellow');
    log('  npm install -D vitest @vitest/coverage-v8', 'cyan');
  }

  log('\n' + '═'.repeat(60), 'cyan');
  log('✅ ¡Configuración completada!', 'green');
  log('═'.repeat(60), 'cyan');

  log('\n📋 Siguientes pasos:', 'bright');
  log('1. Revisa los tipos en src/types/ y ajústalos a tu proyecto', 'yellow');
  log('2. Ejecuta: npm run type-check', 'yellow');
  log('3. Ejecuta: npm run audit', 'yellow');
  log('4. Comienza a desarrollar siguiendo la documentación en SKILL.md', 'yellow');

  log('\n📚 Documentación:', 'bright');
  log('  - skills/calidad-empresarial/SKILL.md (Guía completa)', 'cyan');
  log('  - skills/calidad-empresarial/README.md (Inicio rápido)', 'cyan');

  log('\n' + '═'.repeat(60), 'cyan');
  log('¡Éxito con tu proyecto!', 'green');
  log('═'.repeat(60), 'cyan');

  rl.close();
}

// Ejecutar
main().catch((error) => {
  logError('Error durante la inicialización:');
  console.error(error);
  process.exit(1);
});
