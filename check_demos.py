import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT phone_number_id, name FROM clients WHERE phone_number_id LIKE 'demo%' ORDER BY id")
rows = cur.fetchall()
print("Demos en la base de datos:")
print("-" * 50)
for r in rows:
    print(f"  {r[0]}: {r[1].encode('ascii', 'replace').decode('ascii')}")
print("-" * 50)
print("\nPhone IDs esperados en el codigo:")
print("  demo_restaurant")
print("  demo_clinic (o demo_clinica?)")
print("  demo_retail")
print("  demo_dental")
print("  demo_psychology")
cur.close()
conn.close()
