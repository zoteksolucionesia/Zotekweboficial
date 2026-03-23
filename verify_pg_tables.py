from src.database_pg import get_connection

def verify_tables():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print("Tablas encontradas en InsForge:")
        for table in tables:
            print(f"- {table[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al verificar tablas: {e}")

if __name__ == "__main__":
    verify_tables()
