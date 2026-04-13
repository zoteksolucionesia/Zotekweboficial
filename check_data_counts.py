import psycopg2

def count_rows(url, name):
    print(f"\n--- Conteo de datos en {name} ---")
    try:
        conn = psycopg2.connect(url, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [t[0] for t in cur.fetchall()]
        
        for table in sorted(tables):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"- {table}: {count} registros")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error en {name}: {e}")

insforge_url = "postgresql://postgres:c9fcac8bbaa36a424f003a9b8931d0d5@44mhi2w5.us-east.database.insforge.app:5432/insforge"
supabase_url = "postgresql://postgres.bjtqcnecyknwgieijqgh:Zotek2026s445@aws-0-us-west-2.pooler.supabase.com:6543/postgres"

count_rows(insforge_url, "INSFORGE")
count_rows(supabase_url, "SUPABASE")
