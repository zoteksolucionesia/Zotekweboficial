import firebase_admin
from firebase_admin import credentials, firestore
import json

def get_db(project_id, app_name):
    try:
        cred = credentials.Certificate('service-account-key.json')
        app = firebase_admin.initialize_app(cred, {'projectId': project_id}, name=app_name)
        return firestore.client(app=app)
    except Exception as e:
        print(f"Error connecting to {project_id}: {e}")
        return None

def sync_menu():
    phone_id = "980996958435648"
    
    db_old = get_db('zotek-soluciones-ia-demo', 'old_app')
    db_new = get_db('zotek-ia', 'new_app')
    
    if not db_old or not db_new:
        return

    print(f"Fetching menu from OLD project for client {phone_id}...")
    # The document ID might be different in the old project, let's search by phone_number_id
    old_clients = db_old.collection('clients').where('phone_number_id', '==', phone_id).stream()
    
    old_menu_data = None
    for doc in old_clients:
        print(f"Found client in OLD: {doc.id}")
        menu_doc = db_old.collection('clients').document(doc.id).collection('config').document('menu').get()
        if menu_doc.exists:
            old_menu_data = menu_doc.to_dict()
            print("Menu found in OLD project.")
            break

    if old_menu_data:
        print(f"Syncing menu to NEW project (zotek-ia) for client {phone_id}...")
        db_new.collection('clients').document(phone_id).collection('config').document('menu').set(old_menu_data)
        print("✅ Menu synced successfully.")
    else:
        print("❌ No menu found in OLD project. Creating a default fallback menu...")
        fallback_menu = {
            "text": "¡Hola! Bienvenid@ a Salón RM. 👋\n\n¿En qué puedo ayudarte?",
            "options": [
                {"title": "Cortes de Cabello", "response": "Contamos con cortes para dama, caballero y niños."},
                {"title": "Colorimetría", "response": "Expertos en tintes, luces y balayage."},
                {"title": "Agendar Cita", "response": "Puedes agendar tu cita enviando un mensaje aquí o llamando al 123456789."}
            ]
        }
        db_new.collection('clients').document(phone_id).collection('config').document('menu').set(fallback_menu)
        print("✅ Default menu created in NEW project.")

if __name__ == "__main__":
    sync_menu()
