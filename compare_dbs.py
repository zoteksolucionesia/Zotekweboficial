import os
import psycopg2
from dotenv import load_dotenv

def check_tables(url, name):
    print(f"\n--- Tablas en {name} ---")
    try:
        conn = psycopg2.connect(url, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = cur.fetchall()
        for t in tables:
            print(f"- {t[0]}")
        
        print(f"\n--- Relaciones (FK) en {name} ---")
        cur.execute("""
            SELECT
                tc.table_name, kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY' AND tc.table_schema='public';
        """)
        fks = cur.fetchall()
        for fk in fks:
            print(f"- {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error en {name}: {e}")

insforge_url = "postgresql://postgres:c9fcac8bbaa36a424f003a9b8931d0d5@44mhi2w5.us-east.database.insforge.app:5432/insforge"
supabase_url = "postgresql://postgres.bjtqcnecyknwgieijqgh:Zotek2026s445@aws-0-us-west-2.pooler.supabase.com:6543/postgres"

check_tables(insforge_url, "INSFORGE")
check_tables(supabase_url, "SUPABASE")
