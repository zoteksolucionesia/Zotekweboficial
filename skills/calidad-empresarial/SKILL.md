# 🏗️ SKILL: Desarrollo de Proyectos con Calidad Empresarial

## Descripción
Skill para desarrollar proyectos React/TypeScript con **énfasis en calidad, seguridad y escalabilidad desde el día 1**.

**Filosofía:** "Mejor lento y seguro, que rápido y problemático"

**Tiempo estimado:** 2-3x más que desarrollo tradicional
**Calidad esperada:** 90-95% desde el inicio

---

## 📋 FASES DEL DESARROLLO

### FASE 1: Fundamentos (Día 1-2)

#### 1.1 Configuración Estricta de TypeScript

**Archivo:** `tsconfig.json`
```json
{
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
    "forceConsistentCasingInFileNames": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "lib": ["ES2020"],
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Por qué:** TypeScript estricto previene el 80% de errores en runtime

---

#### 1.2 Estructura de Proyecto Escalable

```
project/
├── src/
│   ├── types/              ← Tipos TypeScript (PRIMERO)
│   │   ├── index.ts        ← Exporta todos los tipos
│   │   ├── user.ts
│   │   ├── common.ts
│   │   └── api.ts
│   │
│   ├── utils/              ← Utilidades puras
│   │   ├── validation.ts   ← Validación de datos
│   │   ├── logger.ts       ← Logger seguro
│   │   └── helpers.ts
│   │
│   ├── config/             ← Configuración
│   │   ├── firebase.ts
│   │   ├── constants.ts
│   │   └── env.ts
│   │
│   ├── hooks/              ← Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useData.ts
│   │   └── index.ts
│   │
│   ├── components/         ← Componentes UI
│   │   ├── ui/             ← Componentes base
│   │   ├── layout/         ← Layout components
│   │   └── features/       ← Feature components
│   │
│   ├── services/           ← Capa de datos
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── storage.ts
│   │
│   ├── contexts/           ← Contextos React
│   │   └── AuthContext.tsx
│   │
│   └── App.tsx
│
├── tests/                  ← Tests (desde el inicio)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .github/
│   └── workflows/
│       ├── ci.yml          ← CI/CD
│       └── security.yml    ← Security scanning
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   └── API.md
│
└── scripts/
    ├── audit.sh
    └── pre-commit.sh
```

**Por qué:** Separación clara permite escalar sin refactorizar

---

#### 1.3 Sistema de Tipos (PRIMERO QUE NADA)

**Archivo:** `src/types/user.ts`
```typescript
/**
 * Usuario autenticado en el sistema
 * 
 * @property uid - Identificador único del usuario
 * @property email - Email verificado
 * @property emailVerified - Si el email fue verificado
 * @property role - Rol del usuario (user, admin, superadmin)
 * @property createdAt - Fecha de creación
 * @property updatedAt - Última actualización
 */
export interface User {
  readonly uid: string;
  readonly email: string | null;
  readonly emailVerified: boolean;
  readonly role: 'user' | 'admin' | 'superadmin';
  readonly displayName?: string | null;
  readonly photoURL?: string | null;
  readonly createdAt: Date;
  readonly updatedAt: Date;
}

/**
 * Usuario para crear (input del formulario)
 */
export interface CreateUserInput {
  readonly email: string;
  readonly password: string;
  readonly displayName?: string;
}

/**
 * Usuario para actualizar (partial)
 */
export interface UpdateUserInput {
  readonly displayName?: string;
  readonly photoURL?: string;
  readonly role?: User['role'];
}

/**
 * Tipo seguro para operaciones de usuario
 */
export type UserOperation = 
  | { type: 'create'; data: CreateUserInput }
  | { type: 'update'; userId: string; data: UpdateUserInput }
  | { type: 'delete'; userId: string }
  | { type: 'read'; userId: string };
```

**Archivo:** `src/types/common.ts`
```typescript
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
 * Resultado de operación
 */
export type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

/**
 * Estado de carga
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Paginación
 */
export interface PaginationParams {
  readonly page: number;
  readonly limit: number;
  readonly sortBy?: string;
  readonly sortOrder?: 'asc' | 'desc';
}

/**
 * Paginación con datos
 */
