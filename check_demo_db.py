import sys, os
sys.path.insert(0, os.path.abspath('functions'))
from src.database import get_db

db = get_db()
print("Sessions in DB:")
sessions = list(db.collection('sandbox_sessions').limit(5).stream())
for s in sessions:
    print(s.id, s.to_dict())

print("\nDemo Clients in clients collection:")
for d_id in ["demo_restaurante", "demo_clinica", "demo_tienda"]:
    c = db.collection('clients').document(d_id).get()
    print(d_id, "exists?", c.exists)
    if c.exists:
        menu = db.collection('clients').document(d_id).collection('config').document('menu').get()
        print(f"  Menu config exists: {menu.exists}")
