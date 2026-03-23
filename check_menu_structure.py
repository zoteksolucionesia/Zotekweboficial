import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT phone_number_id, menu_json FROM clients WHERE phone_number_id = 'demo_restaurant'")
row = cur.fetchone()
if row and row[1]:
    menu = row[1] if isinstance(row[1], dict) else json.loads(row[1])
    print("CAMPOS del menu_json:")
    print(f"  - text: {type(menu.get('text')).__name__}")
    print(f"  - options: {type(menu.get('options')).__name__} ({len(menu.get('options', []))} items)")
    if menu.get('options'):
        print(f"  - options[0]: {type(menu['options'][0]).__name__}")
        print(f"    Keys: {menu['options'][0].keys() if isinstance(menu['options'][0], dict) else 'N/A'}")
    print(f"  - fallback_text: {type(menu.get('fallback_text')).__name__ if menu.get('fallback_text') else 'None'}")
else:
    print("No hay menu_json")

cur.close()
conn.close()
