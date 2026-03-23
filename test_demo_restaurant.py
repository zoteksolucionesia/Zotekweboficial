#!/usr/bin/env python3
"""
Test para verificar si el demo restaurante está configurado correctamente
"""

import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("Verificando demo_restaurant...")
cur.execute("""
    SELECT phone_number_id, name, whatsapp_token IS NOT NULL as has_token, menu_json IS NOT NULL as has_menu
    FROM clients 
    WHERE phone_number_id = 'demo_restaurant'
""")

row = cur.fetchone()
if row:
    print(f"  phone_number_id: {row[0]}")
    print(f"  name: {row[1][:50] if row[1] else 'N/A'}")
    print(f"  has_token: {row[2]}")
    print(f"  has_menu: {row[3]}")
    
    # Obtener menu_json completo
    cur.execute("SELECT menu_json FROM clients WHERE phone_number_id = 'demo_restaurant'")
    menu_row = cur.fetchone()
    if menu_row and menu_row[0]:
        menu = menu_row[0] if isinstance(menu_row[0], dict) else json.loads(menu_row[0])
        print(f"\n  Menu text (primeros 100 chars):")
        menu_text = menu.get('text', 'N/A')
        print(f"    {menu_text[:100]}...")
        
        print(f"\n  Opciones:")
        for i, opt in enumerate(menu.get('options', []), 1):
            title = opt.get('title', 'N/A') if isinstance(opt, dict) else str(opt)
            print(f"    {i}. {title}")
else:
    print("  NO ENCONTRADO")

cur.close()
conn.close()
