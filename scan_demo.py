import firebase_admin
from firebase_admin import credentials, firestore

def scan_demo_project():
    # Attempting to use the same service account for the demo project
    # This may fail if the service account doesn't have cross-project permissions
    try:
        cred = credentials.Certificate('service-account-key.json')
        # We need a different app name if we already initialized one
        app = firebase_admin.initialize_app(cred, {'projectId': 'zotek-soluciones-ia-demo'}, name='demo_app')
        db = firestore.client(app=app)
        
        target_phone_id = "980996958435648"
        print(f"Scanning 'zotek-soluciones-ia-demo' for phone_number_id: {target_phone_id}...")
        
        clients_ref = db.collection('clients')
        docs = clients_ref.where('phone_number_id', '==', target_phone_id).stream()
        
        found = False
        for doc in docs:
            found = True
            data = doc.to_dict()
            print(f"\n--- Document ID: {doc.id} ---")
            print(f"Name: {data.get('name')}")
            print(f"System Instruction: {data.get('system_instruction')}")
            
        if not found:
            print("No documents found in demo project with that phone_number_id.")
            
    except Exception as e:
        print(f"Error accessing demo project: {e}")

if __name__ == "__main__":
    scan_demo_project()
