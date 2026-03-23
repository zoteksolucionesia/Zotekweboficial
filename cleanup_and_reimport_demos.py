"""
Limpieza total y reimportación de los 5 demos con datos EXACTOS de los JSON
"""

import json
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

SERVICE_ACCOUNT_PATH = "functions/service-account-key.json"

def initialize_firebase():
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
        print("✅ Firebase inicializado")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def delete_all_demos():
    """Elimina TODOS los demos de Firestore"""
    db = firestore.client()
    
    # IDs posibles de demos
    demo_ids = [
        # Viejos (3)
        'demo_restaurante', 'demo_clinica', 'demo_tienda',
        # Nuevos hardcodeados (5)
        'demo_dental_sonrisa', 'demo_restaurante_mesa', 'demo_psychology_mente',
        'demo_salon_belleza', 'demo_retail_estilo',
        # Importados (5)
        'demo_dental_001', 'demo_psychology_001', 'demo_restaurant_001',
        'demo_salon_001', 'demo_retail_001',
    ]
    
    deleted = 0
    for doc_id in demo_ids:
        doc_ref = db.collection('clients').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.delete()
            print(f"   🗑️ {doc_id}")
            deleted += 1
    
    return deleted

def convert_json_to_full_zotek(filepath, business_type):
    """Convierte JSON a formato Zotek completo con TODOS los datos"""
    
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
    
    # ===== MENÚ DESDE INTENTS =====
    menu_options = []
    
    icon_map = {
        'agendar_cita': '📅', 'agendar_sesion': '📅',
        'hacer_reserva': '📅',
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
    
    for intent in intents:
        intent_name = intent.get('name', '')
        description = intent.get('description', '')
        responses = intent.get('responses', [])
        
        icon = icon_map.get(intent_name, '💬')
        title = title_map.get(intent_name, f"💬 {intent_name.replace('_', ' ').title()}")
        response = responses[0] if responses else f"Para {description.lower()}, proporciona más detalles."
        
        menu_options.append({'title': title, 'icon': icon, 'response': response})
    
    # ===== AGREGAR FAQs =====
    faqs = knowledge_base.get('faqs', [])
    for faq in faqs:
        question = faq.get('question', '')
        answer = faq.get('answer', '')
        
        if any(w in question.lower() for w in ['costo', 'precio', 'cuesta', 'inversión', 'sesión']):
            menu_options.append({'title': '💰 Costos', 'icon': '💰', 'response': answer})
        elif any(w in question.lower() for w in ['horario', 'abren', 'cierran']):
            menu_options.append({'title': '⏰ Horarios', 'icon': '⏰', 'response': answer})
        elif any(w in question.lower() for w in ['ubicacion', 'dónde', 'sucursales', 'ubicados']):
            menu_options.append({'title': '📍 Ubicación', 'icon': '📍', 'response': answer})
        elif any(w in question.lower() for w in ['cambio', 'devolucion', 'política', 'devolver']):
            menu_options.append({'title': '🔄 Cambios/Devoluciones', 'icon': '🔄', 'response': answer})
        elif any(w in question.lower() for w in ['envio', 'tarda', 'entrega', 'shipping']):
            menu_options.append({'title': '📦 Envíos', 'icon': '📦', 'response': answer})
        elif any(w in question.lower() for w in ['vegano', 'vegetariano', 'mascotas', 'pet', 'gluten']):
            menu_options.append({'title': 'ℹ️ Info', 'icon': 'ℹ️', 'response': answer})
        elif any(w in question.lower() for w in ['factura', 'fiscal', 'pago', 'tarjeta', 'meses']):
            menu_options.append({'title': '💳 Pagos/Factura', 'icon': '💳', 'response': answer})
        elif any(w in question.lower() for w in ['marca', 'tinte', 'producto', 'línea']):
            menu_options.append({'title': '🏷️ Marcas/Productos', 'icon': '🏷️', 'response': answer})
        elif any(w in question.lower() for w in ['novia', 'paquete', 'evento', 'xv']):
            menu_options.append({'title': '👰 Paquetes Especiales', 'icon': '👰', 'response': answer})
        elif any(w in question.lower() for w in ['walk', 'cita', 'tiempo', 'espera']):
            menu_options.append({'title': 'ℹ️ Políticas', 'icon': 'ℹ️', 'response': answer})
    
    # ===== MENSAJE DE BIENVENIDA =====
    welcome_flows = flows.get('on_welcome', [])
    welcome_text = '\n'.join(welcome_flows) if welcome_flows else f"¡Hola! Bienvenido a {bot_name}."
    
    # ===== DATOS BANCARIOS =====
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
    
    return {
        'name': f"🤖 Demo {bot_name}",
        'phone_number_id': phone_id_map.get(business_type),
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
            'fallback_text': "No entendí tu solicitud. Selecciona una opción del menú."
        },
        'created_at': '2026-03-13 00:00:00',
        'whatsapp_token': '',
        'verify_token': f'demo_token_{business_type}',
    }

