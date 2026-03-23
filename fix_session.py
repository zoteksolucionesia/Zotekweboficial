import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Fix the session for this user
cur.execute("""
    UPDATE sandbox_sessions 
    SET demo_mode = 'restaurant',
        session_data = jsonb_set(
            session_data::jsonb,
            '{demo_mode}',
            '"restaurant"'
        ) || jsonb_build_object('demo_phone_id', 'demo_restaurant')
    WHERE user_number = '5213123173431'
""")

conn.commit()

# Verify the fix
cur.execute("SELECT user_number, demo_mode, session_data FROM sandbox_sessions WHERE user_number = %s", ('5213123173431',))
row = cur.fetchone()
if row:
    print(f'User: {row[0]}')
    print(f'Demo: {row[1]}')
    print(f'SessionData: {row[2]}')
else:
    print('No session found')

cur.close()
conn.close()
print('\nSession fixed! Try responding "hoy" again in WhatsApp.')
