import firebase_admin
from firebase_admin import credentials, firestore

def fetch_recent_logs():
    try:
        cred = credentials.Certificate('service-account-key.json')
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
            
        db = firestore.client()
        print("Fetching recent chat messages by iterating clients...")
        
        clients = db.collection('clients').stream()
        all_messages = []
        
        for client in clients:
            chats = db.collection('clients').document(client.id).collection('chats').stream()
            for chat in chats:
                # Get the latest messages for this chat
                msgs = db.collection('clients').document(client.id).collection('chats').document(chat.id).collection('messages').limit(20).stream()
                for msg in msgs:
                    data = msg.to_dict()
                    data['client_id'] = client.id
                    data['user_phone'] = chat.id
                    all_messages.append(data)
                    
        # Sort by timestamp
        all_messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        print(f"Total messages found: {len(all_messages)}")
        for data in all_messages[:30]:
            ts = data.get('timestamp')
            txt = data.get('text', '')
            direction = data.get('direction', 'unknown')
            c_id = data.get('client_id')
            print(f"[{ts}] {c_id} ({direction}): {txt}")
            
    except Exception as e:
        print(f"Error querying Firestore: {e}")

if __name__ == "__main__":
    fetch_recent_logs()
