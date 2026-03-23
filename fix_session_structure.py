import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Fix: Add reservation_flow to session_data structure
print("Checking session structure...")
cur.execute("""
    SELECT user_number, demo_mode, session_data 
    FROM sandbox_sessions 
    WHERE demo_mode IS NOT NULL 
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"User: {row[0]}, Demo: {row[1]}, SessionData: {row[2]}")

cur.close()
conn.close()
print("\nDone!")
