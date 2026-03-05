import firebase_admin
from firebase_admin import credentials, firestore

def check_client_menu(client_id):
    cred = credentials.Certificate('service-account-key.json')
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
        
    db = firestore.client()
    
    doc_ref = db.collection('clients').document(client_id).collection('config').document('menu')
    doc = doc_ref.get()
    
    if doc.exists:
        print(f"Menu data for {client_id}:")
        import json
        print(json.dumps(doc.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ Menu document NOT found for {client_id}")

if __name__ == "__main__":
    check_client_menu('demo_clinica')
    check_client_menu('demo_restaurante')
    check_client_menu('demo_tienda')
