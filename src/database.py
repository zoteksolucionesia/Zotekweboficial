import sqlite3
import json
import os

# Pointing to the new data directory location
ORIGINAL_DB = os.path.join(os.path.dirname(__file__), "..", "data", "consultorio.db")
DB_NAME = ORIGINAL_DB

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

if __name__ == "__main__":
    init_db()
