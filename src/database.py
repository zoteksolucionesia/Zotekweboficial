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
            INSERT INTO conversation_history (phone_number, content, role)
            VALUES (%s, %s, 'user')
        """, (phone_number, user_message))
        cursor.execute("""
            INSERT INTO conversation_history (phone_number, content, role)
            VALUES (%s, %s, 'assistant')
        """, (phone_number, assistant_response))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"ERROR add_to_conversation_history: {e}")

def get_conversation_history(phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT content, role, created_at
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
                     fecha_hora: str, motivo: str = None) -> Optional[int]:
    """Guarda una nueva cita en la base de datos."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO citas (client_id, paciente_nombre, cliente_telefono, fecha_hora, motivo)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (client_id, paciente_nombre, cliente_telefono, fecha_hora, motivo))
        cita_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"DB: Cita guardada con ID={cita_id} para cliente {client_id}")
        return cita_id
    except Exception as e:
        logger.error(f"ERROR save_appointment: {e}")
        return None


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


if __name__ == "__main__":
    init_db()
