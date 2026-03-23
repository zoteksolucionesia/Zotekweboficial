import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("="*70)
print("VERIFICANDO MENUS DE DEMOS")
print("="*70)

cur.execute("""
    SELECT phone_number_id, name, 
           menu_json->>'text' as menu_text,
           jsonb_array_length(menu_json->'options') as num_options
    FROM clients 
    WHERE phone_number_id LIKE 'demo%'
    ORDER BY id
""")

for row in cur.fetchall():
    print(f"\n{row[0]}:")
    print(f"  Nombre: {row[1][:50] if row[1] else 'N/A'}...")
    
    # Verificar menu_text
    if row[2]:
        menu_text = row[2][:80].replace('\n', ' ')
        print(f"  Menu Text: {menu_text}...")
    else:
        print(f"  Menu Text: NULL")
    
    print(f"  Opciones: {row[3]}")
    
    # Verificar opciones individuales
    cur2 = conn.cursor()
    cur2.execute("""
        SELECT jsonb_array_elements(menu_json->'options')->>'title'
        FROM clients
        WHERE phone_number_id = %s
    """, (row[0],))
    
    opts = cur2.fetchall()
    if opts:
        print(f"  Botones:")
        for opt in opts:
            print(f"    - {opt[0]}")
    cur2.close()

cur.close()
conn.close()

print("\n" + "="*70)
