import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("="*80)
print("VERIFICACIÓN DE CHATS Y PDFs EN POSTGRESQL")
print("="*80)

# 1. Verificar tabla client_chats
print("\n1. TABLA client_chats:")
print("-"*80)
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_name = 'client_chats'
""")
if cur.fetchone():
    print("  ✅ La tabla client_chats EXISTE")
    
    # Contar registros
    cur.execute("SELECT COUNT(*) FROM client_chats")
    count = cur.fetchone()[0]
    print(f"  📊 Registros: {count}")
    
    # Últimos 5 chats
    if count > 0:
        cur.execute("""
            SELECT client_id, user_number, message, response, timestamp 
            FROM client_chats 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        print("\n  Últimos 5 chats:")
        for row in cur.fetchall():
            print(f"    Client: {row[0]}, User: {row[1]}, Message: {row[2][:50] if row[2] else 'NULL'}...")
else:
    print("  ❌ La tabla client_chats NO EXISTE")

# 2. Verificar tabla knowledge_base (PDFs)
print("\n\n2. TABLA knowledge_base (PDFs):")
print("-"*80)
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_name = 'knowledge_base'
""")
if cur.fetchone():
    print("  ✅ La tabla knowledge_base EXISTE")
    
    # Contar registros
    cur.execute("SELECT COUNT(*) FROM knowledge_base")
    count = cur.fetchone()[0]
    print(f"  📊 Documentos: {count}")
    
    # Últimos 5 documentos
    if count > 0:
        cur.execute("""
            SELECT client_id, source_file, LENGTH(content) as content_length, updated_at 
            FROM knowledge_base 
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        print("\n  Últimos 5 documentos:")
        for row in cur.fetchall():
            print(f"    Client: {row[0]}, File: {row[1]}, Length: {row[2]} chars")
else:
    print("  ❌ La tabla knowledge_base NO EXISTE")

# 3. Verificar clientes demo
print("\n\n3. CLIENTES DEMO:")
print("-"*80)
cur.execute("""
    SELECT id, phone_number_id, name 
    FROM clients 
    WHERE phone_number_id LIKE 'demo%'
    ORDER BY id
""")
for row in cur.fetchall():
    print(f"  ID: {row[0]}, Phone ID: {row[1]}, Name: {row[2][:50] if row[2] else 'NULL'}...")

cur.close()
conn.close()

print("\n" + "="*80)
print("VERIFICACIÓN COMPLETADA")
print("="*80)
