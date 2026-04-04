import os
import json
import threading
import logging
from psycopg2 import pool as pg_pool
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List, Tuple

# Cargar variables de entorno desde .env
load_dotenv()

from .services.encryption_service import encrypt_client_fields, decrypt_client_fields

logger = logging.getLogger(__name__)

# La URL de conexión se debe configurar en el archivo .env o en el panel del hosting
DATABASE_URL = os.environ.get("DATABASE_URL")

# ============================================
# CONNECTION POOL
# ============================================
_pool: Optional[pg_pool.ThreadedConnectionPool] = None
_pool_lock = threading.Lock()


class _PooledConnection:
    """Wraps a psycopg2 connection from the pool. close() returns it to the pool."""

    def __init__(self, conn, pool: pg_pool.ThreadedConnectionPool):
        self._conn = conn
        self._pool = pool

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        if self._conn is not None:
            self._pool.putconn(self._conn)
            self._conn = None

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _get_pool() -> pg_pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                if not DATABASE_URL:
                    raise ValueError("DATABASE_URL no está configurada. Verifica tu archivo .env.")
                _pool = pg_pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=10,
                    dsn=DATABASE_URL,
                    sslmode='require',
                )
                logger.info("PostgreSQL connection pool initialized (min=2, max=10)")
    return _pool


def get_connection() -> _PooledConnection:
    """Obtiene una conexión del pool de PostgreSQL."""
    try:
        pool = _get_pool()
        conn = pool.getconn()
        return _PooledConnection(conn, pool)
    except Exception as e:
        logger.error(f"Error obteniendo conexión del pool: {e}")
        raise

import re

def sanitize_phone(phone: str) -> str:
    """Elimina caracteres no numéricos de un número de teléfono."""
    return re.sub(r'[^\d+]', '', phone or '')

def sanitize_message_preview(text: str, max_len: int = 100) -> str:
    """Sanitiza y trunca un mensaje para preview en logs."""
    if not text:
        return ''
    cleaned = text.replace('\n', ' ').strip()
    return cleaned[:max_len]

def normalize_phone(phone: str, country_code: str = '52') -> str:
    """
    Normaliza número de teléfono a formato E.164 (+52XXXXXXXXXX para México).

    Ejemplos:
    - 3121149153 → +523121149153
    - 523121149153 → +523121149153
    - +523121149153 → +523121149153
    - 521234567890 → +5212345678990 (quita el 1 extra de México)
    - +52 312 1149153 → +523121149153
    """
    if not phone:
        return ''

    # Limpiar caracteres no numéricos excepto +
    cleaned = sanitize_phone(phone)

    # Si ya tiene formato E.164, retornar
    if cleaned.startswith('+'):
        return cleaned

    # Si empieza con 521 (México con 1 extra), quitar el 1
    if cleaned.startswith('521'):
        cleaned = '52' + cleaned[3:]

    # Si empieza con 52 pero no con +, agregar +
    if cleaned.startswith('52'):
        return '+' + cleaned

    # Si son 10 dígitos (formato local México sin 52), agregar +52
    if len(cleaned) == 10 and cleaned.isdigit():
        return f'+52{cleaned}'

    # Fallback: agregar código de país
    return f'+{country_code}{cleaned}'

