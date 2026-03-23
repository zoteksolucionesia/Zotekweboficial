import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("="*70)
print("MENUS DEMO GUARDADOS EN POSTGRESQL")
print("="*70)

cur.execute("""
    SELECT phone_number_id, 
           menu_json->>'text' as welcome,
           jsonb_array_length(menu_json->'options') as opt_count
    FROM clients 
    WHERE phone_number_id LIKE 'demo%'
    ORDER BY id
""")

for row in cur.fetchall():
    print(f"\n{row[0]}:")
    welcome = row[0].encode('ascii', 'replace').decode('ascii')
    print(f"  Welcome: {welcome[:50]}...")
    print(f"  Options: {row[2]} botones")
    
    # Ver cada opcion
    cur2 = conn.cursor()
    cur2.execute("""
        SELECT jsonb_array_elements(menu_json->'options')->>'title'
        FROM clients
        WHERE phone_number_id = %s
    """, (row[0],))
    
    for opt in cur2.fetchall():
        title = opt[0].encode('ascii', 'replace').decode('ascii')
        print(f"    - {title}")
    
    cur2.close()

print("\n" + "="*70)

cur.close()
conn.close()
