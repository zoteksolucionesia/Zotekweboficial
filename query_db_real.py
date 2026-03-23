import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from functions.src.database import get_db

db = get_db()
print("Fetching recent chat messages using Firebase DB context from functions...")
clients = db.collection('clients').stream()
all_messages = []

for client in clients:
    chats = db.collection('clients').document(client.id).collection('chats').stream()
    for chat in chats:
        msgs = db.collection('clients').document(client.id).collection('chats').document(chat.id).collection('messages').limit(20).stream()
        for msg in msgs:
            data = msg.to_dict()
            data['client_id'] = client.id
            data['user_phone'] = chat.id
            all_messages.append(data)

# Extract timestamp string correctly for sorting
all_messages.sort(key=lambda x: str(x.get('timestamp', '')), reverse=True)

print(f"Total messages found: {len(all_messages)}")
for data in all_messages[:30]:
    ts = data.get('timestamp')
    txt = data.get('text', '').replace('\n', ' ')
    direction = data.get('direction', 'unknown')
    c_id = data.get('client_id')
    print(f"[{ts}] {c_id} ({direction}): {txt[:100]}")