def init_db():
    """Inicializa la base de datos con el esquema multitenencia relacional."""
    logger.info("Inicializando base de datos PostgreSQL (InsForge)...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Tabla de Clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                whatsapp_token TEXT NOT NULL,
                phone_number_id TEXT NOT NULL UNIQUE,
                verify_token TEXT NOT NULL,
                system_instruction TEXT,
                stripe_api_key TEXT,
                bank_name TEXT,
                clabe TEXT,
                beneficiary_name TEXT,
                menu_json JSONB,
                plan TEXT DEFAULT 'free',
                email TEXT DEFAULT '',
                calendly_url TEXT DEFAULT '',
                vapi_target TEXT DEFAULT 'paciente',
                vapi_professional_phone TEXT,
                google_calendar_id TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Migración segura de columnas en clients
        for col, col_type in [
            ('vapi_target', "TEXT DEFAULT 'paciente'"),
            ('vapi_professional_phone', 'TEXT'),
            ('google_calendar_id', 'TEXT')
        ]:
            try:
                cursor.execute(f'ALTER TABLE clients ADD COLUMN IF NOT EXISTS {col} {col_type}')
            except Exception:
                pass

        # Tabla de Base de Conocimientos (Extraído de PDFs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                source_file TEXT,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de Citas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citas (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                cliente_telefono TEXT,
                paciente_nombre TEXT,
                fecha_hora TEXT,
                motivo TEXT,
                reminder_status TEXT DEFAULT NULL,
                vapi_call_id TEXT DEFAULT NULL,
                reminder_intentos INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Agregar columnas de VAPI si no existen (migración segura)
        for col, col_type in [
            ('reminder_status', 'TEXT'),
            ('vapi_call_id', 'TEXT'),
            ('reminder_intentos', 'INTEGER DEFAULT 0'),
        ]:
            try:
                cursor.execute(f'ALTER TABLE citas ADD COLUMN IF NOT EXISTS {col} {col_type}')
            except Exception:
                pass

        # Tabla de Message Logs (para métricas y facturación)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_logs (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                direction TEXT NOT NULL,
                phone_number TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para message_logs
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_client ON message_logs(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_date ON message_logs(created_at)')
        
        # Tabla de Historial de Conversación (para contexto con Gemini)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id SERIAL PRIMARY KEY,
                phone_number TEXT NOT NULL,
                content TEXT NOT NULL,
                is_user INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para conversation_history
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_phone ON conversation_history(phone_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_date ON conversation_history(created_at)')

        # Tabla de códigos 2FA (reemplaza almacenamiento en memoria)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_codes (
                email TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL
            )
        ''')

        # Tabla de consumo de eventos (Twilio/VAPI/WhatsApp)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumo_eventos (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                proveedor TEXT NOT NULL,
                tipo TEXT NOT NULL,
                costo_usd NUMERIC(10,4) DEFAULT 0,
                duracion_segundos INTEGER,
                estado TEXT,
                evento_id TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumo_client ON consumo_eventos(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumo_timestamp ON consumo_eventos(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumo_proveedor ON consumo_eventos(proveedor)')

        # Tabla de tarifas por cliente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tarifas_cliente (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                fee_mensual_mxn NUMERIC(10,2) DEFAULT 0,
                precio_por_mensaje_mxn NUMERIC(10,4) DEFAULT 0,
                precio_por_llamada_mxn NUMERIC(10,4) DEFAULT 0,
                activo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Base de datos PostgreSQL multitenencia inicializada (Tablas verificadas).")
    except Exception as e:
        logger.error(f"Error al inicializar PostgreSQL: {e}")


def get_client_by_phone_id(phone_number_id):
    """Obtiene los datos de un cliente por su Phone Number ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients WHERE phone_number_id = %s", (phone_number_id,))
        client = cursor.fetchone()
        cursor.close()
        conn.close()
        return decrypt_client_fields(dict(client)) if client else None
    except Exception as e:
        logger.error(f"ERROR get_client_by_phone_id: {e}")
        return None

def list_clients():
    """Retorna una lista de todos los clientes de la base de datos."""
    if not DATABASE_URL:
        return []

    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        real_clients = []
        for row in rows:
            c = decrypt_client_fields(dict(row))
            if isinstance(c.get('menu_json'), dict):
                c['menu_json'] = json.dumps(c['menu_json'])
            real_clients.append(c)
        return real_clients
    except Exception as e:
        logger.error(f"ERROR list_clients: {e}")
        return []


def add_client(data: dict) -> bool:
    """Inserta un nuevo cliente en la base de datos con campos sensibles cifrados."""
    try:
        data = encrypt_client_fields(data)
        conn = get_connection()
        cursor = conn.cursor()

        fields = [k for k in data.keys() if k not in ('id', 'created_at')]
        values = []
        for key in fields:
            val = data[key]
            if key == 'menu_json' and isinstance(val, str):
                try:
                    val = json.loads(val)
                except Exception:
                    pass
            if isinstance(val, (dict, list)):
                val = json.dumps(val)
            values.append(val)

        placeholders = ['%s'] * len(fields)
        query = f"INSERT INTO clients ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"ERROR add_client: {e}")
        return False


def update_client(client_id, data):
    """Actualiza los datos de un cliente. Si no existe, lo inserta."""
    try:
        data = encrypt_client_fields(data)
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar si existe
        cursor.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
        exists = cursor.fetchone()

        fields = []
        values = []
        for key, value in data.items():
            if key not in ['id', 'created_at']:
                fields.append(f"{key} = %s")
                if key == 'menu_json' and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value))
                else:
                    values.append(value)

        if exists:
            # Update
            if not fields:
                return False
            values.append(client_id)
            query = f"UPDATE clients SET {', '.join(fields)} WHERE id = %s"
            cursor.execute(query, values)
        else:
            # Insert (preserving the requested ID if possible)
            cols = ['id'] + [k for k in data.keys() if k not in ['id', 'created_at']]
            placeholders = ['%s'] * len(cols)
            
            insert_vals = [client_id]
            for key in cols[1:]:
                val = data.get(key)
                if key == 'menu_json' and isinstance(val, str):
                    try: val = json.loads(val)
                    except: pass
                if isinstance(val, (dict, list)):
                    insert_vals.append(json.dumps(val))
                else:
                    insert_vals.append(val)
                    
            query = f"INSERT INTO clients ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, insert_vals)

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"ERROR update_client: {e}")
        return False


def get_client_by_id(client_id):
    # Demos hardcodeados como respaldo o para pruebas rápidas
    demo_ids = {
        "demo_restaurante": {"id": "demo_restaurante", "name": "🍕 La Trattoria Demo", "phone_number_id": "demo_restaurante", "system_instruction": "Eres el asistente del restaurante La Trattoria..."},
        "demo_clinica": {"id": "demo_clinica", "name": "🏥 Clínica San Juan Demo", "phone_number_id": "demo_clinica", "system_instruction": "Eres el asistente de la Clínica San Juan..."},
        "demo_tienda": {"id": "demo_tienda", "name": "🛍 Urban Vibe Style Demo", "phone_number_id": "demo_tienda", "system_instruction": "Eres el asistente de la tienda Urban Vibe..."},
        "demo_dental_001": {"id": "demo_dental_001", "name": "🦷 SonrisaPerfecta IA Demo", "phone_number_id": "demo_dental_001", "system_instruction": "Eres el asistente de SonrisaPerfecta IA..."},
        "demo_psychology_001": {"id": "demo_psychology_001", "name": "🧠 MenteSana Bot Demo", "phone_number_id": "demo_psychology_001", "system_instruction": "Eres el asistente del Dr. Alejandro Ruiz..."}
    }
    
    # Soporte para IDs numéricos viejos de demo
    demo_map_old = {9991: "demo_restaurante", 9992: "demo_clinica", 9993: "demo_tienda"}
    
    try:
        cid_str = str(client_id)
        if cid_str in demo_ids:
            return demo_ids[cid_str]
        
        cid_int = None
        try: cid_int = int(client_id)
        except: pass

        if cid_int in demo_map_old:
            return demo_ids[demo_map_old[cid_int]]
    except:
        pass
        
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
        client = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if client:
            c_dict = decrypt_client_fields(dict(client))
            if isinstance(c_dict.get('menu_json'), dict):
                c_dict['menu_json'] = json.dumps(c_dict['menu_json'])
            return c_dict
        return None
    except Exception as e:
        logger.error(f"ERROR get_client_by_id: {e}")
        return None


def duplicate_client(client_id):
    """
    Duplica un cliente en la base de datos, incluyendo su base de conocimientos.
    """
    import time
    original = get_client_by_id(client_id)
    if not original:
        return None

    timestamp = int(time.time() * 1000)
    new_name = f"{original.get('name', 'Copia')} (Copia {time.strftime('%Y-%m-%d')})"
    new_phone_number_id = f"client_{timestamp}"
    new_verify_token = f"verify_{timestamp}"
    
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
            INSERT INTO clients (
                name, whatsapp_token, phone_number_id, verify_token,
                system_instruction, stripe_api_key, bank_name, clabe,
                beneficiary_name, menu_json, plan, email, calendly_url,
                vapi_target, vapi_professional_phone, google_calendar_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        ''', (
            new_name, 
            "", 
            new_phone_number_id, 
            new_verify_token,
            original.get('system_instruction', ''), 
            original.get('stripe_api_key', ''),
            original.get('bank_name', ''), 
            original.get('clabe', ''), 
            original.get('beneficiary_name', ''),
            json.dumps(original.get('menu_json')) if isinstance(original.get('menu_json'), dict) else original.get('menu_json'),
            original.get('plan', 'free'), 
            "", 
            original.get('calendly_url', ''),
            original.get('vapi_target', 'paciente'),
            original.get('vapi_professional_phone', ''),
            original.get('google_calendar_id', '')
        ))
        
        new_client_id = cursor.fetchone()['id']
        
        demo_ids = [9991, 9992, 9993]
        if int(client_id) not in demo_ids:
            cursor.execute("SELECT content, source_file FROM knowledge_base WHERE client_id = %s", (client_id,))
            kb_docs = cursor.fetchall()
            for doc in kb_docs:
                cursor.execute('''
                    INSERT INTO knowledge_base (client_id, content, source_file)
                    VALUES (%s, %s, %s)
                ''', (new_client_id, doc['content'], doc['source_file']))
                
        conn.commit()
        cursor.close()
        conn.close()
        
        return get_client_by_id(new_client_id)
        
    except Exception as e:
        logger.error(f"ERROR duplicate_client: {e}")
        return None


def delete_client_db_entry(client_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return deleted
    except Exception as e:
        logger.error(f"ERROR delete_client: {e}")
        return False


def list_client_documents(client_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, source_file, updated_at FROM knowledge_base WHERE client_id = %s", (client_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"ERROR list_client_documents: {e}")
        return []

def get_client_knowledge(client_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM knowledge_base WHERE client_id = %s", (client_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return "\n".join([row[0] for row in rows])
    except Exception as e:
        return ""

def add_knowledge_entry(client_id, content, source_file=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO knowledge_base (client_id, content, source_file) VALUES (%s, %s, %s)",
            (client_id, content, source_file)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"ERROR add_knowledge_entry: {e}")
        return False

def delete_knowledge_entry(client_id, doc_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM knowledge_base WHERE client_id = %s AND id = %s",
            (client_id, doc_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"ERROR delete_knowledge_entry: {e}")
        return False

def track_message(client_id: int, direction: str = "outbound", phone_number: str = None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO message_logs (client_id, direction, phone_number)
            VALUES (%s, %s, %s)
        """, (client_id, direction, phone_number))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"ERROR track_message: {e}")

def get_monthly_message_count(client_id: int) -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM message_logs 
            WHERE client_id = %s 
            AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
        """, (client_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        return 0

def check_message_limit(client_id: int, plan: str = 'free') -> Tuple[bool, str]:
    from .config import Config
    limits = Config.get_plan_limits(plan)
    monthly_limit = limits.get('monthly_messages', 100)
    
    if monthly_limit == -1:
        return True, "Ilimitado"
    
    current_count = get_monthly_message_count(client_id)
    if current_count >= monthly_limit:
        return False, f"Límite de {monthly_limit} mensajes alcanzado. Mes: {current_count}/{monthly_limit}"
    return True, f"{monthly_limit - current_count} mensajes restantes este mes"

def get_message_stats(client_id: int = None) -> Dict[str, Any]:
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if client_id:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN direction = 'inbound' THEN 1 ELSE 0 END) as inbound,
                    SUM(CASE WHEN direction = 'outbound' THEN 1 ELSE 0 END) as outbound,
                    MIN(created_at) as first_message,
                    MAX(created_at) as last_message
                FROM message_logs 
                WHERE client_id = %s
            """, (client_id,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN direction = 'inbound' THEN 1 ELSE 0 END) as inbound,
                    SUM(CASE WHEN direction = 'outbound' THEN 1 ELSE 0 END) as outbound,
                    COUNT(DISTINCT client_id) as unique_clients,
                    MIN(created_at) as first_message,
                    MAX(created_at) as last_message
                FROM message_logs
            """)
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row and row['total'] > 0:
            return {
                'total': row['total'],
                'inbound': row['inbound'] or 0,
                'outbound': row['outbound'] or 0,
                'unique_clients': row.get('unique_clients', 0),
                'first_message': row['first_message'],
                'last_message': row['last_message']
            }
        return {'total': 0, 'inbound': 0, 'outbound': 0, 'unique_clients': 0}
    except Exception as e:
        return {'total': 0, 'inbound': 0, 'outbound': 0}

def add_to_conversation_history(phone_number: str, user_message: str, assistant_response: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversation_history (phone_number, content, is_user)
            VALUES (%s, %s, 1)
        """, (phone_number, user_message))
        cursor.execute("""
            INSERT INTO conversation_history (phone_number, content, is_user)
            VALUES (%s, %s, 0)
        """, (phone_number, assistant_response))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"ERROR add_to_conversation_history: {e}")

def get_conversation_history(phone_number: str, limit: int = 10, timeout_minutes: int = 30) -> List[Dict[str, Any]]:
    """Retorna historial reciente. Si el último mensaje tiene más de timeout_minutes, retorna vacío (nueva sesión)."""
    from datetime import datetime, timedelta, timezone
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        # Verificar si la última interacción fue hace más de timeout_minutes
        cursor.execute("""
            SELECT created_at FROM conversation_history
            WHERE phone_number = %s
            ORDER BY created_at DESC LIMIT 1
        """, (phone_number,))
        last = cursor.fetchone()
        if last:
            last_time = last['created_at']
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - last_time > timedelta(minutes=timeout_minutes):
                # Sesión expirada — limpiar historial y empezar fresco
                cursor.execute("DELETE FROM conversation_history WHERE phone_number = %s", (phone_number,))
                conn.commit()
                cursor.close()
                conn.close()
                return []
        cursor.execute("""
            SELECT content, is_user, created_at
            FROM conversation_history
            WHERE phone_number = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (phone_number, limit))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in reversed(rows)]
    except Exception as e:
        logger.error(f"ERROR get_conversation_history: {e}")
        return []

def clear_conversation_history(phone_number: str = None, older_than_days: int = 30):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if phone_number:
            cursor.execute("DELETE FROM conversation_history WHERE phone_number = %s", (phone_number,))
        else:
            cursor.execute("DELETE FROM conversation_history WHERE created_at < CURRENT_DATE - INTERVAL '%s days'", (older_than_days,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"ERROR clear_conversation_history: {e}")

def update_appointment_reminder_status(
    cita_id: int,
    status: str,
    vapi_call_id: str = None
):
    """
    Actualiza el estado de recordatorio de una cita.
    
    Args:
        cita_id: ID de la cita.
        status: 'pendiente' | 'llamando' | 'llamado' | 'fallido' | 'fallido_max'
        vapi_call_id: ID de la llamada en VAPI para tracking.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE citas
            SET 
                reminder_status = %s,
                vapi_call_id = COALESCE(%s, vapi_call_id),
                reminder_intentos = reminder_intentos + 1
            WHERE id = %s
        """, (status, vapi_call_id, cita_id))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"DB: Cita {cita_id} actualizada → reminder_status='{status}'")
    except Exception as e:
        logger.error(f"ERROR update_appointment_reminder_status: {e}")


def get_all_appointments(limit: int = 200) -> List[Dict[str, Any]]:
    """Obtiene todas las citas de todos los clientes, con nombre del cliente."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT c.paciente_nombre, c.cliente_telefono, c.fecha_hora, c.motivo,
                   c.created_at, cl.name AS cliente_nombre
            FROM citas c
            JOIN clients cl ON cl.id = c.client_id
            ORDER BY c.fecha_hora DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"ERROR get_all_appointments: {e}")
        return []


def get_appointments_by_client(client_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene las citas de un cliente, para mostrar en el dashboard admin."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM citas 
            WHERE client_id = %s 
            ORDER BY fecha_hora DESC 
            LIMIT %s
        """, (client_id, limit))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"ERROR get_appointments_by_client: {e}")
        return []


def save_appointment(client_id: int, paciente_nombre: str, cliente_telefono: str,
                     fecha_hora: str, motivo: str = None, paciente_email: str = None) -> Optional[int]:
    """Guarda una nueva cita en la base de datos."""
    try:
        # Normalizar teléfono antes de guardar
        cliente_telefono = normalize_phone(cliente_telefono)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE citas ADD COLUMN IF NOT EXISTS paciente_email TEXT")
        conn.commit()
        cursor.execute("""
            INSERT INTO citas (client_id, paciente_nombre, cliente_telefono, fecha_hora, motivo, paciente_email)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (client_id, paciente_nombre, cliente_telefono, fecha_hora, motivo, paciente_email))
        cita_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"DB: Cita guardada con ID={cita_id} para cliente {client_id}")
        return cita_id
    except Exception as e:
        logger.error(f"ERROR save_appointment: {e}")
        return None


def get_available_slots(client_id: int, horario_inicio: str = "09:00", horario_fin: str = "18:00",
                        duracion_min: int = 60, working_days: str = "1,2,3,4,5,6",
                        dias_adelante: int = 5) -> list:
    """
    Genera slots disponibles excluyendo horarios ya ocupados.
    working_days: días laborales como string CSV (1=Lun ... 7=Dom), ej. '1,2,3,4,5'
    dias_adelante: cuántos días hábiles hacia adelante buscar
    Retorna lista de strings como ['Lun 6 Abr 10:00', ...]
    """
    from datetime import datetime, timedelta
    try:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now()

        dias_laborales = {int(x.strip()) for x in working_days.split(",") if x.strip().isdigit()}
        # weekday(): 0=Lun ... 6=Dom → convertir a 1-7
        dias_habiles = []
        d = now + timedelta(days=1)
        while len(dias_habiles) < dias_adelante:
            if (d.weekday() + 1) in dias_laborales:
                dias_habiles.append(d)
            d += timedelta(days=1)

        if not dias_habiles:
            return []

        fecha_inicio = dias_habiles[0].strftime("%Y-%m-%d")
        fecha_fin    = dias_habiles[-1].strftime("%Y-%m-%d 23:59")
        cursor.execute(
            "SELECT fecha_hora FROM citas WHERE client_id = %s AND fecha_hora::text >= %s AND fecha_hora::text <= %s",
            (client_id, fecha_inicio, fecha_fin)
        )
        ocupados = {str(r[0])[:16] for r in cursor.fetchall()}
        cursor.close()
        conn.close()

        h_ini = int(horario_inicio.split(":")[0])
        m_ini = int(horario_inicio.split(":")[1]) if ":" in horario_inicio else 0
        h_fin = int(horario_fin.split(":")[0])
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        dias_semana = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

        slots = []
        for dia in dias_habiles:
            minutos = h_ini * 60 + m_ini
            fin_minutos = h_fin * 60
            while minutos < fin_minutos:
                h, m = divmod(minutos, 60)
                slot_dt = dia.replace(hour=h, minute=m, second=0, microsecond=0)
                slot_key = slot_dt.strftime("%Y-%m-%d %H:%M")
                if slot_key not in ocupados:
                    etiqueta = f"{dias_semana[dia.weekday()]} {dia.day} {meses[dia.month-1]} {h:02d}:{m:02d}"
                    slots.append(etiqueta)
                minutos += duracion_min
        return slots
    except Exception as e:
        logger.error(f"ERROR get_available_slots: {e}")
        return []


def get_client_schedules(client_id: int) -> list:
    """Retorna las franjas horarias del cliente agrupadas por día."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT day_of_week, start_time, end_time
            FROM client_schedules
            WHERE client_id = %s
            ORDER BY day_of_week, start_time
        """, (client_id,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"ERROR get_client_schedules: {e}")
        return []


def save_client_schedules(client_id: int, schedules: list) -> bool:
    """
    Reemplaza todas las franjas del cliente.
    schedules: [{"day_of_week": 1, "start_time": "09:00", "end_time": "14:00"}, ...]
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM client_schedules WHERE client_id = %s", (client_id,))
        for s in schedules:
            cur.execute("""
                INSERT INTO client_schedules (client_id, day_of_week, start_time, end_time)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (client_id, day_of_week, start_time) DO UPDATE
                SET end_time = EXCLUDED.end_time
            """, (client_id, s["day_of_week"], s["start_time"], s["end_time"]))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"ERROR save_client_schedules: {e}")
        return False


def get_available_slots_v2(client_id: int, duracion_min: int = 60, dias_adelante: int = 5, test_time: str = None) -> list:
    """
    Genera slots disponibles usando client_schedules (soporta franjas partidas).
    Excluye slots ya ocupados en la tabla citas.
    Retorna [{"label": "Lun 6 Abr 09:00", "datetime": "2026-04-06 09:00", "ocupado": False}, ...]

    Args:
        client_id: ID del cliente
        duracion_min: Duración de la cita en minutos (default 60)
        dias_adelante: Cuántos días mirar adelante (default 5)
        test_time: (TESTING ONLY) Tiempo en formato "2026-04-04 14:30" para simular
    """
    from datetime import datetime, timedelta
    try:
        schedules = get_client_schedules(client_id)
        if not schedules:
            return []

        conn = get_connection()
        cur = conn.cursor()

        # Support test mode
        if test_time:
            now = datetime.strptime(test_time, "%Y-%m-%d %H:%M")
            logger.info(f"[TEST MODE] Using test_time: {now.strftime('%Y-%m-%d %H:%M:%S %A')}")
        else:
            now = datetime.now()

        logger.info(f"get_available_slots_v2: now={now.strftime('%Y-%m-%d %H:%M:%S %A')}")

        # Días a revisar: solo dentro de los próximos 7 días calendario
        # No inventar horarios para semanas futuras
        dias = []
        d = now.replace(hour=0, minute=0, second=0, microsecond=0)
        limite = d + timedelta(days=7)  # máximo 7 días calendario
        while d < limite:
            dow = d.weekday() + 1  # 1=Lun ... 7=Dom
            if any(s["day_of_week"] == dow for s in schedules):
                dias.append(d)
            d += timedelta(days=1)

        if not dias:
            cur.close()
            conn.close()
            return []

        logger.info(f"get_available_slots_v2: dias={[d.strftime('%Y-%m-%d %A') for d in dias]}")
        fecha_inicio = dias[0].strftime("%Y-%m-%d")
        fecha_fin    = dias[-1].strftime("%Y-%m-%d 23:59")
        cur.execute(
            "SELECT fecha_hora FROM citas WHERE client_id = %s AND fecha_hora::text >= %s AND fecha_hora::text <= %s",
            (client_id, fecha_inicio, fecha_fin)
        )
        ocupados = {str(r[0])[:16] for r in cur.fetchall()}
        cur.close()
        conn.close()

        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        dias_semana = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

        slots = []
        for dia in dias:
            dow = dia.weekday() + 1
            franjas = [s for s in schedules if s["day_of_week"] == dow]
            for franja in franjas:
                h_ini = int(franja["start_time"].split(":")[0])
                m_ini = int(franja["start_time"].split(":")[1])
                h_fin = int(franja["end_time"].split(":")[0])
                m_fin = int(franja["end_time"].split(":")[1])
                minutos = h_ini * 60 + m_ini
                fin_minutos = h_fin * 60 + m_fin
                while minutos < fin_minutos:
                    h, m = divmod(minutos, 60)
                    slot_dt = dia.replace(hour=h, minute=m, second=0, microsecond=0)
                    slot_key = slot_dt.strftime("%Y-%m-%d %H:%M")

                    # Excluir slots que ya pasaron (si es hoy)
                    if slot_dt <= now:
                        minutos += duracion_min
                        continue

                    label = f"{dias_semana[dia.weekday()]} {dia.day} {meses[dia.month-1]} {h:02d}:{m:02d}"
                    slots.append({
                        "label": label,
                        "datetime": slot_key,
                        "ocupado": slot_key in ocupados
                    })
                    minutos += duracion_min

        import sys
        sys.stderr.write(f"[get_available_slots_v2] Returning {len(slots)} slots for client {client_id}\n")
        if slots:
            sys.stderr.write(f"[get_available_slots_v2] First slot: {slots[0]['label']} ({slots[0]['datetime']})\n")
        return slots
    except Exception as e:
        logger.error(f"ERROR get_available_slots_v2: {e}")
        return []


def save_lead(client_id: int, nombre: str, telefono: str, interes: str) -> bool:
    """Registra o actualiza un lead en lead_tracking."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lead_tracking (client_id, phone_number, status, last_message_response)
            VALUES (%s, %s, 'nuevo', %s)
            ON CONFLICT (client_id, phone_number) DO UPDATE
            SET status = 'interesado',
                last_message_response = EXCLUDED.last_message_response,
                updated_at = CURRENT_TIMESTAMP
        """, (client_id, telefono, f"{nombre} — {interes}"))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"ERROR save_lead: {e}")
        return False


