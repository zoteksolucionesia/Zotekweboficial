import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2, json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT menu_json FROM clients WHERE phone_number_id = 'demo_restaurant'")
row = cur.fetchone()
menu = row[0] if isinstance(row[0], dict) else json.loads(row[0])

print("OPCIONES EN EL MENU:")
for i, opt in enumerate(menu.get('options', []), 1):
    title = opt.get('title', 'N/A')
    title_ascii = title.encode('ascii', 'replace').decode('ascii')
    print(f"  {i}. Title: '{title_ascii}'")

cur.close()
conn.close()
