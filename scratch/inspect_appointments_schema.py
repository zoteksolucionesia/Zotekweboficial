import sys
sys.path.insert(0, '.')
from functions.src.database import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'appointments'
""")
for r in cursor.fetchall():
    print(r)
cursor.close()
conn.close()
