import sqlite3
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
            "stripe_api_key": "TEXT" 
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
    """Retorna una lista de todos los clientes."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ ERROR list_clients: {e}")
        return []

def update_client(client_id, data):
    """Actualiza los datos de un cliente."""
    fields = []
    values = []
    for key, value in data.items():
        if key != 'id' and key != 'created_at':
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        return False
        
    values.append(client_id)
    query = f"UPDATE clients SET {', '.join(fields)} WHERE id = ?"
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR UPDATE CLIENT: {e}")
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
    """Obtiene un cliente por su ID numérico."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = cursor.fetchone()
        conn.close()
        return dict(client) if client else None
    except Exception as e:
        print(f"❌ ERROR get_client_by_id: {e}")
        return None

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
