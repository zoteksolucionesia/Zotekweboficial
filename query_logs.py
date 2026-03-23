import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import src.database as db

print("Fetching recent message_logs...")
conn = db.get_connection()
cursor = conn.cursor(cursor_factory=db.RealDictCursor)

cursor.execute('''
    SELECT client_id, direction, phone_number, created_at 
    FROM message_logs 
    ORDER BY created_at DESC 
    LIMIT 30
''')

rows = cursor.fetchall()
for r in rows:
    print(f"[{r['created_at']}] Client: {r['client_id']} | Dir: {r['direction']} | Phone: {r['phone_number']}")

cursor.close()
conn.close()