export interface PaginatedResult<T> {
  readonly data: T[];
  readonly total: number;
  readonly page: number;
  readonly totalPages: number;
  readonly hasMore: boolean;
}
```

**Por qué:** Definir tipos primero previene cambios costosos después

---

### FASE 2: Seguridad y Validación (Día 2-3)

#### 2.1 Sistema de Validación

**Archivo:** `src/utils/validation.ts`
```typescript
/**
 * Validador de emails con regex seguro
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Valida fortaleza de contraseña
 * Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número
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
    .replace(/on\w+=/gi, '')
    .trim();
}

/**
 * Valida URL segura (solo HTTPS o relativa)
 */
export function isValidUrl(url: string, options: { allowRelative?: boolean } = {}): boolean {
  try {
    const parsed = new URL(url, options.allowRelative ? window.location.origin : undefined);
    return parsed.protocol === 'https:' || (options.allowRelative && url.startsWith('/'));
  } catch {
    return false;
  }
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
```

**Por qué:** Validación previene ataques y datos corruptos

---

#### 2.2 Logger Seguro

**Archivo:** `src/utils/logger.ts`
```typescript
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

  private formatEntry(level: LogLevel, message: string, data?: unknown): LogEntry {
    return {
      level,
      message,
      data,
      timestamp: new Date().toISOString(),
      source: this.source,
    };
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
    const entry = this.formatEntry('debug', message, this.sanitizeData(data));
    console.debug('[DEBUG]', entry);
  }

  info(message: string, data?: unknown): void {
    if (!this.isDev) return;
    const entry = this.formatEntry('info', message, this.sanitizeData(data));
    console.info('[INFO]', entry);
  }

  warn(message: string, data?: unknown): void {
    const entry = this.formatEntry('warn', message, this.sanitizeData(data));
    
    // En producción, solo warnings importantes
    if (this.isDev) {
      console.warn('[WARN]', entry);
    } else {
      // En producción, enviar a servicio de monitoreo
      this.sendToMonitoring(entry);
    }
  }

  error(message: string, error?: unknown): void {
    const entry = this.formatEntry('error', message, {
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : error,
    });

    // Siempre loggear errores, incluso en producción
    if (this.isDev) {
      console.error('[ERROR]', entry);
    } else {
      // En producción, enviar a servicio de monitoreo
      this.sendToMonitoring(entry);
    }
  }

  private sendToMonitoring(entry: LogEntry): void {
    // Aquí integrarías con Sentry, LogRocket, etc.
    // Por ahora, solo en consola
    if (entry.level === 'error') {
      console.error('[PRODUCTION ERROR]', entry);
    }
  }
}

// Factory function
export function createLogger(source: string): SecureLogger {
  return new SecureLogger(source);
}

// Logger global
export const logger = createLogger('app');
```

**Por qué:** Logging seguro previene exposición de datos sensibles

---

### FASE 3: Servicios con Tipos (Día 3-4)

#### 3.1 Capa de Servicios Tipificada

**Archivo:** `src/services/api.ts`
```typescript
import type { Result, PaginatedResult, PaginationParams } from '../types/common';
import type { User } from '../types/user';
import { validateUser } from '../utils/validation';
import { logger } from '../utils/logger';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.example.com';

/**
 * Error HTTP tipificado
 */
export class HttpError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly details?: Record<string, string>
  ) {
    super(`HTTP ${status}: ${code}`);
    this.name = 'HttpError';
  }
}

/**
 * Cliente HTTP seguro
 */
class HttpClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit
  ): Promise<Result<T, HttpError>> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    logger.debug('API Request', { url, method: options.method });

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        const error = new HttpError(
          response.status,
          data.error?.code || 'UNKNOWN_ERROR',
          data.error?.details
        );
        logger.error('API Error', error);
        return { success: false, error };
      }

      return { success: true, data: data as T };
    } catch (error) {
      const httpError = error instanceof HttpError 
        ? error 
        : new HttpError(500, 'NETWORK_ERROR');
      logger.error('Network Error', httpError);
      return { success: false, error: httpError };
    }
  }

  async get<T>(endpoint: string): Promise<Result<T, HttpError>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body: unknown): Promise<Result<T, HttpError>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async put<T>(endpoint: string, body: unknown): Promise<Result<T, HttpError>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  async delete<T>(endpoint: string): Promise<Result<T, HttpError>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new HttpClient();

/**
 * Servicio de Usuarios
 */
