import firebase_admin
from firebase_admin import credentials, firestore

def list_all_clients():
    cred = credentials.Certificate('service-account-key.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    print("Listing ALL clients in 'clients' collection...")
    clients_ref = db.collection('clients')
    docs = clients_ref.stream()
    
    for doc in docs:
        data = doc.to_dict()
        print(f"ID: {doc.id} | Name: {data.get('name')} | PhoneID: {data.get('phone_number_id')} | Email: {data.get('email')}")

if __name__ == "__main__":
    list_all_clients()