def save_verification_code(email: str, code: str, expires_minutes: int = 10) -> bool:
    """Guarda un código 2FA en la base de datos con TTL."""
    from datetime import datetime, timedelta
    try:
        conn = get_connection()
        cursor = conn.cursor()
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)
        cursor.execute("""
            INSERT INTO verification_codes (email, code, expires_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET code = EXCLUDED.code, expires_at = EXCLUDED.expires_at
        """, (email, code, expires_at))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"ERROR save_verification_code: {e}")
        return False


def get_verification_code(email: str) -> Optional[str]:
    """Obtiene el código 2FA si existe y no ha expirado. Lo elimina tras leerlo."""
    from datetime import datetime
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM verification_codes
            WHERE email = %s AND expires_at > %s
            RETURNING code
        """, (email, datetime.now()))
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"ERROR get_verification_code: {e}")
        return None


def registrar_consumo_evento(client_id: int, proveedor: str, tipo: str, costo_usd: float = 0,
                             duracion: Optional[int] = None, estado: Optional[str] = None,
                             evento_id: Optional[str] = None) -> bool:
    """
    Registra un evento de consumo (llamada, SMS, WhatsApp).
    No debe romper el flujo principal si falla — manejo silencioso de errores.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO consumo_eventos
            (client_id, proveedor, tipo, costo_usd, duracion_segundos, estado, evento_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (client_id, proveedor, tipo, costo_usd, duracion, estado, evento_id))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Consumo registrado: client={client_id}, proveedor={proveedor}, costo=${costo_usd}")
        return True
    except Exception as e:
        logger.error(f"ERROR registrar_consumo_evento: {e}")
        return False


