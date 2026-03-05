import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (ZotekSolucionesIA)
parent_dir = os.path.dirname(script_dir)
# Add functions/src to python path
sys.path.insert(0, os.path.join(parent_dir, 'functions'))

import src.database as database

clients = database.list_clients()
print("Clientes encontrados:", len(clients))
for c in clients:
    print(f"Nombre: {c.get('name')}")
    print(f"Número guardado (whatsapp_number): {c.get('whatsapp_number')}")
    print(f"ID Meta (phone_number_id): {c.get('phone_number_id')}")
    print("---")