export const userService = {
  async getUser(userId: string): Promise<Result<User, HttpError>> {
    const result = await apiClient.get<User>(`/users/${userId}`);
    
    if (!result.success) {
      return result;
    }

    // Validar datos antes de retornar
    const validated = validateUser(result.data);
    
    if (!validated.success) {
      logger.error('User validation failed', validated.error);
      return {
        success: false,
        error: new HttpError(500, 'VALIDATION_ERROR'),
      };
    }

    return { success: true, data: validated.data };
  },

  async getUsers(params: PaginationParams): Promise<Result<PaginatedResult<User>, HttpError>> {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      limit: params.limit.toString(),
      ...(params.sortBy && { sortBy: params.sortBy }),
      ...(params.sortOrder && { sortOrder: params.sortOrder }),
    });

    const result = await apiClient.get<PaginatedResult<User>>(`/users?${queryParams}`);
    
    if (!result.success) {
      return result;
    }

    // Validar cada usuario
    const validatedUsers = result.data.data
      .map(user => validateUser(user))
      .filter((v): v is { success: true; data: User } => v.success)
      .map(v => v.data);

    return {
      success: true,
      data: {
        ...result.data,
        data: validatedUsers,
      },
    };
  },
};
```

**Por qué:** Capa de servicios con validación previene datos corruptos

---

### FASE 4: Componentes con Tipos (Día 4-5)

#### 4.1 Componente con Tipos Estrictos

**Archivo:** `src/components/UserProfile.tsx`
```typescript
import React, { useState, useEffect } from 'react';
import type { User } from '../types/user';
import type { Result } from '../types/common';
import { userService } from '../services/api';
import { logger } from '../utils/logger';

interface UserProfileProps {
  readonly userId: string;
  readonly onUserUpdate?: (user: User) => void;
  readonly className?: string;
}

interface UserProfileState {
  readonly user: User | null;
  readonly loading: boolean;
  readonly error: string | null;
}

/**
 * Componente de Perfil de Usuario
 * 
 * Muestra información del usuario con validación completa
 * 
 * @param userId - ID del usuario a mostrar
 * @param onUserUpdate - Callback cuando el usuario se actualiza
 * @param className - Clases CSS adicionales
 */
