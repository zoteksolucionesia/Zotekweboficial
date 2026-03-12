import sqlite3
import json
import os
import re
from typing import Optional, Dict, Any, List, Tuple

# Pointing to the new data directory location
ORIGINAL_DB = os.path.join(os.path.dirname(__file__), "..", "data", "consultorio.db")
DB_NAME = ORIGINAL_DB


def sanitize_phone(phone: str, visible_digits: int = 4) -> str:
    """
    Sanitiza un número de teléfono para logs, mostrando solo los últimos dígitos.
    
    Args:
        phone: Número de teléfono a sanitizar
        visible_digits: Cantidad de dígitos visibles al final
    
    Returns:
        Número sanitizado con asteriscos
    """
    if len(phone) > visible_digits:
        return "*" * (len(phone) - visible_digits) + phone[-visible_digits:]
    return phone


def sanitize_message_preview(message: str, max_length: int = 50) -> str:
    """
    Trunca un mensaje para logs, mostrando solo un preview.
    
    Args:
        message: Mensaje a truncar
        max_length: Longitud máxima del preview
    
    Returns:
        Mensaje truncado con elipsis si es necesario
    """
    if len(message) <= max_length:
        return message
    return message[:max_length] + "..."

# Workaround for Firebase Functions (Read-only filesystem)
if os.environ.get('K_SERVICE') or os.environ.get('FIREBASE_CONFIG'):
    import shutil
    TEMP_DB = "/tmp/consultorio.db"
    if not os.path.exists(TEMP_DB):
        print(f"📦 Copying database to /tmp for writing: {ORIGINAL_DB} -> {TEMP_DB}")
        try:
            shutil.copy2(ORIGINAL_DB, TEMP_DB)
            # Ensure permissions
            os.chmod(TEMP_DB, 0o666)
        except Exception as e:
            print(f"⚠️ Error copying DB to /tmp: {e}")
            # Fallback will stay as the original read-only DB
    DB_NAME = TEMP_DB

