import sqlite3
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import database

# Note: This requires 'pypdf' or similar. I'll include a placeholder logic 
# that can be expanded if the user installs dependencies.
try:
    from pypdf import PdfReader
except ImportError:
    print("⚠️ 'pypdf' no está instalado. Instálalo con: pip install pypdf")
    PdfReader = None

def ingest_pdf(client_id, pdf_path):
    if not PdfReader:
        print("❌ No se puede procesar PDF sin pypdf.")
        return False
        
    if not os.path.exists(pdf_path):
        print(f"❌ El archivo no existe: {pdf_path}")
        return False

    try:
        reader = PdfReader(pdf_path)
        content = ""
        for page in reader.pages:
            content += page.extract_text() + "\n"
        
        conn = sqlite3.connect(database.DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO knowledge_base (client_id, content, source_file)
            VALUES (?, ?, ?)
        ''', (client_id, content, os.path.basename(pdf_path)))
        conn.commit()
        conn.close()
        print(f"✅ Contenido del PDF '{os.path.basename(pdf_path)}' guardado para el cliente ID {client_id}.")
        return True
    except Exception as e:
        print(f"❌ Error al procesar PDF: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python process_pdfs.py <client_id> <path_to_pdf>")
    else:
        ingest_pdf(int(sys.argv[1]), sys.argv[2])
