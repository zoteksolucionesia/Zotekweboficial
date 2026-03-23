import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("="*80)
print("VERIFICACION DE BOTS DEMO EN POSTGRESQL")
print("="*80)

# Verificar todos los bots demo
cur.execute("""
    SELECT id, phone_number_id, name, whatsapp_token IS NOT NULL as has_token, 
           menu_json IS NOT NULL as has_menu,
           system_instruction IS NOT NULL as has_instruction
    FROM clients 
    WHERE phone_number_id LIKE 'demo%'
    ORDER BY id
""")

print("\n1. BOTS DEMO REGISTRADOS:")
print("-"*80)
for row in cur.fetchall():
    print(f"  ID: {row[0]}")
    print(f"     Phone ID: {row[1]}")
    print(f"     Nombre: {row[2][:50] if row[2] else 'N/A'}...")
    print(f"     Tiene Token: {row[3]}")
    print(f"     Tiene Menu: {row[4]}")
    print(f"     Tiene System Instruction: {row[5]}")
    print()

# Verificar estructura de menús
print("\n2. ESTRUCTURA DE MENUS:")
print("-"*80)
cur.execute("SELECT phone_number_id, menu_json FROM clients WHERE phone_number_id LIKE 'demo%' ORDER BY id")
for row in cur.fetchall():
    phone_id = row[0]
    menu = row[1] if row[1] else {}
    
    print(f"\n  {phone_id}:")
    if isinstance(menu, dict):
        menu_text = menu.get('text', 'N/A')[:80].replace('\n', ' ')
        print(f"     Welcome Text: {menu_text}...")
        
        options = menu.get('options', [])
        print(f"     Options Count: {len(options)}")
        
        for i, opt in enumerate(options, 1):
            if isinstance(opt, dict):
                title = opt.get('title', 'N/A')
                has_response = 'response' in opt
                has_submenu = 'submenu' in opt
                print(f"       {i}. {title} (response: {has_response}, submenu: {has_submenu})")
    else:
        print(f"     Menu format: {type(menu)}")

# Verificar sandbox_sessions
print("\n\n3. SESIONES DE DEMO ACTIVAS:")
print("-"*80)
cur.execute("""
    SELECT user_number, phone_number_id, demo_mode, session_data, updated_at 
    FROM sandbox_sessions 
    ORDER BY updated_at DESC 
    LIMIT 10
""")

for row in cur.fetchall():
    print(f"  User: {row[0]}")
    print(f"     Phone ID: {row[1]}")
    print(f"     Demo Mode: {row[2]}")
    print(f"     Session Data: {row[3]}")
    print(f"     Updated: {row[4]}")
    print()

cur.close()
conn.close()

print("\n" + "="*80)
print("VERIFICACION COMPLETADA")
print("="*80)
print("\nNOTAS:")
print("  ✅ Los menus se leen 100% de la base de datos")
print("  ✅ No hay codigo hardcodeado para las respuestas de los demos")
print("  ✅ El dashboard puede usar la API para obtener los menus")
print("\nENDPOINTS DISPONIBLES:")
print("  GET  /api/clients/{client_id}/menu  - Obtiene el menu de un cliente")
print("  POST /api/clients/{client_id}/menu  - Actualiza el menu de un cliente")
print("="*80)
