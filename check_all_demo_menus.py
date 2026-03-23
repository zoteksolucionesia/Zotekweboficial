import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT phone_number_id, name, menu_json FROM clients WHERE phone_number_id LIKE 'demo%' ORDER BY id")
rows = cur.fetchall()

for row in rows:
    print("=" * 60)
    print(f"Phone ID: {row[0]}")
    name_ascii = row[1].encode('ascii', 'replace').decode('ascii')
    print(f"Name: {name_ascii}")
    
    if row[2]:
        menu = row[2] if isinstance(row[2], dict) else json.loads(row[2])
        text = menu.get('text', 'N/A')
        text_ascii = text.encode('ascii', 'replace').decode('ascii')
        print(f"Welcome: {text_ascii[:80]}...")
        
        options = menu.get('options', [])
        print(f"Options count: {len(options)}")
        if options:
            print("  Options:")
            for opt in options:
                title = opt.get('title', 'N/A')
                title_ascii = title.encode('ascii', 'replace').decode('ascii')
                icon = opt.get('icon', '').encode('ascii', 'replace').decode('ascii')
                print(f"    - {title_ascii} {icon}")
    else:
        print("  NO MENU CONFIGURED")
    print("")

cur.close()
conn.close()
