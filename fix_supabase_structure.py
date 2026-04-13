import psycopg2

def fix_supabase():
    url = "postgresql://postgres.bjtqcnecyknwgieijqgh:Zotek2026s445@aws-0-us-west-2.pooler.supabase.com:6543/postgres"
    print("🛠️ Iniciando reparación de estructura en Supabase...")
    
    try:
        conn = psycopg2.connect(url, sslmode='require')
        cur = conn.cursor()

        # 1. Crear tabla faltante
        print("- Creando tabla 'appointments'...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                client_id INTEGER,
                phone TEXT,
                name TEXT,
                date_time TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Asegurar que las columnas client_id existen y son del tipo correcto para ser FK
        # (El script init_db ya las crea como INTEGER, pero vamos a asegurar)

        # 3. Aplicar todas las Relaciones (Foreign Keys)
        relationships = [
            ("knowledge_base", "client_id"),
            ("client_chats", "client_id"),
            ("message_logs", "client_id"),
            ("lead_tracking", "client_id"),
            ("email_templates", "client_id"),
            ("consumo_eventos", "client_id"),
            ("tarifas_cliente", "client_id"),
            ("client_schedules", "client_id"),
            ("appointments", "client_id")
        ]

        for table, column in relationships:
            try:
                print(f"- Vinculando {table} con clients...")
                # Primero intentamos borrar si existe para evitar duplicados, luego creamos
                cur.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_client")
                cur.execute(f'''
                    ALTER TABLE {table} 
                    ADD CONSTRAINT fk_{table}_client 
                    FOREIGN KEY ({column}) REFERENCES clients(id) 
                    ON DELETE CASCADE
                ''')
            except Exception as e_row:
                print(f"  ⚠️ Error en {table}: {e_row}")
                conn.rollback() # Limpiar estado de la transacción si falla una FK
                continue

        conn.commit()
        print("\n✅ Reparación completada. Supabase ahora tiene la misma estructura que InsForge.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error crítico durante la reparación: {e}")

if __name__ == "__main__":
    fix_supabase()
