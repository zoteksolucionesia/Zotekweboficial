import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import json

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("="*70)
print("MENU ACTUAL DE ZOTEK")
print("="*70)

cur.execute("""
    SELECT id, name, menu_json 
    FROM clients 
    WHERE phone_number_id = '980996958435648'
""")

row = cur.fetchone()
if row:
    print(f"\nID: {row[0]}")
    print(f"Nombre: {row[1]}")
    
    if row[2]:
        menu = row[2] if isinstance(row[2], dict) else json.loads(row[2])
        print(f"\nTexto de bienvenida:")
        print(f"  {menu.get('text', 'N/A')[:200]}...")
        
        print(f"\nOpciones del menú:")
        for i, opt in enumerate(menu.get('options', []), 1):
            if isinstance(opt, dict):
                title = opt.get('title', 'N/A')
                print(f"  {i}. {title}")
                
                # Verificar si tiene respuesta o submenú
                if opt.get('response'):
                    print(f"     → Tiene respuesta directa")
                if opt.get('submenu'):
                    print(f"     → Tiene submenú:")
                    submenu = opt['submenu']
                    for j, subopt in enumerate(submenu.get('options', []), 1):
                        if isinstance(subopt, dict):
                            sub_title = subopt.get('title', 'N/A')
                            has_response = 'response' in subopt
                            has_submenu = 'submenu' in subopt
                            print(f"        {j}. {sub_title} (respuesta: {has_response}, submenu: {has_submenu})")
                        else:
                            print(f"        {j}. {subopt}")
            else:
                print(f"  {i}. {opt}")
    else:
        print("No hay menú configurado")
else:
    print("No se encontró el bot de Zotek")

cur.close()
conn.close()

print("\n" + "="*70)
