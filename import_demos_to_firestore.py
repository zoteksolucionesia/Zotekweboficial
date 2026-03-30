"""
Script para importar los 5 demos a Firebase Firestore
Requiere: firebase-admin instalado y service-account-key.json
"""

import json
import firebase_admin
from firebase_admin import credentials, firestore

# Ruta al service account (descárgalo de Firebase Console)
SERVICE_ACCOUNT_PATH = "functions/service-account-key.json"

def initialize_firebase():
    """Inicializa Firebase Admin SDK"""
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
        print("✅ Firebase inicializado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar Firebase: {e}")
        print("💡 Asegúrate de tener el archivo service-account-key.json")
        return False

def import_demos():
    """Importa los demos a Firestore"""
    
    # Cargar demos
    with open("data/demos_completos_firestore.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    demos = data['demos']
    db = firestore.client()
    
    print(f"\n📥 Importando {len(demos)} demos a Firestore...\n")
    
    imported = 0
    skipped = 0
    
    for demo in demos:
        doc_id = demo['id']
        doc_data = demo['firestore_data']
        
        # Verificar si ya existe
        doc_ref = db.collection('clients').document(doc_id)
        doc = doc_ref.get()
        
        if doc.exists:
            print(f"⚠️  '{doc_id}' ya existe - Saltando")
            skipped += 1
            continue
        
        # Crear documento
        doc_ref.set(doc_data)
        print(f"✅ '{doc_id}' importado: {doc_data['name']}")
        imported += 1
    
    print(f"\n" + "=" * 60)
    print(f"✅ Importados: {imported}")
    print(f"⚠️  Saltados: {skipped}")
    print("=" * 60)

if __name__ == "__main__":
    if initialize_firebase():
        import_demos()