def init_db():
    """Inicializa la base de datos con el esquema multitenencia."""
    print(f"🗄️ Connecting to database: {DB_NAME}")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Tabla de Clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                whatsapp_token TEXT NOT NULL,
                phone_number_id TEXT NOT NULL UNIQUE,
                verify_token TEXT NOT NULL,
                system_instruction TEXT,
                stripe_api_key TEXT,
                bank_name TEXT,
                clabe TEXT,
                beneficiary_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Manejar actualizaciones de esquema para tablas existentes
        cursor.execute("PRAGMA table_info(clients)")
        client_columns = [column[1] for column in cursor.fetchall()]
        
        new_cols = {
            "bank_name": "TEXT",
            "clabe": "TEXT",
            "beneficiary_name": "TEXT",
            "stripe_api_key": "TEXT",
            "menu_json": "TEXT" 
        }
        
        for col, type in new_cols.items():
            if col not in client_columns:
                print(f"🔧 Agregando columna '{col}' a la tabla 'clients'...")
                cursor.execute(f'ALTER TABLE clients ADD COLUMN {col} {type}')
        
        # Tabla de Base de Conocimientos (Extraído de PDFs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                content TEXT NOT NULL,
                source_file TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        # Asegurar que la tabla exista (si no existía)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                cliente_telefono TEXT,
                paciente_nombre TEXT,
                fecha_hora TEXT,
                motivo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')

        # Tabla de Message Logs (para métricas y facturación)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                direction TEXT NOT NULL,
                phone_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_client ON message_logs(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_date ON message_logs(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_client_date ON message_logs(client_id, created_at)')

        # Tabla de Historial de Conversación (para contexto con Gemini)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                content TEXT NOT NULL,
                is_user INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_phone ON conversation_history(phone_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_date ON conversation_history(created_at)')

        # Agregar columna 'plan' a clients si no existe
        cursor.execute("PRAGMA table_info(clients)")
        client_columns = [column[1] for column in cursor.fetchall()]
        
        if 'plan' not in client_columns:
            print("🔧 Agregando columna 'plan' a la tabla 'clients'...")
            cursor.execute("ALTER TABLE clients ADD COLUMN plan TEXT DEFAULT 'free'")

        conn.commit()
        conn.close()
        print("✅ Base de datos multitenencia inicializada.")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")

def get_client_by_phone_id(phone_number_id):
    """Obtiene los datos de un cliente por su Phone Number ID."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE phone_number_id = ?", (phone_number_id,))
        client = cursor.fetchone()
        conn.close()
        return dict(client) if client else None
    except Exception as e:
        print(f"❌ ERROR get_client_by_phone_id: {e}")
        return None

def list_clients():
    """Retorna una lista de todos los clientes, incluyendo los de demostración."""
    # Inyectar clientes demo que siempre deben estar visibles
    demo_clients = [
        {
            "id": 9991, 
            "name": "🍕 Demo Restaurante V9", 
            "phone": "521550000001",
            "phone_number_id": "demo_restaurante", 
            "email": "demo@zotek.ia", 
            "response_type": "text",
            "gemini_prompt": "Eres el asistente de una Pizzería Gourmet. Saluda con entusiasmo y ofrece las pizzas del día.",
            "created_at": "2024-01-01 00:00:00",
            "menu_json": '{"text": "¡Bienvenido a *La Trattoria*! 👋 Soy tu asistente virtual. ¿Qué te gustaría hacer hoy?", "options": [{"title": "Ver Menú", "icon": "🍕", "response": "Nuestro menú incluye pizzas a la leña, pastas frescas y postres italianos."}, {"title": "Hacer Reserva", "icon": "📅", "response": "Indícanos la fecha y hora para verificar disponibilidad."}, {"title": "Horarios", "icon": "⏰", "response": "Estamos abiertos todos los días de 12:00 PM a 11:00 PM."}], "fallback_text": "Lo siento, no entendí eso. Aquí tienes las opciones principales de La Trattoria:"}'
        },
        {
            "id": 9992, 
            "name": "🏥 Demo Clínica Dental", 
            "phone": "521550000002",
            "phone_number_id": "demo_clinica", 
            "email": "demo@zotek.ia", 
            "response_type": "text",
            "gemini_prompt": "Eres el asistente de una Clínica Dental. Ayuda a los pacientes a conocer los servicios de ortodoncia y limpieza.",
            "created_at": "2024-01-01 00:00:00",
            "menu_json": '{"text": "Bienvenido a la *Clínica San Juan*. 🏥 ¿En qué podemos ayudarte hoy?", "options": [{"title": "Agendar Cita", "icon": "📅", "response": "Por favor, dinos para qué especialidad buscas cita."}, {"title": "Especialidades", "icon": "👨‍⚕️", "response": "Contamos con Medicina General, Odontología y Pediatría."}, {"title": "Ubicación", "icon": "📍", "response": "Estamos en Av. Central #123. Haz clic aquí para ver en el mapa: https://maps.google.com"}], "fallback_text": "No comprendo tu solicitud. Selecciona una de estas opciones de la clínica:"}'
        },
        {
            "id": 9993, 
            "name": "🛍️ Demo Tienda e-Commerce", 
            "phone": "521550000003",
            "phone_number_id": "demo_tienda", 
            "email": "demo@zotek.ia", 
            "response_type": "text",
            "gemini_prompt": "Eres el asistente de una tienda de gadgets tecnológicos. Recomienda los mejores productos según las necesidades del cliente.",
            "created_at": "2024-01-01 00:00:00",
            "menu_json": '{"text": "¡Hola! Bienvenido a *Moda Urbana*. 🛍️ ✨ ¿Cómo podemos ayudarte con tu estilo hoy?", "options": [{"title": "Ver Catálogo", "icon": "👕", "response": "Nuestra nueva colección de otoño ya está disponible."}, {"title": "Tallas", "icon": "📏", "response": "Manejamos tallas desde XS hasta XL en la mayoría de nuestras prendas."}, {"title": "Devoluciones", "icon": "🔄", "response": "Tienes 30 días para realizar cambios o devoluciones con tu ticket."}], "fallback_text": "Ups, no reconozco eso. Aquí tienes lo que puedo hacer por ti en Moda Urbana:"}'
        }
    ]
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients")
        rows = cursor.fetchall()
        conn.close()
        real_clients = [dict(row) for row in rows]
        return demo_clients + real_clients
    except Exception as e:
        print(f"❌ ERROR list_clients: {e}")
        return demo_clients

def update_client(client_id, data):
    """Actualiza los datos de un cliente. Si no existe en BD (ej. demo), lo inserta."""
    fields = []
    values = []
    for key, value in data.items():
        if key != 'id' and key != 'created_at':
            fields.append(f"{key} = ?")
            values.append(value if not isinstance(value, (dict, list)) else json.dumps(value))
    
    if not fields:
        return False
        
    values.append(client_id)
    query = f"UPDATE clients SET {', '.join(fields)} WHERE id = ?"
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query, values)
        rows_affected = cursor.rowcount
        
        if rows_affected == 0:
            # El cliente no existía en BD (probablemente un demo). Insertar con el ID dado.
            print(f"⚠️ Client {client_id} not in DB, inserting...")
            
            # Asegurar campos NOT NULL con valores por defecto
            defaults = {
                'name': data.get('name', 'Cliente'),
                'whatsapp_token': data.get('whatsapp_token', ''),
                'phone_number_id': data.get('phone_number_id', f'client_{client_id}'),
                'verify_token': data.get('verify_token', ''),
            }
            
            insert_cols = ['id']
            insert_vals = [client_id]
            
            # Primero agregar los defaults
            for key, val in defaults.items():
                if key not in [k for k in data.keys()]:
                    insert_cols.append(key)
                    insert_vals.append(val)
            
            # Luego agregar los datos del usuario
            for key, value in data.items():
                if key != 'id' and key != 'created_at':
                    insert_cols.append(key)
                    insert_vals.append(value if not isinstance(value, (dict, list)) else json.dumps(value))
            
            placeholders = ', '.join(['?'] * len(insert_cols))
            insert_query = f"INSERT INTO clients ({', '.join(insert_cols)}) VALUES ({placeholders})"
            cursor.execute(insert_query, insert_vals)

        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR UPDATE CLIENT: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_client(data):
    """Agrega un nuevo cliente."""
    columns = []
    placeholders = []
    values = []
    for key, value in data.items():
        columns.append(key)
        placeholders.append("?")
        values.append(value)
        
    query = f"INSERT INTO clients ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR ADD CLIENT: {e}")
        return False

def get_client_by_id(client_id):
    """Obtiene un cliente por su ID numérico, incluyendo clientes demo."""
    # Soporte para IDs de demo hardcodeados
    demo_ids = {
        9991: {
            "id": 9991, 
            "name": "🍕 Demo Restaurante V9", 
            "phone_number_id": "demo_restaurante", 
            "email": "demo@zotek.ia",
            "system_instruction": "Eres el asistente de una Pizzería Gourmet. Saluda con entusiasmo y ofrece las pizzas del día.",
            "menu_json": '{"text": "¡Bienvenido a *La Trattoria*! 👋 Soy tu asistente virtual. ¿Qué te gustaría hacer hoy?", "options": [{"title": "Ver Menú", "icon": "🍕", "response": "Nuestro menú incluye pizzas a la leña, pastas frescas y postres italianos."}, {"title": "Hacer Reserva", "icon": "📅", "response": "Indícanos la fecha y hora para verificar disponibilidad."}, {"title": "Horarios", "icon": "⏰", "response": "Estamos abiertos todos los días de 12:00 PM a 11:00 PM."}], "fallback_text": "Lo siento, no entendí eso. Aquí tienes las opciones principales de La Trattoria:"}'
        },
        9992: {
            "id": 9992, 
            "name": "🏥 Demo Clínica Dental", 
            "phone_number_id": "demo_clinica", 
            "email": "demo@zotek.ia",
            "system_instruction": "Eres el asistente de una Clínica Dental. Ayuda a los pacientes a conocer los servicios de ortodoncia y limpieza.",
            "menu_json": '{"text": "Bienvenido a la *Clínica San Juan*. 🏥 ¿En qué podemos ayudarte hoy?", "options": [{"title": "Agendar Cita", "icon": "📅", "response": "Por favor, dinos para qué especialidad buscas cita."}, {"title": "Especialidades", "icon": "👨‍⚕️", "response": "Contamos con Medicina General, Odontología y Pediatría."}, {"title": "Ubicación", "icon": "📍", "response": "Estamos en Av. Central #123. Haz clic aquí para ver en el mapa: https://maps.google.com"}], "fallback_text": "No comprendo tu solicitud. Selecciona una de estas opciones de la clínica:"}'
        },
        9993: {
            "id": 9993, 
            "name": "🛍️ Demo Tienda e-Commerce", 
            "phone_number_id": "demo_tienda", 
            "email": "demo@zotek.ia",
            "system_instruction": "Eres el asistente de una tienda de gadgets tecnológicos. Recomienda los mejores productos según las necesidades del cliente.",
            "menu_json": '{"text": "¡Hola! Bienvenido a *Moda Urbana*. 🛍️ ✨ ¿Cómo podemos ayudarte con tu estilo hoy?", "options": [{"title": "Ver Catálogo", "icon": "👕", "response": "Nuestra nueva colección de otoño ya está disponible."}, {"title": "Tallas", "icon": "📏", "response": "Manejamos tallas desde XS hasta XL en la mayoría de nuestras prendas."}, {"title": "Devoluciones", "icon": "🔄", "response": "Tienes 30 días para realizar cambios o devoluciones con tu ticket."}], "fallback_text": "Ups, no reconozco eso. Aquí tienes lo que puedo hacer por ti en Moda Urbana:"}'
        }
    }
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = cursor.fetchone()
        conn.close()
        
        if client:
            return dict(client)
        
        # Si no está en BD, buscar en demos
        if int(client_id) in demo_ids:
            return demo_ids[int(client_id)]
            
        return None
    except Exception as e:
        print(f"❌ ERROR get_client_by_id: {e}")
        return None

def delete_client_db_entry(client_id):
    """Elimina un cliente de la base de datos (usado para resetear demos)."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR delete_client: {e}")
        return False

def list_client_documents(client_id):
    """Lista los archivos de conocimiento de un cliente."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, source_file, updated_at FROM knowledge_base WHERE client_id = ?", (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ ERROR list_client_documents: {e}")
        return []

def get_client_knowledge(client_id):
    """Obtiene todo el conocimiento acumulado de un cliente."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM knowledge_base WHERE client_id = ?", (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return "\n".join([row[0] for row in rows])
    except Exception as e:
        print(f"❌ ERROR get_client_knowledge: {e}")
        return ""


# ============================================
# TRACKING DE MENSAJES Y MÉTRICAS
# ============================================

def track_message(client_id: int, direction: str = "outbound", phone_number: str = None):
    """
    Registra un mensaje para métricas de facturación.
    
    Args:
        client_id: ID del cliente
        direction: 'inbound' (recibido) o 'outbound' (enviado)
        phone_number: Número de teléfono (opcional, para logs)
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO message_logs (client_id, direction, phone_number, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (client_id, direction, phone_number))
        conn.commit()
        conn.close()
    except Exception as e:
        # No bloquear el flujo principal por errores de tracking
        print(f"⚠️ ERROR track_message: {e}")


def get_monthly_message_count(client_id: int) -> int:
    """
    Obtiene la cantidad de mensajes del mes actual para facturación.
    
    Args:
        client_id: ID del cliente
    
    Returns:
        Cantidad de mensajes en el mes actual
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM message_logs 
            WHERE client_id = ? 
            AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        """, (client_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"❌ ERROR get_monthly_message_count: {e}")
        return 0


def check_message_limit(client_id: int, plan: str = 'free') -> Tuple[bool, str]:
    """
    Verifica si el cliente excedió su límite de mensajes mensual.
    
    Args:
        client_id: ID del cliente
        plan: Plan del cliente (free, basic, pro, enterprise)
    
    Returns:
        Tuple (allowed: bool, message: str)
    """
    # Importar planes desde config si está disponible
    from .config import Config
    
    limits = Config.get_plan_limits(plan)
    monthly_limit = limits.get('monthly_messages', 100)
    
    # Ilimitado
    if monthly_limit == -1:
        return True, "Ilimitado"
    
    current_count = get_monthly_message_count(client_id)
    
    if current_count >= monthly_limit:
        return False, f"Límite de {monthly_limit} mensajes alcanzado. Mes: {current_count}/{monthly_limit}"
    
    remaining = monthly_limit - current_count
    return True, f"{remaining} mensajes restantes este mes"


def get_message_stats(client_id: int = None) -> Dict[str, Any]:
    """
    Obtiene estadísticas de mensajes.
    
    Args:
        client_id: ID del cliente (opcional, si None retorna globales)
    
    Returns:
        Diccionario con estadísticas
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if client_id:
            # Estadísticas por cliente
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN direction = 'inbound' THEN 1 ELSE 0 END) as inbound,
                    SUM(CASE WHEN direction = 'outbound' THEN 1 ELSE 0 END) as outbound,
                    MIN(created_at) as first_message,
                    MAX(created_at) as last_message
                FROM message_logs 
                WHERE client_id = ?
            """, (client_id,))
        else:
            # Estadísticas globales
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
        conn.close()
        
        if row:
            return {
                'total': row['total'] or 0,
                'inbound': row['inbound'] or 0,
                'outbound': row['outbound'] or 0,
                'unique_clients': row.get('unique_clients', 0),
                'first_message': row['first_message'],
                'last_message': row['last_message']
            }
        return {'total': 0, 'inbound': 0, 'outbound': 0, 'unique_clients': 0}
    except Exception as e:
        print(f"❌ ERROR get_message_stats: {e}")
        return {'total': 0, 'inbound': 0, 'outbound': 0}


# ============================================
# HISTORIAL DE CONVERSACIÓN
# ============================================

def add_to_conversation_history(phone_number: str, user_message: str, assistant_response: str):
    """
    Agrega un intercambio de mensajes al historial de conversación.
    
    Args:
        phone_number: Número de teléfono del usuario
        user_message: Mensaje del usuario
        assistant_response: Respuesta del asistente
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Insertar mensaje del usuario
        cursor.execute("""
            INSERT INTO conversation_history (phone_number, content, is_user, created_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
        """, (phone_number, user_message))
        
        # Insertar respuesta del asistente
        cursor.execute("""
            INSERT INTO conversation_history (phone_number, content, is_user, created_at)
            VALUES (?, ?, 0, CURRENT_TIMESTAMP)
        """, (phone_number, assistant_response))
        
        conn.commit()
        conn.close()
    except Exception as e:
        # No bloquear el flujo principal por errores de historial
        print(f"⚠️ ERROR add_to_conversation_history: {e}")


def get_conversation_history(phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene el historial reciente de conversación para un usuario.
    
    Args:
        phone_number: Número de teléfono del usuario
        limit: Cantidad máxima de mensajes a retornar
    
    Returns:
        Lista de mensajes con estructura: {content, is_user, created_at}
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content, is_user, created_at 
            FROM conversation_history 
            WHERE phone_number = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (phone_number, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Invertir para que el más antiguo vaya primero
        return [dict(row) for row in reversed(rows)]
    except Exception as e:
        print(f"❌ ERROR get_conversation_history: {e}")
        return []


def clear_conversation_history(phone_number: str = None, older_than_days: int = 30):
    """
    Limpia el historial de conversación.
    
    Args:
        phone_number: Número específico (opcional, si None limpia todo)
        older_than_days: Días de antigüedad para limpiar (default 30)
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        if phone_number:
            cursor.execute("""
                DELETE FROM conversation_history 
                WHERE phone_number = ?
            """, (phone_number,))
        else:
            # Limpieza automática de conversaciones antiguas
            cursor.execute("""
                DELETE FROM conversation_history 
                WHERE created_at < datetime('now', ?)
            """, (f'-{older_than_days} days',))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ ERROR clear_conversation_history: {e}")


if __name__ == "__main__":
    init_db()
