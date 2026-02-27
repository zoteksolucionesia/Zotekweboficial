import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# Initialize Firebase Admin with Service Account Key if available
cred_path = "service-account-key.json"
if os.path.exists(cred_path):
    print(f"Using service account key from {cred_path}")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'projectId': 'zotek-ia'
    })
else:
    print("Service account key not found, attempting Application Default Credentials...")
    try:
        firebase_admin.initialize_app(options={'projectId': 'zotek-ia'})
    except Exception as e:
        print(f"Failed to initialize: {e}")
        exit(1)

db = firestore.client()
print("Firebase Admin initialized successfully.")

def migrate_data():
    try:
        with open("migration_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("migration_data.json not found.")
        return

    # 1. Migrate Clients
    clients = data.get("clients", [])
    current_client_id = None
    
    print(f"Migrating {len(clients)} clients...")
    for client in clients:
        # Use phone_number_id as the document ID for consistency in Firestore
        phone_id = str(client.get("phone_number_id"))
        if not phone_id:
            print("Skipping client without phone_number_id")
            continue
            
        current_client_id = phone_id
        db.collection("clients").document(phone_id).set(client)
        print(f"Migrated client: {client.get('name')} (ID: {phone_id})")
    
    if not current_client_id:
        print("No clients migrated, skipping subcollections.")
        return

    # 2. Migrate Knowledge Base (As subcollection of the client)
    kb = data.get("knowledge", []) # JSON field name is 'knowledge' based on previous view_file
    print(f"Migrating {len(kb)} knowledge base entries...")
    for entry in kb:
        # Nest under the first client for this migration (assuming single client context)
        db.collection("clients").document(current_client_id).collection("knowledge").add({
            "content": entry.get("content"),
            "source_file": entry.get("source_file"),
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
    # 3. Migrate Appointments (citas) (As subcollection or top-level depending on backend)
    # Backend database.py mentions get_db().collection('citas'), so top-level is fine for appointments.
    citas = data.get("appointments", []) # JSON field name 'appointments'
    print(f"Migrating {len(citas)} appointments...")
    for cita in citas:
        db.collection("citas").add(cita)

    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate_data()