def get_consumo_mensual(client_id: Optional[int] = None, mes: Optional[int] = None,
                       anio: Optional[int] = None) -> Dict[str, Any]:
    """
    Obtiene el consumo del mes especificado, agrupado por proveedor y tipo.
    Si mes/anio no se especifican, usa el mes/año actual.
    """
    from datetime import datetime
    try:
        if mes is None:
            mes = datetime.now().month
        if anio is None:
            anio = datetime.now().year

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if client_id:
            cursor.execute("""
                SELECT
                    proveedor,
                    tipo,
                    COUNT(*) as cantidad,
                    SUM(costo_usd) as total_costo,
                    SUM(COALESCE(duracion_segundos, 0)) as duracion_total
                FROM consumo_eventos
                WHERE client_id = %s
                  AND EXTRACT(MONTH FROM timestamp) = %s
                  AND EXTRACT(YEAR FROM timestamp) = %s
                GROUP BY proveedor, tipo
                ORDER BY proveedor, tipo
            """, (client_id, mes, anio))
        else:
            cursor.execute("""
                SELECT
                    client_id,
                    proveedor,
                    tipo,
                    COUNT(*) as cantidad,
                    SUM(costo_usd) as total_costo,
                    SUM(COALESCE(duracion_segundos, 0)) as duracion_total
                FROM consumo_eventos
                WHERE EXTRACT(MONTH FROM timestamp) = %s
                  AND EXTRACT(YEAR FROM timestamp) = %s
                GROUP BY client_id, proveedor, tipo
                ORDER BY client_id, proveedor, tipo
            """, (mes, anio))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "mes": f"{anio}-{mes:02d}",
            "datos": [dict(r) for r in rows] if rows else []
        }
    except Exception as e:
        logger.error(f"ERROR get_consumo_mensual: {e}")
        return {"mes": f"{anio}-{mes:02d}", "datos": []}


