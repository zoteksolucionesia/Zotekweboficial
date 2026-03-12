#!/usr/bin/env python
"""
Script para limpiar clientes duplicados de la base de datos.
Elimina las copias de demos que se hayan creado accidentalmente.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "consultorio.db")

def clean_duplicate_demos():
    """Elimina clientes que sean copias de demos."""
    
    print(f"🗄️  Conectando a base de datos: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar tabla clients
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
    if not cursor.fetchone():
        print("❌ La tabla 'clients' no existe")
        conn.close()
        return
    
    # Contar registros antes
    cursor.execute("SELECT COUNT(*) FROM clients")
    count_before = cursor.fetchone()[0]
    print(f"📊 Clientes antes de limpiar: {count_before}")
    
    # Listar todos los clientes
    cursor.execute("SELECT id, name, phone_number_id FROM clients")
    clients = cursor.fetchall()
    
    print("\n📋 Clientes actuales:")
    for client in clients:
        print(f"   ID: {client[0]}, Nombre: {client[1]}, Phone ID: {client[2]}")
    
    # Eliminar clientes que sean copias de demos (phone_number_id empieza con 'client_' y name contiene 'Copia')
    cursor.execute("""
        DELETE FROM clients 
        WHERE phone_number_id LIKE 'client_%' 
        AND (name LIKE '%(Copia %' OR name LIKE '%(Copy %')
    """)
    deleted_count = cursor.rowcount
    
    # También eliminar cualquier cliente con phone_number_id de demo pero que esté en BD
    # (esto no debería pasar, pero por seguridad)
    cursor.execute("""
        DELETE FROM clients 
        WHERE phone_number_id IN ('demo_restaurante', 'demo_clinica', 'demo_tienda')
    """)
    demo_deleted = cursor.rowcount
    
    if demo_deleted > 0:
        print(f"⚠️  Se eliminaron {demo_deleted} registros de demos puros (no deberían existir en BD)")
    
    # Contar registros después
    cursor.execute("SELECT COUNT(*) FROM clients")
    count_after = cursor.fetchone()[0]
    
    print(f"\n📊 Clientes después de limpiar: {count_after}")
    print(f"🗑️  Registros eliminados: {deleted_count + demo_deleted}")
    
    # Confirmar cambios
    conn.commit()
    conn.close()
    
    print("\n✅ Limpieza completada exitosamente")
    print("\n📝 Nota: Los 3 demos originales (9991, 9992, 9993) siguen disponibles")
    print("   porque están hardcodeados en el código, no en la base de datos.")

if __name__ == "__main__":
    clean_duplicate_demos()
