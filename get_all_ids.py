import firebase_admin
from firebase_admin import credentials, firestore

def list_clients():
    if not firebase_admin._apps:
        cred = credentials.Certificate('service-account-key.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    docs = db.collection('clients').stream()
    for doc in docs:
        data = doc.to_dict()
        print(f"ID: {doc.id} | Name: {data.get('name')}")

if __name__ == "__main__":
    list_clients()