def import_demo(client_data, doc_id):
    """Importa un demo a Firestore"""
    db = firestore.client()
    doc_ref = db.collection('clients').document(doc_id)
    doc_ref.set(client_data)
    print(f"   ✅ {doc_id}: {client_data['name']}")
    return True

def main():
    print("=" * 60)
    print("🧹 Limpieza Total + Reimportación de 5 Demos")
    print("=" * 60)
    
    if not initialize_firebase():
        return
    
    # Paso 1: Eliminar TODOS los demos
    print("\n🗑️  Paso 1: Eliminando TODOS los demos existentes...")
    deleted = delete_all_demos()
    print(f"   Total eliminados: {deleted}")
    
    # Paso 2: Importar los 5 demos con datos EXACTOS
    print("\n📥 Paso 2: Importando 5 demos con datos EXACTOS de JSON...")
    print("-" * 60)
    
    demos_dir = Path("data/Bots_demo")
    files_config = {
        'Demo_Clinica_Dental.json': 'dental',
        'Demo_Psicologo.json': 'psychology',
        'Demo_Restaurante.json': 'restaurant',
        'Demo_SalonBelleza.json': 'salon',
        'Demo_Tienda_Ropa.json': 'retail',
    }
    
    imported = 0
    for filename, business_type in files_config.items():
        filepath = demos_dir / filename
        print(f"\n📄 {filename}:")
        
        if not filepath.exists():
            print(f"   ❌ No encontrado")
            continue
        
        try:
            client_data = convert_json_to_full_zotek(filepath, business_type)
            bot_id = client_data['phone_number_id']
            
            import_demo(client_data, bot_id)
            imported += 1
            
            # Mostrar menú
            menu = client_data['menu_json']
            print(f"   📋 Menú: {len(menu['options'])} opciones")
            for opt in menu['options']:
                preview = opt['response'][:45] + "..." if len(opt['response']) > 45 else opt['response']
                print(f"      {opt['title']}: {preview}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 Resumen Final")
    print("=" * 60)
    print(f"🗑️  Eliminados: {deleted}")
    print(f"✅ Importados: {imported}")
    print("=" * 60)
    
    if imported == 5:
        print("\n✨ ¡ÉXITO! Ahora hay exactamente 5 demos en Firestore")
        print("\n📋 Los 5 demos son:")
        print("   1. demo_dental_001 - SonrisaPerfecta IA")
        print("   2. demo_psychology_001 - MenteSana Bot")
        print("   3. demo_restaurant_001 - GourmetBot 2026")
        print("   4. demo_salon_001 - GlamourBot 2026")
        print("   5. demo_retail_001 - StyleBot 2026")
        print("\n💡 Ahora actualiza functions/src/database.py para que coincida")
    else:
        print(f"\n⚠️  Se esperaban 5 demos, se importaron {imported}")

if __name__ == "__main__":
    main()
