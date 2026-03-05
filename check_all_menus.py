import firebase_admin
from firebase_admin import credentials, firestore

def check_menus():
    if not firebase_admin._apps:
        cred = credentials.Certificate('service-account-key.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    ids = ['demo_clinica', 'demo_restaurante', 'demo_tienda', '980996958435648']
    for client_id in ids:
        doc = db.collection('clients').document(client_id).collection('config').document('menu').get()
        print(f"Client {client_id}: Menu Exists = {doc.exists}")
        if doc.exists:
            print(f"  Data keys: {list(doc.to_dict().keys())}")

if __name__ == "__main__":
    check_menus()
