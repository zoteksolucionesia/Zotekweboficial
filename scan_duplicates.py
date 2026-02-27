import firebase_admin
from firebase_admin import credentials, firestore
import json

def scan_clients():
    cred = credentials.Certificate('service-account-key.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    target_phone_id = "980996958435648"
    print(f"Scanning for phone_number_id: {target_phone_id}...")
    
    clients_ref = db.collection('clients')
    docs = clients_ref.where('phone_number_id', '==', target_phone_id).stream()
    
    found = False
    for doc in docs:
        found = True
        data = doc.to_dict()
        print(f"\n--- Document ID: {doc.id} ---")
        print(f"Name: {data.get('name')}")
        print(f"Email: {data.get('email')}")
        print(f"System Instruction: {data.get('system_instruction')}")
        
        # Check menu subcollection
        menu_ref = clients_ref.document(doc.id).collection('config').document('menu')
        menu_doc = menu_ref.get()
        if menu_doc.exists:
            print("Menu Config Found:")
            print(json.dumps(menu_doc.to_dict(), indent=2))
        else:
            print("No Menu Config subcollection found.")
            
    if not found:
        print("No documents found with that phone_number_id.")

if __name__ == "__main__":
    scan_clients()
