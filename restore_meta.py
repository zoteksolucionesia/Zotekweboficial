import sqlite3
import psycopg2
from src.database import get_connection

def restore_original_client():
    sqlite_db = "data/consultorio.db"
    conn_sq = sqlite3.connect(sqlite_db)
    conn_sq.row_factory = sqlite3.Row
    cursor_sq = conn_sq.cursor()
    cursor_sq.execute("SELECT * FROM clients WHERE id != 9991 AND id != 9992 AND id != 9993")
    clients = [dict(row) for row in cursor_sq.fetchall()]
    conn_sq.close()

    print(f"Found {len(clients)} non-demo clients in SQLite.")

    if not clients:
        return

    conn_pg = get_connection()
    cursor_pg = conn_pg.cursor()

    for client in clients:
        print(f"Restoring {client['name']}")
        try:
            # Reconstruct the fields
            fields = list(client.keys())
            if 'id' in fields:
                fields.remove('id')
            if 'created_at' in fields:
                fields.remove('created_at')
            if 'plan' not in fields:
                client['plan'] = 'free'
                fields.append('plan')
                
            placeholders = ', '.join(['%(' + f + ')s' for f in fields])
            query = f"INSERT INTO clients ({', '.join(fields)}) VALUES ({placeholders}) ON CONFLICT (phone_number_id) DO NOTHING"
            
            cursor_pg.execute(query, client)
            conn_pg.commit()
            print("✅ Restored!")
        except Exception as e:
            print(f"❌ Failed: {e}")
            conn_pg.rollback()

    cursor_pg.close()
    conn_pg.close()

if __name__ == '__main__':
    restore_original_client()
