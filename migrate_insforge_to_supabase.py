import psycopg2
from psycopg2.extras import RealDictCursor
import json

def migrate_data():
    insforge_url = "postgresql://postgres:c9fcac8bbaa36a424f003a9b8931d0d5@44mhi2w5.us-east.database.insforge.app:5432/insforge"
    supabase_url = "postgresql://postgres.bjtqcnecyknwgieijqgh:Zotek2026s445@aws-0-us-west-2.pooler.supabase.com:6543/postgres"

    print("🚀 Iniciando migración de datos (v3 - Sincronizada): InsForge -> Supabase")

    try:
        conn_src = psycopg2.connect(insforge_url, sslmode='require')
        cur_src = conn_src.cursor(cursor_factory=RealDictCursor)

        conn_dst = psycopg2.connect(supabase_url, sslmode='require')
        cur_dst = conn_dst.cursor()

        # 1. Limpiar Supabase (en orden de FKs)
        print("🧹 Limpiando Supabase...")
        tables = [
            "knowledge_base", "client_chats", "citas", "message_logs", 
            "client_schedules", "email_templates", "appointments", 
            "consumo_eventos", "tarifas_cliente", "sandbox_sessions",
            "verification_codes", "conversation_history", "clients"
        ]
        for table in tables:
            cur_dst.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        conn_dst.commit()

        def migrate_table(table_name):
            print(f"📦 Migrando '{table_name}'...")
            cur_src.execute(f"SELECT * FROM {table_name}")
            src_rows = cur_src.fetchall()
            if not src_rows:
                print(f"  ℹ️ Sin registros.")
                return

            # Obtener columnas de destino para ignorar las que no existan
            cur_dst.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' AND table_schema = 'public'")
            dst_cols = [r[0] for r in cur_dst.fetchall()]

            # Filtrar columnas de origen que existen en destino
            src_cols = src_rows[0].keys()
            common_cols = [col for col in src_cols if col in dst_cols]
            
            query = f"INSERT INTO {table_name} ({', '.join(common_cols)}) VALUES ({', '.join(['%s'] * len(common_cols))})"
            
            for row in src_rows:
                values = []
                for col in common_cols:
                    val = row[col]
                    if isinstance(val, (dict, list)):
                        values.append(json.dumps(val))
                    else:
                        values.append(val)
                cur_dst.execute(query, tuple(values))
            
            print(f"  ✅ {len(src_rows)} registros migrados.")

        # Realizar migración
        migrate_table("clients")
        for t in tables[:-1]: # Todas menos clients que ya se hizo
            migrate_table(t)

        conn_dst.commit()
        print("\n✨ ¡MIGRACIÓN COMPLETADA EXITOSAMENTE! ✨")

        cur_src.close()
        conn_src.close()
        cur_dst.close()
        conn_dst.close()

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")

if __name__ == "__main__":
    migrate_data()
