import firebase_admin
from firebase_admin import credentials, firestore
import os

# Inicializar Firebase Admin si no está inicializado
try:
    firebase_admin.initialize_app()
except ValueError:
    # Ya estaba inicializado
    pass

_db = None

def get_db():
    global _db
    if _db is None:
        _db = firestore.client()
    return _db

# Usage: Whenever you need db, call get_db()

def init_db():
    """
    En Firestore no es estrictamente necesario inicializar el esquema,
    pero podemos usar esto para asegurar que existan los índices o datos base.
    """
    print("ℹ️ Firestore no requiere init_db tradicional. Esquema bajo demanda.")
    pass

def get_client_by_phone_id(phone_number_id):
    """Obtiene los datos de un cliente por su Phone Number ID o número de WhatsApp."""
    try:
        db = get_db()
        clients_ref = db.collection('clients')
        
        # 1. Intentar por phone_number_id (ID numérico de Meta)
        query = clients_ref.where('phone_number_id', '==', str(phone_number_id)).stream()
        for doc in query:
            client_data = doc.to_dict()
            client_data['id'] = doc.id
            return client_data
            
        # 2. Intentar por whatsapp_number (por si Meta envía el número en el webhook)
        query = clients_ref.where('whatsapp_number', '==', str(phone_number_id)).stream()
        for doc in query:
            client_data = doc.to_dict()
            client_data['id'] = doc.id
            return client_data
            
        return None
    except Exception as e:
        print(f"❌ ERROR get_client_by_phone_id: {e}")
        return None

def get_client_by_email(email):
    """Obtiene un cliente por su email de login (SaaS Phase 3)."""
    if not email: return None
    clients_ref = get_db().collection('clients')
    query = clients_ref.where('email', '==', str(email).lower().strip()).stream()
    
    for doc in query:
        client_data = doc.to_dict()
        client_data['id'] = doc.id
        return client_data
    return None

def get_client_knowledge(client_id):
    """Retorna el contenido de la base de conocimientos de un cliente."""
    # Buscamos en la subcolección 'knowledge' del cliente
    knowledge_ref = get_db().collection('clients').document(str(client_id)).collection('knowledge').stream()
    
    entries = [doc.to_dict().get('content', '') for doc in knowledge_ref]
    if not entries:
        return "Sin base de conocimiento configurada."
    return "\n\n".join(entries)

def add_knowledge_entry(client_id, content, source_file=None):
    """Agrega una nueva entrada a la base de conocimientos de un cliente."""
    client_ref = get_db().collection('clients').document(str(client_id))
    knowledge_ref = client_ref.collection('knowledge').document() # ID automático
    
    knowledge_ref.set({
        'content': content,
        'source_file': source_file,
        'updated_at': firestore.SERVER_TIMESTAMP
    })
    return True

def list_clients():
    """Retorna una lista de todos los clientes."""
    clients_ref = get_db().collection('clients').stream()
    clients = []
    for doc in clients_ref:
        client_data = doc.to_dict()
        client_data['id'] = doc.id
        clients.append(client_data)
    return clients

def update_client(client_id, data):
    """Actualiza los datos de un cliente."""
    try:
        # Limpiar el ID de los datos para no guardarlo como campo si viene incluido
        if 'id' in data:
            del data['id']
            
        get_db().collection('clients').document(str(client_id)).update(data)
        return True
    except Exception as e:
        print(f"❌ ERROR UPDATE CLIENT (Firestore): {e}")
        return False

def add_client(data):
    """Agrega un nuevo cliente."""
    try:
        # Firestore puede generar el ID solo
        doc_ref = get_db().collection('clients').document()
        doc_data = data.copy()
        doc_data['created_at'] = firestore.SERVER_TIMESTAMP
        doc_ref.set(doc_data)
        return True
    except Exception as e:
        print(f"❌ ERROR ADD CLIENT (Firestore): {e}")
        return False

def get_client_by_id(client_id):
    """Obtiene un cliente por su ID (document string en Firestore)."""
    doc_ref = get_db().collection('clients').document(str(client_id)).get()
    if doc_ref.exists:
        client_data = doc_ref.to_dict()
        client_data['id'] = doc_ref.id
        return client_data
    return None

def list_client_documents(client_id):
    """Lista los archivos de conocimiento de un cliente."""
    knowledge_ref = get_db().collection('clients').document(str(client_id)).collection('knowledge').stream()
    
    docs = []
    for doc in knowledge_ref:
        doc_data = doc.to_dict()
        # Convertir timestamp a string si es necesario para el frontend
        updated_at = doc_data.get('updated_at')
        if updated_at:
            doc_data['updated_at'] = str(updated_at)
        
        docs.append({
            'id': doc.id,
            'source_file': doc_data.get('source_file') or 'Documento sin nombre',
            'updated_at': doc_data.get('updated_at', '')
        })
    return docs


def delete_knowledge_entry(client_id, doc_id):
    """Elimina una entrada de la base de conocimientos de un cliente."""
    try:
        doc_ref = get_db().collection('clients').document(str(client_id)).collection('knowledge').document(str(doc_id))
        doc_ref.delete()
        return True
    except Exception as e:
        print(f"❌ ERROR DELETE KNOWLEDGE (Firestore): {e}")
        return False

def save_chat_message(client_id, user_number, message, response):
    """Guarda un mensaje de chat en Firestore para el historial."""
    try:
        chat_ref = get_db().collection('clients').document(str(client_id)).collection('chats').document()
        chat_ref.set({
            'user_number': user_number,
            'message': message,
            'response': response,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        print(f"❌ ERROR SAVE CHAT (Firestore): {e}")
        return False

def get_client_chats(client_id, limit=50):
    """Obtiene los últimos mensajes de chat de un cliente."""
    try:
        chats_ref = get_db().collection('clients').document(str(client_id)).collection('chats')
        query = chats_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        chats = []
        for doc in query:
            chat_data = doc.to_dict()
            chat_data['id'] = doc.id
            # Convertir timestamp a ISO string para JSON
            ts = chat_data.get('timestamp')
            if ts:
                chat_data['timestamp'] = ts.isoformat()
            chats.append(chat_data)
        return chats
    except Exception as e:
        print(f"❌ ERROR GET CHATS (Firestore): {e}")
        return []

if __name__ == "__main__":
    # Prueba rápida
    pass
