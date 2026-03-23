from src.database import get_connection
from psycopg2.extras import RealDictCursor

def check_db():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, name, phone_number_id FROM clients")
    rows = cursor.fetchall()
    
    print(f"Total clients in DB: {len(rows)}")
    for r in rows:
        print(f"ID: {r['id']} | Name: {r['name']} | Phone_number_id: {r['phone_number_id']}")
        
    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_db()
