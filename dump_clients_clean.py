from src import database
import re

def clean_name(name):
    return re.sub(r'[^\x00-\x7F]+', '', name)

clients = database.list_clients()
with open("clients_dump_clean.txt", "w") as f:
    for c in clients:
        name = clean_name(c['name'])
        f.write(f"ID: {c['id']} | Name: {name} | PhoneID: {c['phone_number_id']}\n")
