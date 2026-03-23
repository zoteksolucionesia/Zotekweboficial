"""
Script para actualizar los 5 Demos con la información EXACTA de los archivos JSON
Elimina los 3 demos originales e importa los 5 nuevos con datos completos
"""

import json
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

SERVICE_ACCOUNT_PATH = "functions/service-account-key.json"

def initialize_firebase():
    """Inicializa Firebase Admin SDK"""
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
        print("✅ Firebase inicializado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def convert_json_to_zotek(filepath, business_type):
    """Convierte un archivo JSON al formato Zotek con TODA la información"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    agent_config = json_data.get('agent_config', {})
    llm_settings = json_data.get('llm_settings', {})
    flows = json_data.get('flows', {})
    intents = json_data.get('intents', [])
    knowledge_base = json_data.get('knowledge_base', {})
    
    bot_name = agent_config.get('name', 'Bot')
    bot_id = agent_config.get('id', 'unknown')
    system_prompt = llm_settings.get('system_prompt', '')
    
    # ============================================
    # CONSTRUIR MENÚ DESDE INTENTS
    # ============================================
    
    menu_options = []
    
    for intent in intents:
        intent_name = intent.get('name', '')
        description = intent.get('description', '')
        responses = intent.get('responses', [])
        
        # Iconos específicos por intent
        icon_map = {
            'agendar_cita': '📅', 'agendar_sesion': '📅',
            'hacer_reserva': '📅', 'reservar_mesa': '📅',
            'reportar_emergencia': '🚨', 'crisis_urgencia': '🚨',
            'validar_seguro': '📄',
            'info_terapia': 'ℹ️',
            'pedir_domicilio': '🛵',
            'consultar_menu': '📋',
            'consultar_precios': '💰',
            'cancelar_cita': '🔄',
            'buscar_prenda_imagen': '📷',
            'rastrear_pedido': '📦',
            'asesoria_tallas': '📏',
        }
        
        icon = icon_map.get(intent_name, '💬')
        
        # Títulos específicos
        title_map = {
            'agendar_cita': '📅 Agendar Cita',
            'agendar_sesion': '📅 Agendar Sesión',
            'hacer_reserva': '📅 Reservar Mesa',
            'reportar_emergencia': '🚨 Reportar Emergencia',
            'crisis_urgencia': '🚨 Crisis/Emergencia',
            'validar_seguro': '📄 Validar Seguro',
            'info_terapia': 'ℹ️ Info Terapia',
            'pedir_domicilio': '🛵 Pedir Domicilio',
            'consultar_menu': '📋 Ver Menú',
            'consultar_precios': '💰 Consultar Precios',
            'cancelar_cita': '🔄 Cancelar/Reagendar',
            'buscar_prenda_imagen': '📷 Buscar con Foto',
            'rastrear_pedido': '📦 Rastrear Pedido',
            'asesoria_tallas': '📏 Asesoría de Tallas',
        }
        
        title = title_map.get(intent_name, f"💬 {intent_name.replace('_', ' ').title()}")
        
        # Usar la respuesta específica del JSON si existe
        if responses:
            response = responses[0]
        else:
            response = f"Para {description.lower()}, por favor proporciona más detalles."
        
        menu_options.append({
            'title': title,
            'icon': icon,
            'response': response
        })
    
    # ============================================
    # AGREGAR INFORMACIÓN DEL KNOWLEDGE BASE COMO OPCIONES EXTRA
    # ============================================
    
    faqs = knowledge_base.get('faqs', [])
    
    # Agregar FAQs como opciones adicionales si hay menos de 6 opciones
    if len(menu_options) < 6 and faqs:
        # Extraer información relevante de FAQs
        for faq in faqs:
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            
            # Detectar tipo de FAQ y crear opción
            if 'costo' in question.lower() or 'precio' in question.lower() or 'cuesta' in question.lower():
                menu_options.append({
                    'title': '💰 Costos',
                    'icon': '💰',
                    'response': answer
                })
            elif 'horario' in question.lower() or 'horarios' in question.lower() or 'abren' in question.lower():
                menu_options.append({
                    'title': '⏰ Horarios',
                    'icon': '⏰',
                    'response': answer
                })
            elif 'ubicacion' in question.lower() or 'dónde' in question.lower() or 'sucursales' in question.lower():
                menu_options.append({
                    'title': '📍 Ubicación',
                    'icon': '📍',
                    'response': answer
                })
            elif 'cambio' in question.lower() or 'devolucion' in question.lower() or 'política' in question.lower():
                menu_options.append({
                    'title': '🔄 Cambios/Devoluciones',
                    'icon': '🔄',
                    'response': answer
                })
            elif 'envio' in question.lower() or 'envío' in question.lower() or 'tarda' in question.lower():
                menu_options.append({
                    'title': '📦 Envíos',
                    'icon': '📦',
                    'response': answer
                })
            elif 'vegano' in question.lower() or 'opciones' in question.lower() or 'mascotas' in question.lower():
                menu_options.append({
                    'title': 'ℹ️ Información',
                    'icon': 'ℹ️',
                    'response': answer
                })
    
    # ============================================
    # MENSAJE DE BIENVENIDA DESDE FLOWS
    # ============================================
    
    welcome_flows = flows.get('on_welcome', [])
    if welcome_flows:
        welcome_text = '\n'.join(welcome_flows)
    else:
        welcome_text = f"¡Hola! Bienvenido a {bot_name}. ¿En qué puedo ayudarte?"
    
    # ============================================
    # DATOS BANCARIOS Y DE CONTACTO
    # ============================================
    
    bank_data = {
        'dental': {'bank': 'BBVA', 'clabe': '012180012345678901'},
        'psychology': {'bank': 'Banorte', 'clabe': '072180056789012345'},
        'restaurant': {'bank': 'Santander', 'clabe': '014180098765432109'},
        'salon': {'bank': 'HSBC', 'clabe': '021180067890123456'},
        'retail': {'bank': 'Scotiabank', 'clabe': '044180034567890123'},
    }
    
    bank_info = bank_data.get(business_type, {'bank': 'BBVA', 'clabe': '012180011111111111'})
    
    phone_id_map = {
        'dental': 'demo_dental_001',
        'psychology': 'demo_psychology_001',
        'restaurant': 'demo_restaurant_001',
        'salon': 'demo_salon_001',
        'retail': 'demo_retail_001',
    }
    
    # ============================================
    # CONSTRUIR DATOS COMPLETOS
    # ============================================
    
    client_data = {
        'name': f"🤖 Demo {bot_name}",
        'phone_number_id': phone_id_map.get(business_type, f'demo_{business_type}'),
        'email': f"{business_type}@demo.zotek.ia",
        'phone': f"52155000000{hash(bot_id) % 1000:03d}",
        'system_instruction': system_prompt,
        'gemini_prompt': f"Eres el asistente virtual experto de {bot_name}. {system_prompt}",
        'response_type': 'text',
        'calendly_url': f"https://calendly.com/{business_type}-demo" if business_type in ['dental', 'psychology', 'restaurant'] else '',
        'bank_name': bank_info['bank'],
        'clabe': bank_info['clabe'],
        'beneficiary_name': f"{bot_name} Demo SA de CV",
        'menu_json': {
            'text': welcome_text,
            'options': menu_options,
            'fallback_text': "No entendí tu solicitud. Por favor selecciona una opción del menú o sé más específico."
        },
        'created_at': '2026-03-13 00:00:00',
        'whatsapp_token': '',
        'verify_token': f'demo_token_{business_type}',
    }
    
    return client_data, bot_id

def delete_old_demos():
    """Elimina los 3 demos originales de Firestore"""
    db = firestore.client()
    
    old_demo_ids = [
        'demo_restaurante',
        'demo_clinica',
        'demo_tienda',
    ]
    
    deleted = 0
    for doc_id in old_demo_ids:
        doc_ref = db.collection('clients').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.delete()
            print(f"   🗑️ Eliminado: {doc_id}")
            deleted += 1
        else:
            print(f"   ⚠️  No existe: {doc_id}")
    
    return deleted

def import_demo(client_data, doc_id):
    """Importa o actualiza un demo en Firestore"""
    db = firestore.client()
    
    doc_ref = db.collection('clients').document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        # Actualizar existente
        doc_ref.update(client_data)
        print(f"   ✏️  Actualizado: {doc_id}")
    else:
        # Crear nuevo
        doc_ref.set(client_data)
        print(f"   ✅ Creado: {doc_id}")
    
    # --- NUEVO: Guardar menú en subcolección config/menu ---
    if 'menu_json' in client_data:
        menu_data = client_data['menu_json']
        # Guardar en clients/{doc_id}/config/menu
        db.collection('clients').document(doc_id).collection('config').document('menu').set(menu_data)
        print(f"   📋 Menú guardado en subcolección para: {doc_id}")
    
    return 'updated' if doc.exists else 'created'

def main():
    print("=" * 60)
    print("🔄 Actualización de Demos con Información JSON Exacta")
    print("=" * 60)
    
    if not initialize_firebase():
        return
    
    demos_dir = Path("data/Bots_demo")
    
    files_config = {
        'Demo_Clinica_Dental.json': 'dental',
        'Demo_Psicologo.json': 'psychology',
        'Demo_Restaurante.json': 'restaurant',
        'Demo_SalonBelleza.json': 'salon',
        'Demo_Tienda_Ropa.json': 'retail',
    }
    
    # Paso 1: Eliminar demos antiguos
    print("\n🗑️  Paso 1: Eliminando demos originales...")
    deleted = delete_old_demos()
    print(f"   Total eliminados: {deleted}")
    
    # Paso 2: Importar nuevos demos con datos exactos
    print("\n📥 Paso 2: Importando 5 demos con información JSON exacta...")
    print("-" * 60)
    
    created_count = 0
    updated_count = 0
    
    for filename, business_type in files_config.items():
        filepath = demos_dir / filename
        print(f"\n📄 {filename}:")
        
        if not filepath.exists():
            print(f"   ❌ No encontrado")
            continue
        
        try:
            client_data, bot_id = convert_json_to_zotek(filepath, business_type)
            
            # Generar ID único
            doc_id = f"demo_{business_type}_{bot_id.split('_')[-1]}"
            
            # Importar
            result = import_demo(client_data, doc_id)
            if result == 'created':
                created_count += 1
            else:
                updated_count += 1
            
            # Mostrar menú
            menu = client_data['menu_json']
            print(f"   📋 Menú: {len(menu['options'])} opciones")
            for opt in menu['options']:
                print(f"      {opt['title']}: {opt['response'][:50]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 Resumen")
    print("=" * 60)
    print(f"🗑️  Eliminados: {deleted}")
    print(f"✅ Creados: {created_count}")
    print(f"✏️  Actualizados: {updated_count}")
    print(f"📁 Total: {deleted + created_count + updated_count}")
    print("=" * 60)
    
    print("\n✨ ¡Actualización completada!")
    print("\n💡 Ahora los 5 demos tienen la información EXACTA de tus archivos JSON")
    print("\n🔍 Para verificar:")
    print("   1. Ve a Firebase Console > Firestore Database")
    print("   2. Colección 'clients'")
    print("   3. Busca los documentos: demo_dental_001, demo_psychology_001, etc.")

if __name__ == "__main__":
    main()
