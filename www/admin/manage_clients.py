import sqlite3
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import database

def list_clients():
    conn = sqlite3.connect(database.DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone_number_id FROM clients")
    clients = cursor.fetchall()
    conn.close()
    
    print("\n--- LISTA DE CLIENTES ---")
    for c in clients:
        print(f"ID: {c['id']} | Nombre: {c['name']} | Phone ID: {c['phone_number_id']}")
    print("-------------------------\n")

def add_client():
    print("\n--- AGREGAR NUEVO CLIENTE ---")
    name = input("Nombre del negocio: ")
    whatsapp_token = input("WhatsApp Access Token: ")
    phone_number_id = input("Phone Number ID: ")
    verify_token = input("Verify Token (ej. MI_TOKEN_123): ")
    system_instruction = input("Instrucción del sistema (AI personality): ")
    
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO clients (name, whatsapp_token, phone_number_id, verify_token, system_instruction)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, whatsapp_token, phone_number_id, verify_token, system_instruction))
        conn.commit()
        print(f"✅ Cliente '{name}' agregado con éxito.")
    except Exception as e:
        print(f"❌ Error al agregar cliente: {e}")
    finally:
        conn.close()

def main():
    while True:
        print("1. Listar Clientes")
        print("2. Agregar Cliente")
        print("3. Salir")
        choice = input("Seleccione una opción: ")
        
        if choice == '1':
            list_clients()
        elif choice == '2':
            add_client()
        elif choice == '3':
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    database.init_db()
    main()
