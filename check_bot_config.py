#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la configuracion actual de los bots
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("psycopg2 no disponible. Instala: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """Obtiene conexion a PostgreSQL"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        host = os.getenv('DB_HOST', 'localhost')
        database = os.getenv('DB_NAME', 'zotek_db')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        
        if host == 'localhost' and not password:
            print("No se encontro DATABASE_URL en .env")
            return None
        
        return psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
    
    return psycopg2.connect(db_url)


def check_bot_config():
    """Verifica la configuracion de todos los bots"""
    print("="*70)
    print("VERIFICANDO CONFIGURACION DE BOTS")
    print("="*70)
    
    conn = get_db_connection()
    if not conn:
        print("No se pudo conectar a PostgreSQL")
        return
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Ver todos los bots demo
        cursor.execute("""
            SELECT id, name, phone_number_id, system_instruction, menu_json::TEXT as menu_text
            FROM clients 
            WHERE phone_number_id LIKE 'demo%' OR name LIKE '%Zotek%'
            ORDER BY id
        """)
        
        bots = cursor.fetchall()
        
        for bot in bots:
            print("")
            print(f"ID: {bot['id']}")
            # Eliminar emojis del nombre para evitar problemas de codificacion
            name_ascii = bot['name'].encode('ascii', 'replace').decode('ascii')
            print(f"  Nombre: {name_ascii}")
            print(f"  Phone ID: {bot['phone_number_id']}")

            # Verificar menu_json
            menu_text = bot.get('menu_text', '')
            if menu_text:
                # Extraer solo el texto de bienvenida
                if '"text":' in menu_text:
                    start = menu_text.find('"text":') + 7
                    end = menu_text.find(',', start)
                    welcome = menu_text[start:end].strip('"')[:80]
                    welcome_ascii = welcome.encode('ascii', 'replace').decode('ascii')
                    print(f"  Menu Welcome: {welcome_ascii}...")

                    # Verificar si aun tiene "La Trattoria"
                    if 'La Trattoria' in menu_text:
                        print("  WARNING: Todavia contiene 'La Trattoria'!")
                    else:
                        print("  OK: No contiene 'La Trattoria'")

            # System instruction preview
            if bot['system_instruction']:
                preview = bot['system_instruction'][:80].replace('\n', ' ')
                preview = preview.encode('ascii', 'replace').decode('ascii')
                print(f"  System Instruction: {preview}...")
        
        print("")
        print("="*70)
        print("VERIFICACION COMPLETADA")
        print("="*70)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    check_bot_config()
