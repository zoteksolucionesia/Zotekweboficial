import sqlite3
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Configuración de rutas
DB_NAME = "functions/data/consultorio.db"

def migrate():
    if not os.path.exists(DB_NAME):
        print(f"❌ No se encontró la base de datos en {DB_NAME}")
        return

    # Inicializar Firebase Admin (usará las credenciales por defecto si se corre localmente con firebase login)
    print("🚀 Iniciando migración de SQLite a Firestore...")
    try:
        firebase_admin.initialize_app(options={'projectId': 'zotek-ia'})
    except Exception as e:
        print(f"ℹ️ Firebase ya inicializado o error: {e}")
    
    db = firestore.client()
    
    # Conectar a SQLite
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Migrar Clientes
    print("📋 Migrando clientes...")
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    for client in clients:
        client_dict = dict(client)
        client_id_sqlite = client_dict.pop('id')
        
        # Usamos el ID de SQLite como documento o generamos uno nuevo
        # Para Firestore es mejor usar strings manejables
        doc_ref = db.collection('clients').document(str(client_id_sqlite))
        doc_ref.set(client_dict)
        print(f"✅ Cliente migrado: {client_dict['name']}")
        
        # 2. Migrar Conocimiento (Base de conocimiento) por cliente
        print(f"📖 Migrando conocimiento para {client_dict['name']}...")
        cursor.execute("SELECT * FROM knowledge_base WHERE client_id = ?", (client_id_sqlite,))
        knowledge_entries = cursor.fetchall()
        for entry in knowledge_entries:
            entry_dict = dict(entry)
            entry_id = entry_dict.pop('id')
            entry_dict.pop('client_id') # Ya está implícito en la subcolección
            
            # Guardamos en subcolección para mejor organización
            doc_ref.collection('knowledge').document(str(entry_id)).set(entry_dict)
        
    # 3. Migrar Citas (Opcional si las usabas)
    print("📅 Migrando citas...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='citas'")
    if cursor.fetchone():
        cursor.execute("SELECT * FROM citas")
        citas = cursor.fetchall()
        for cita in citas:
            cita_dict = dict(cita)
            cita_id = cita_dict.pop('id')
            client_id = cita_dict.pop('client_id')
            
            # Guardar en una colección global o vinculada al cliente
            db.collection('clients').document(str(client_id)).collection('appointments').document(str(cita_id)).set(cita_dict)

    conn.close()
    print("🎉 Migración completada exitosamente.")

if __name__ == "__main__":
    migrate()
