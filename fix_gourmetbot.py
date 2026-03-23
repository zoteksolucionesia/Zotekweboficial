#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir los nombres y configuraciones de los bots en PostgreSQL
Elimina referencias a "La Trattoria" y actualiza a "GourmetBot 2026"
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar psycopg2 para PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    print("psycopg2 no disponible. Instala: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """Obtiene conexion a PostgreSQL"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # Intentar con variables individuales
        host = os.getenv('DB_HOST', 'localhost')
        database = os.getenv('DB_NAME', 'zotek_db')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        
        if host == 'localhost' and not password:
            print("No se encontro DATABASE_URL en .env")
            print("Configura tu archivo .env con las credenciales de PostgreSQL")
            return None
        
        return psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
    
    # Conectar usando URL
    return psycopg2.connect(db_url)


def update_gourmetbot():
    """Actualiza GourmetBot 2026 en PostgreSQL"""
    print("")
    print("="*60)
    print("ACTUALIZANDO GOURMETBOT 2026")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("No se pudo conectar a PostgreSQL")
        return False
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Actualizar demo_restaurant (usando phone_number_id, no id)
        cursor.execute("""
            UPDATE clients
            SET name = %s,
                system_instruction = %s
            WHERE phone_number_id = %s
        """, (
            'Demo GourmetBot 2026',
            "Eres el asistente virtual experto de GourmetBot 2026. Eres el asistente virtual experto del Restaurante 'La Mesa Elegante'. Tu objetivo es tomar pedidos, gestionar reservas y resolver dudas. Responde de manera amable, rapida y apetitosa. Si el usuario tiene restricciones alimentarias, prioriza recomendar platillos seguros.",
            'demo_restaurant'
        ))
        updated = cursor.rowcount
        print(f"demo_restaurant: {updated} fila(s) actualizada(s)")

        # Actualizar demo_restaurant_001
        cursor.execute("""
            UPDATE clients
            SET name = %s,
                system_instruction = %s
            WHERE phone_number_id = %s
        """, (
            'Demo GourmetBot 2026',
            "Eres el asistente virtual experto de GourmetBot 2026. Eres el asistente virtual experto del Restaurante 'La Mesa Elegante'. Tu objetivo es tomar pedidos, gestionar reservas y resolver dudas. Responde de manera amable, rapida y apetitosa. Si el usuario tiene restricciones alimentarias, prioriza recomendar platillos seguros.",
            'demo_restaurant_001'
        ))
        updated = cursor.rowcount
        print(f"demo_restaurant_001: {updated} fila(s) actualizada(s)")
        
        # Actualizar menu_json si contiene "La Trattoria" (convertir JSONB a texto primero)
        cursor.execute("SELECT id, menu_json::TEXT as menu_json_text FROM clients WHERE menu_json::TEXT LIKE '%La Trattoria%'")
        rows = cursor.fetchall()

        for row in rows:
            menu_json = row['menu_json_text']
            if menu_json:
                # Reemplazar "La Trattoria" con "GourmetBot 2026"
                new_menu_json = menu_json.replace('La Trattoria', 'GourmetBot 2026')

                cursor.execute(
                    "UPDATE clients SET menu_json = %s::jsonb WHERE id = %s",
                    (new_menu_json, row['id'])
                )
                print(f"Actualizado menu_json para cliente: {row['id']}")
        
        conn.commit()
        print("")
        print("GourmetBot 2026 actualizado correctamente")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def verify_zotek_master():
    """Verifica que el bot maestro de Zotek este configurado"""
    print("")
    print("="*60)
    print("VERIFICANDO ZOTEK MASTER BOT")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        return False
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Buscar el bot maestro de Zotek
        cursor.execute("""
            SELECT id, name, phone_number_id, system_instruction
            FROM clients
            WHERE name LIKE '%Zotek%' OR phone_number_id = '980996958435648'
            ORDER BY id
        """)

        zotek_bots = cursor.fetchall()

        if zotek_bots:
            print(f"Bot(s) Zotek encontrado(s): {len(zotek_bots)}")
            for bot in zotek_bots:
                print(f"  ID: {bot['id']}")
                print(f"     Nombre: {bot['name']}")
                print(f"     Phone ID: {bot['phone_number_id']}")
                if bot['system_instruction']:
                    preview = bot['system_instruction'][:150].replace('\n', ' ')
                    # Eliminar caracteres no ASCII para evitar errores de codificacion
                    preview = preview.encode('ascii', 'replace').decode('ascii')
                    print(f"     System Instruction: {preview}...")
        else:
            print("No se encontro el bot maestro de Zotek")
            print("   Ejecuta: python restore_zotek_master.py")

        # Verificar GourmetBot
        cursor.execute("""
            SELECT id, name, phone_number_id, system_instruction
            FROM clients
            WHERE phone_number_id LIKE 'demo_restaurant%'
            ORDER BY id
        """)

        gourmet_bots = cursor.fetchall()

        if gourmet_bots:
            print(f"GourmetBot 2026 encontrado(s): {len(gourmet_bots)}")
            for bot in gourmet_bots:
                print(f"  ID: {bot['id']}")
                print(f"     Nombre: {bot['name']}")
                print(f"     Phone ID: {bot['phone_number_id']}")
                if bot['system_instruction']:
                    preview = bot['system_instruction'][:150].replace('\n', ' ')
                    preview = preview.encode('ascii', 'replace').decode('ascii')
                    print(f"     System Instruction: {preview}...")
        else:
            print("No se encontro GourmetBot 2026")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("Script de correccion de bots - Zotek Soluciones IA")
    print("   Eliminando 'La Trattoria' -> 'GourmetBot 2026'")
    print("="*60)
    
    # Actualizar GourmetBot
    if update_gourmetbot():
        print("")
        print("Actualizacion completada")
    else:
        print("")
        print("Error en la actualizacion")
    
    # Verificar bots
    verify_zotek_master()
    
    print("")
    print("="*60)
    print("Script completado")
    print("="*60)
    print("")
    print("IMPORTANTE: Reinicia los servidores para aplicar los cambios:")
    print("   1. Deten el servidor actual (Ctrl+C)")
    print("   2. python src/main.py")
