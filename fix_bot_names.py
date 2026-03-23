#!/usr/bin/env python3
"""
Script para corregir los nombres y configuraciones de los bots en Firebase/PostgreSQL
Elimina referencias a "La Trattoria" y actualiza a "GourmetBot 2026"
"""

import os
import sys

# Intentar importar firebase_admin, si no está disponible, solo usar PostgreSQL
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    print("⚠️ firebase_admin no disponible. Solo se actualizará PostgreSQL.")
    FIREBASE_AVAILABLE = False

# Importar psycopg2 para PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    print("❌ psycopg2 no disponible. No se puede conectar a PostgreSQL.")
    POSTGRES_AVAILABLE = False
    sys.exit(1)


def update_postgres():
    """Actualiza los bots en PostgreSQL"""
    print("\n" + "="*60)
    print("ACTUALIZANDO POSTGRESQL")
    print("="*60)
    
    # Conexión a PostgreSQL
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'zotek_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Actualizar GourmetBot 2026
    update_queries = [
        """
        UPDATE clients 
        SET name = '🤖 Demo GourmetBot 2026',
            system_instruction = 'Eres el asistente virtual experto de GourmetBot 2026. Eres el asistente virtual experto del Restaurante ''La Mesa Elegante''. Tu objetivo es tomar pedidos, gestionar reservas y resolver dudas. Responde de manera amable, rápida y apetitosa. Si el usuario tiene restricciones alimentarias, prioriza recomendar platillos seguros.'
        WHERE phone_number_id = 'demo_restaurant' OR id = 'demo_restaurant'
        """,
        """
        UPDATE clients 
        SET name = '🤖 Demo GourmetBot 2026',
            system_instruction = 'Eres el asistente virtual experto de GourmetBot 2026. Eres el asistente virtual experto del Restaurante ''La Mesa Elegante''. Tu objetivo es tomar pedidos, gestionar reservas y resolver dudas. Responde de manera amable, rápida y apetitosa. Si el usuario tiene restricciones alimentarias, prioriza recomendar platillos seguros.'
        WHERE phone_number_id = 'demo_restaurant_001' OR id = 'demo_restaurant_001'
        """,
    ]
    
    for query in update_queries:
        try:
            cursor.execute(query)
            updated = cursor.rowcount
            if updated > 0:
                print(f"✅ Actualizadas {updated} fila(s)")
            else:
                print(f"⚠️ No se encontraron filas para actualizar")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Actualizar menu_json si contiene "La Trattoria"
    cursor.execute("SELECT id, menu_json FROM clients WHERE menu_json LIKE '%La Trattoria%'")
    rows = cursor.fetchall()
    
    for row in rows:
        menu_json = row['menu_json']
        if menu_json:
            # Reemplazar "La Trattoria" con "GourmetBot 2026"
            new_menu_json = menu_json.replace('La Trattoria', 'GourmetBot 2026')
            new_menu_json = new_menu_json.replace(
                '¡Bienvenido a *GourmetBot 2026*! 👋 Soy tu asistente virtual.',
                '¡Bienvenido a *GourmetBot 2026*! 👋 Soy tu asistente virtual del restaurante \'La Mesa Elegante\'.'
            )
            
            cursor.execute(
                "UPDATE clients SET menu_json = %s WHERE id = %s",
                (new_menu_json, row['id'])
            )
            print(f"✅ Actualizado menu_json para cliente: {row['id']}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL actualizado correctamente")


def update_firebase():
    """Actualiza los bots en Firebase Firestore"""
    if not FIREBASE_AVAILABLE:
        print("⚠️ Firebase no disponible, saltando...")
        return
    
    print("\n" + "="*60)
    print("ACTUALIZANDO FIREBASE")
    print("="*60)
    
    try:
        # Inicializar Firebase
        cred_path = 'service-account-key.json'
        if not os.path.exists(cred_path):
            print(f"❌ No se encontró {cred_path}")
            return
            
        cred = credentials.Certificate(cred_path)
        
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
        
        db = firestore.client()
        
        # Buscar clientes con "La Trattoria"
        clients_ref = db.collection('clients')
        query = clients_ref.where('name', '>=', 'La Trattoria').where('name', '<=', 'La Trattoria\uf8ff')
        docs = query.stream()
        
        updated_count = 0
        for doc in docs:
            data = doc.to_dict()
            if 'La Trattoria' in data.get('name', '') or 'La Trattoria' in data.get('system_instruction', ''):
                print(f"📝 Encontrado: {doc.id} - {data.get('name')}")
                
                update_data = {}
                if 'La Trattoria' in data.get('name', ''):
                    update_data['name'] = data['name'].replace('La Trattoria', '🤖 Demo GourmetBot 2026')
                if 'La Trattoria' in data.get('system_instruction', ''):
                    update_data['system_instruction'] = data['system_instruction'].replace(
                        'La Trattoria', 
                        'GourmetBot 2026 - Restaurante La Mesa Elegante'
                    )
                
                if update_data:
                    clients_ref.document(doc.id).update(update_data)
                    print(f"✅ Actualizado: {doc.id}")
                    updated_count += 1
        
        print(f"✅ Firebase: {updated_count} cliente(s) actualizado(s)")
        
    except Exception as e:
        print(f"❌ Error en Firebase: {e}")


def verify_zotek_master():
    """Verifica que el bot maestro de Zotek esté configurado"""
    print("\n" + "="*60)
    print("VERIFICANDO ZOTEK MASTER BOT")
    print("="*60)
    
    if POSTGRES_AVAILABLE:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'zotek_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar el bot maestro de Zotek
        cursor.execute("""
            SELECT id, name, phone_number_id, is_active, system_instruction 
            FROM clients 
            WHERE name LIKE '%Zotek%' OR phone_number_id = '980996958435648'
        """)
        
        zotek_bots = cursor.fetchall()
        
        if zotek_bots:
            print(f"✅ Bot(s) Zotek encontrado(s): {len(zotek_bots)}")
            for bot in zotek_bots:
                print(f"  - ID: {bot['id']}")
                print(f"    Nombre: {bot['name']}")
                print(f"    Phone ID: {bot['phone_number_id']}")
                print(f"    Activo: {bot['is_active']}")
                print(f"    System Instruction: {bot['system_instruction'][:100] if bot['system_instruction'] else 'None'}...")
        else:
            print("⚠️ No se encontró el bot maestro de Zotek")
            print("   Ejecuta: python restore_zotek_master.py")
        
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("🔧 Script de corrección de bots - Zotek Soluciones IA")
    print("="*60)
    
    # Actualizar PostgreSQL
    if POSTGRES_AVAILABLE:
        update_postgres()
    
    # Actualizar Firebase
    if FIREBASE_AVAILABLE:
        update_firebase()
    
    # Verificar Zotek Master
    verify_zotek_master()
    
    print("\n" + "="*60)
    print("✅ Script completado")
    print("="*60)
    print("\n⚠️ IMPORTANTE: Reinicia los servidores para aplicar los cambios:")
    print("   - Functions: firebase deploy --only functions")
    print("   - Main API: python src/main.py")