def get_resumen_facturacion(client_id: Optional[int] = None, mes: Optional[int] = None,
                           anio: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Obtiene resumen de facturación: consumo real vs precio cobrado.
    Requiere que tarifas_cliente esté configurado.
    """
    from datetime import datetime
    try:
        if mes is None:
            mes = datetime.now().month
        if anio is None:
            anio = datetime.now().year

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if client_id:
            cursor.execute("""
                SELECT
                    c.id,
                    c.name as nombre_cliente,
                    SUM(ce.costo_usd) as costo_real_usd,
                    COALESCE(tc.fee_mensual_mxn, 0) as fee_mensual_mxn,
                    COALESCE(tc.precio_por_llamada_mxn, 0) as precio_llamada_mxn,
                    COUNT(ce.id) as total_eventos
                FROM clients c
                LEFT JOIN consumo_eventos ce ON c.id = ce.client_id
                    AND EXTRACT(MONTH FROM ce.timestamp) = %s
                    AND EXTRACT(YEAR FROM ce.timestamp) = %s
                LEFT JOIN tarifas_cliente tc ON c.id = tc.client_id AND tc.activo = TRUE
                WHERE c.id = %s
                GROUP BY c.id, c.name, tc.fee_mensual_mxn, tc.precio_por_llamada_mxn
            """, (mes, anio, client_id))
        else:
            cursor.execute("""
                SELECT
                    c.id,
                    c.name as nombre_cliente,
                    SUM(ce.costo_usd) as costo_real_usd,
                    COALESCE(tc.fee_mensual_mxn, 0) as fee_mensual_mxn,
                    COALESCE(tc.precio_por_llamada_mxn, 0) as precio_llamada_mxn,
                    COUNT(ce.id) as total_eventos
                FROM clients c
                LEFT JOIN consumo_eventos ce ON c.id = ce.client_id
                    AND EXTRACT(MONTH FROM ce.timestamp) = %s
                    AND EXTRACT(YEAR FROM ce.timestamp) = %s
                LEFT JOIN tarifas_cliente tc ON c.id = tc.client_id AND tc.activo = TRUE
                GROUP BY c.id, c.name, tc.fee_mensual_mxn, tc.precio_por_llamada_mxn
                ORDER BY c.name
            """, (mes, anio))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        resultado = []
        for row in rows:
            r = dict(row)
            r["costo_real_usd"] = float(r["costo_real_usd"] or 0)
            r["fee_mensual_mxn"] = float(r["fee_mensual_mxn"] or 0)
            resultado.append(r)
        return resultado
    except Exception as e:
        logger.error(f"ERROR get_resumen_facturacion: {e}")
        return []


if __name__ == "__main__":
    init_db()
