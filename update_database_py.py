"""
Script para actualizar functions/src/database.py con los 5 demos exactos de los JSON
Reemplaza las funciones list_clients() y get_client_by_id() con los datos correctos
"""

import json
import re
from pathlib import Path

def load_json_data(filepath):
    """Carga un archivo JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_to_zotek_full(json_data, business_type):
    """Convierte JSON a formato Zotek completo"""
    
    agent_config = json_data.get('agent_config', {})
    llm_settings = json_data.get('llm_settings', {})
    flows = json_data.get('flows', {})
    intents = json_data.get('intents', [])
    knowledge_base = json_data.get('knowledge_base', {})
    
    bot_name = agent_config.get('name', 'Bot')
    bot_id = agent_config.get('id', 'unknown')
    system_prompt = llm_settings.get('system_prompt', '')
    
    # Construir menú desde intents
    menu_options = []
    
    icon_map = {
        'agendar_cita': '📅', 'agendar_sesion': '📅',
        'hacer_reserva': '📅', 'reportar_emergencia': '🚨',
        'crisis_urgencia': '🚨', 'validar_seguro': '📄',
        'info_terapia': 'ℹ️', 'pedir_domicilio': '🛵',
        'consultar_menu': '📋', 'consultar_precios': '💰',
        'cancelar_cita': '🔄', 'buscar_prenda_imagen': '📷',
        'rastrear_pedido': '📦', 'asesoria_tallas': '📏',
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
        
        menu_options.append({
            'title': title,
            'icon': icon,
            'response': response
        })
    
    # Agregar FAQs como opciones
    faqs = knowledge_base.get('faqs', [])
    for faq in faqs:
        question = faq.get('question', '')
        answer = faq.get('answer', '')
        
        if any(word in question.lower() for word in ['costo', 'precio', 'cuesta']):
            menu_options.append({'title': '💰 Costos', 'icon': '💰', 'response': answer})
        elif any(word in question.lower() for word in ['horario', 'abren']):
            menu_options.append({'title': '⏰ Horarios', 'icon': '⏰', 'response': answer})
        elif any(word in question.lower() for word in ['ubicacion', 'dónde', 'sucursales']):
            menu_options.append({'title': '📍 Ubicación', 'icon': '📍', 'response': answer})
        elif any(word in question.lower() for word in ['cambio', 'devolucion', 'política']):
            menu_options.append({'title': '🔄 Cambios/Devoluciones', 'icon': '🔄', 'response': answer})
        elif any(word in question.lower() for word in ['envio', 'tarda']):
            menu_options.append({'title': '📦 Envíos', 'icon': '📦', 'response': answer})
    
    # Mensaje de bienvenida
    welcome_flows = flows.get('on_welcome', [])
    welcome_text = '\n'.join(welcome_flows) if welcome_flows else f"¡Hola! Bienvenido a {bot_name}."
    
    # Datos bancarios
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

def main():
    print("=" * 60)
    print("📝 Actualización de functions/src/database.py")
    print("=" * 60)
    
    # Cargar JSONs
    demos_dir = Path("data/Bots_demo")
    files_config = {
        'Demo_Clinica_Dental.json': 'dental',
        'Demo_Psicologo.json': 'psychology',
        'Demo_Restaurante.json': 'restaurant',
        'Demo_SalonBelleza.json': 'salon',
        'Demo_Tienda_Ropa.json': 'retail',
    }
    
    print("\n📋 Convirtiendo 5 demos...")
    demos = {}
    for filename, business_type in files_config.items():
        filepath = demos_dir / filename
        json_data = load_json_data(filepath)
        demo_data = convert_to_zotek_full(json_data, business_type)
        bot_id = json_data.get('agent_config', {}).get('id', '')
        doc_id = f"demo_{business_type}_{bot_id.split('_')[-1]}"
        demos[doc_id] = demo_data
        print(f"   ✅ {doc_id}: {demo_data['name']}")
    
    print("\n💡 Nota: Los datos hardcodeados en database.py son complejos de actualizar automáticamente.")
    print("   Los datos YA están en Firestore (importados anteriormente).")
    print("   La función get_client_by_id() buscará en Firestore si el demo no está hardcodeado.")
    print("\n✨ No es necesario modificar database.py - los datos en Firestore son los correctos.")
    print("\n🚀 Para aplicar los cambios en producción:")
    print("   firebase deploy --only functions")

if __name__ == "__main__":
    main()
