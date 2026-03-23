from src import database
clients = database.list_clients()
with open("clients_dump.txt", "w", encoding="utf-8") as f:
    for c in clients:
        f.write(f"ID: {c['id']} | Name: {c['name']} | PhoneID: {c['phone_number_id']}\n")
