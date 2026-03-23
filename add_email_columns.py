import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("Agregando columnas email...")

# Agregar email a lead_tracking
cur.execute("ALTER TABLE lead_tracking ADD COLUMN IF NOT EXISTS email TEXT DEFAULT ''")
conn.commit()
print("OK: Columna email agregada a lead_tracking")

# Agregar customer_email a appointments
cur.execute("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS customer_email TEXT DEFAULT ''")
conn.commit()
print("OK: Columna customer_email agregada a appointments")

cur.close()
conn.close()

print("OK: Migracion completada")
