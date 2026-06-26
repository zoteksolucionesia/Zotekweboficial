import sys
sys.path.insert(0, '.')
from functions.src.database import get_connection

conn = get_connection()
cursor = conn.cursor()
try:
    print("Searching for token 'c7b412cf-f08f-4e56-ba42-725dc88968c8'...")
    # Check what columns exist in the appointments table (we saw it was named "citas" or "appointments" in different code parts?)
    # Wait, functions/src/main.py uses:
    # database.get_appointment_by_token(token)
    # Let's inspect the database structure or verify which table holds appointments.
    cursor.execute("SELECT * FROM appointments WHERE token='c7b412cf-f08f-4e56-ba42-725dc88968c8'")
    rows = cursor.fetchall()
    print("In 'appointments':", rows)
except Exception as e:
    print("Error appointments:", e)

try:
    # Check in citas table too
    cursor.execute("SELECT * FROM citas WHERE token='c7b412cf-f08f-4e56-ba42-725dc88968c8'")
    rows = cursor.fetchall()
    print("In 'citas':", rows)
except Exception as e:
    print("Error citas:", e)

try:
    # Print the last 5 appointments from the appointments table
    cursor.execute("SELECT id, client_id, token, status, created_at FROM appointments ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    print("\nLast 5 in 'appointments':")
    for r in rows:
        print(r)
except Exception as e:
    print("Error querying last appointments:", e)

cursor.close()
conn.close()
