import sqlite3
import json
import os

db_path = 'functions/data/consultorio.db'

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get clients
cursor.execute("SELECT * FROM clients")
clients = [dict(row) for row in cursor.fetchall()]

# Get knowledge
cursor.execute("SELECT * FROM knowledge_base")
knowledge = [dict(row) for row in cursor.fetchall()]

# Get quotes/appointments if any
cursor.execute("SELECT * FROM citas")
citas = [dict(row) for row in cursor.fetchall()]

data = {
    "clients": clients,
    "knowledge": knowledge,
    "appointments": citas
}

with open('migration_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("Data exported to migration_data.json")
conn.close()
