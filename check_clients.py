import json
from src import database

clients = database.list_clients()

print("--- CLIEBT LIST ---")
for c in clients:
    print(f"ID: {c['id']} | Name: {c['name']} | PhoneID: {c['phone_number_id']}")
