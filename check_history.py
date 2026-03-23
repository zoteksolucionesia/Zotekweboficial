import json
from src import database

phone = "523123775877"
history = database.get_conversation_history(phone, limit=20)

print(f"--- History for {phone} ---")
for h in history:
    role = "USER" if h['is_user'] else "BOT"
    print(f"[{role}]: {h['content']}")