export const UserProfile: React.FC<UserProfileProps> = ({
  userId,
  onUserUpdate,
  className = '',
}) => {
  const [state, setState] = useState<UserProfileState>({
    user: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let mounted = true;

    const loadUser = async () => {
      setState(prev => ({ ...prev, loading: true, error: null }));

      const result = await userService.getUser(userId);

      if (!mounted) return;

      if (result.success) {
        setState({
          user: result.data,
          loading: false,
          error: null,
        });
      } else {
        setState({
          user: null,
          loading: false,
          error: result.error.message,
        });
        logger.error('Failed to load user', result.error);
      }
    };

    loadUser();

    return () => {
      mounted = false;
    };
  }, [userId]);

  if (state.loading) {
    return (
      <div className={`user-profile-loading ${className}`}>
        <span>Cargando...</span>
      </div>
    );
  }

  if (state.error || !state.user) {
    return (
      <div className={`user-profile-error ${className}`}>
        <span>Error: {state.error || 'Usuario no encontrado'}</span>
      </div>
    );
  }

  return (
    <div className={`user-profile ${className}`}>
      <div className="user-profile-header">
        {state.user.photoURL && (
          <img
            src={state.user.photoURL}
            alt={state.user.displayName || 'User'}
            className="user-profile-avatar"
          />
        )}
        <div className="user-profile-info">
          <h2 className="user-profile-name">
            {state.user.displayName || 'Sin nombre'}
          </h2>
          <p className="user-profile-email">{state.user.email}</p>
          <span className={`user-profile-role role-${state.user.role}`}>
            {state.user.role}
          </span>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
```

**Por qué:** Componentes con tipos estrictos previenen bugs de UI

---

### FASE 5: Tests (Día 5-6)

#### 5.1 Tests Unitarios

**Archivo:** `tests/unit/validation.test.ts`
```typescript
import { describe, it, expect } from 'vitest';
import { isValidEmail, isValidPassword, sanitizeString, validateUser } from '../../src/utils/validation';

describe('Validation Utils', () => {
  describe('isValidEmail', () => {
    it('should return true for valid emails', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name@domain.co.uk')).toBe(true);
    });

    it('should return false for invalid emails', () => {
      expect(isValidEmail('invalid')).toBe(false);
      expect(isValidEmail('test@')).toBe(false);
      expect(isValidEmail('@example.com')).toBe(false);
    });
  });

  describe('isValidPassword', () => {
    it('should return true for strong passwords', () => {
      const result = isValidPassword('Password123');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should return false for weak passwords', () => {
      const result = isValidPassword('weak');
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });

  describe('sanitizeString', () => {
    it('should remove HTML tags', () => {
      expect(sanitizeString('<script>alert("xss")</script>')).toBe('');
      expect(sanitizeString('Hello <b>World</b>')).toBe('Hello World');
    });

    it('should remove dangerous protocols', () => {
      expect(sanitizeString('javascript:alert(1)')).toBe('');
    });

    it('should return empty string for non-strings', () => {
      expect(sanitizeString(null)).toBe('');
      expect(sanitizeString(123)).toBe('');
    });
  });

  describe('validateUser', () => {
    it('should validate correct user data', () => {
      const userData = {
        uid: '123',
        email: 'test@example.com',
        emailVerified: true,
        role: 'user',
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      const result = validateUser(userData);
      expect(result.success).toBe(true);
    });

    it('should reject invalid user data', () => {
      const result = validateUser({ invalid: 'data' });
      expect(result.success).toBe(false);
    });
  });
});
```

**Por qué:** Tests previenen regresiones

---

## ✅ CHECKLIST DE CALIDAD

### Antes de Cada Commit

- [ ] TypeScript compila sin errores (`npm run type-check`)
- [ ] Tests pasan (`npm run test`)
- [ ] No hay `any` en el código nuevo
- [ ] No hay `console.log` (usar `logger`)
- [ ] Datos validados antes de usar
- [ ] Errores manejados con try/catch
- [ ] Tipos definidos para nuevas entidades

### Antes de Cada Pull Request

- [ ] Auditoría de seguridad pasa
- [ ] Cobertura de tests > 80%
- [ ] Documentación actualizada
- [ ] No hay console warnings
- [ ] Lighthouse score > 90

### Antes de Producción

- [ ] Tests E2E pasan
- [ ] Auditoría de seguridad externa
- [ ] Backup de base de datos
- [ ] Plan de rollback definido
- [ ] Monitoreo configurado

---

## 📊 MÉTRICAS DE CALIDAD

| Métrica | Objetivo | Mínimo Aceptable |
|---------|----------|------------------|
| **Errores TypeScript** | 0 | 0 |
| **Uso de `any`** | 0 | < 5 |
| **Cobertura de tests** | > 90% | > 80% |
| **Lighthouse score** | > 95 | > 90 |
| **Bundle size** | < 300KB | < 500KB |
| **Tiempo de carga** | < 2s | < 3s |
| **Issues de seguridad** | 0 | 0 críticos |

---

## 🚀 CÓMO USAR ESTA SKILL

### Para un Nuevo Proyecto:

1. **Copia esta carpeta** a tu nuevo proyecto
2. **Ejecuta:** `node scripts/init-project.js`
3. **Define tipos primero:** `src/types/`
4. **Configura validación:** `src/utils/validation.ts`
5. **Crea servicios:** `src/services/`
6. **Desarrolla componentes:** `src/components/`
7. **Escribe tests:** `tests/`
8. **Ejecuta auditoría:** `npm run audit`

### Comandos Disponibles:

```bash
npm run type-check      # Verifica tipos TypeScript
npm run test            # Ejecuta tests
npm run test:coverage   # Tests con cobertura
npm run lint            # Linting
npm run audit           # Auditoría de seguridad
npm run build           # Build de producción
npm run pre-commit      # Checks antes de commit
```

---

## ⏱️ TIEMPOS ESTIMADOS

| Fase | Tiempo | Entregable |
|------|--------|------------|
| **1. Fundamentos** | 2 días | TypeScript + Estructura + Tipos |
| **2. Seguridad** | 1 día | Validación + Logger |
| **3. Servicios** | 1 día | API tipificada |
| **4. Componentes** | 1 día | UI con tipos |
| **5. Tests** | 1 día | Tests unitarios |
| **TOTAL** | **6 días** | **Proyecto 90%+ calidad** |

**Comparado con desarrollo tradicional:**
- Tradicional: 2-3 días, 70% calidad
- Esta skill: 6 días, 90-95% calidad

**ROI:** Menos bugs, menos refactorización, más escalable

---

## 📈 BENEFICIOS

### Inmediatos:
- ✅ Código más seguro desde el inicio
- ✅ Menos bugs en producción
- ✅ Mejor DX (Developer Experience)

### A Largo Plazo:
- ✅ Más fácil de mantener
- ✅ Más fácil de escalar
- ✅ Más fácil de migrar (de Firebase, etc.)
- ✅ Menos deuda técnica

---

*Skill creada: Marzo 2026*
*Versión: 1.0.0*
*Calidad sobre velocidad*
