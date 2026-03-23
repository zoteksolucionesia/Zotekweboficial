import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT phone_number_id, name, menu_json FROM clients WHERE phone_number_id = 'demo_retail'")
row = cur.fetchone()
if row:
    print(f"Phone ID: {row[0]}")
    name_ascii = row[1].encode('ascii', 'replace').decode('ascii')
    print(f"Name: {name_ascii}")
    print(f"\nMenu JSON:")
    if row[2]:
        menu = row[2] if isinstance(row[2], dict) else json.loads(row[2])
        text_ascii = menu.get('text', 'N/A').encode('ascii', 'replace').decode('ascii')
        print(f"  Text: {text_ascii}")
        print(f"\n  Options:")
        for opt in menu.get('options', []):
            title = opt.get('title', 'N/A').encode('ascii', 'replace').decode('ascii')
            icon = opt.get('icon', '')
            print(f"    - {title} {icon}")
    else:
        print("  No menu configured")
else:
    print("demo_retail no encontrado")
cur.close()
conn.close()
