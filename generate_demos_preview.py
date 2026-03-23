"""
Script para generar los datos de los 5 Demos en formato JSON
Listo para revisar o importar manualmente a Firebase
"""

import json
from pathlib import Path

def get_icon_for_intent(intent_name, description, business_type):
    """Obtiene un icono emoji apropiado para el intent"""
    icon_map = {
        'agendar': '📅', 'cita': '📅', 'reserva': '📅', 'sesion': '📅', 'sesión': '📅',
        'emergencia': '🚨', 'urgencia': '🚨', 'crisis': '🚨',
        'menu': '📋', 'menú': '📋', 'catalogo': '👕', 'catalogo': '👕',
        'servicio': '✨', 'tratamiento': '💊', 'terapia': '🛋️',
        'ubicacion': '📍', 'ubicación': '📍', 'horario': '⏰', 'horarios': '⏰',
        'pago': '💳', 'pagos': '💳', 'precio': '💰', 'costo': '💰', 'seguro': '📄',
        'domicilio': '🛵', 'delivery': '🛵', 'envio': '📦', 'pedido': '📝',
        'corte': '✂️', 'manicure': '💅', 'facial': '💆', 'maquillaje': '🎨',
        'dental': '🦷', 'limpieza': '✨', 'ortodoncia': '😁',
        'comida': '🍽️', 'mesa': '🍴', 'vegano': '🌱',
        'talla': '📏', 'devolucion': '🔄', 'devolución': '🔄', 'promo': '🏷️',
        'psicolog': '🧠', 'consulta': '👨‍⚕️', 'valoracion': '👨‍⚕️',
        'imagen': '📷', 'foto': '📷', 'buscar': '🔍', 'rastrear': '📦',
        'asesoria': '💁', 'estilo': '👔',
    }
    
    text_to_search = f"{intent_name} {description}".lower()
    for key, icon in icon_map.items():
        if key in text_to_search:
            return icon
    
    business_icons = {
        'dental': '🦷', 'restaurant': '🍽️', 'psychology': '🧠',
        'salon': '💇', 'retail': '👕',
    }
    return business_icons.get(business_type, '💬')

def get_title_for_intent(intent_name, business_type):
    """Obtiene un título legible para el intent"""
    title_map = {
        'agendar_cita': 'Agendar Cita', 'agendar_sesion': 'Agendar Sesión',
        'reportar_emergencia': '🚨 Urgencia', 'crisis_urgencia': '🚨 Crisis/Emergencia',
        'validar_seguro': 'Validar Seguro', 'info_terapia': 'ℹ️ Info Terapia',
        'buscar_prenda_imagen': '📷 Buscar con Foto', 'asesoria_tallas': '📏 Guía de Tallas',
        'rastrear_pedido': '📦 Rastrear Pedido', 'consultar_precios': '💰 Precios',
        'cancelar_cita': '🔄 Cancelar/Reagendar',
    }
    
    if intent_name in title_map:
        return title_map[intent_name]
    
    return intent_name.replace('_', ' ').title()

def convert_to_zotek_format(json_data, business_type):
    """Convierte el formato del JSON al formato Zotek"""
    
    agent_config = json_data.get('agent_config', {})
    llm_settings = json_data.get('llm_settings', {})
    flows = json_data.get('flows', {})
    intents = json_data.get('intents', [])
    
    system_prompt = llm_settings.get('system_prompt', '')
    bot_name = agent_config.get('name', 'Bot Demo')
    bot_id = agent_config.get('id', 'demo_unknown')
    
    # Construir menú
    menu_options = []
    
    for intent in intents:
        intent_name = intent.get('name', '')
        description = intent.get('description', '')
        responses = intent.get('responses', [])
        
        icon = get_icon_for_intent(intent_name, description, business_type)
        title = get_title_for_intent(intent_name, business_type)
        
        if len(title) > 0 and title[0] not in '📅🚨📋👕🛍️✨💊📍⏰📞💳💰📄🛵📦🔄🏷️🧠🛋️👨‍⚕️🦷😁🍽️🌱✂️💇💅💆🎨📷🔍💁👔✅ℹ️':
            title = f"{icon} {title}"
        
        response = responses[0] if responses else f"Para {description.lower()}, proporciona más detalles."
        
        menu_options.append({
            'title': title,
            'icon': icon,
            'response': response
        })
    
    # Agregar opciones genéricas
    generic_options = {
        'dental': [
            {'title': '💰 Costos', 'icon': '💰', 'response': 'Aceptamos tarjetas con MSI y seguros de gastos médicos.'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': 'Lun-Vie: 9AM-8PM, Sáb: 9AM-3PM, Dom: Solo urgencias'},
            {'title': '📍 Ubicación', 'icon': '📍', 'response': 'Av. Reforma #123, CDMX'},
        ],
        'restaurant': [
            {'title': '🌱 Opciones Veganas', 'icon': '🌱', 'response': 'Menú 100% plant-based disponible'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': 'Mar-Dom: 1PM-11PM, Lun: Cerrado'},
            {'title': '📍 Ubicación', 'icon': '📍', 'response': 'Polanco, CDMX. Pet-friendly'},
        ],
        'psychology': [
            {'title': '💰 Costos', 'icon': '💰', 'response': 'Individual: $800, Pareja: $1,200, Familiar: $1,500'},
            {'title': '📍 Online', 'icon': '💻', 'response': 'Sesiones por videollamada disponibles'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': 'Lun-Vie: 8AM-9PM, Sáb: 9AM-3PM'},
        ],
        'salon': [
            {'title': '📅 Agendar', 'icon': '📅', 'response': '¿Qué día y servicio te interesa?'},
            {'title': '📍 Ubicación', 'icon': '📍', 'response': 'Plaza Las Américas, CDMX'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': 'Mar-Sáb: 10AM-8PM, Dom: 10AM-3PM'},
        ],
        'retail': [
            {'title': '📏 Tallas', 'icon': '📏', 'response': 'XS, S, M, L, XL. ¿Necesitas ayuda?'},
            {'title': '🔄 Devoluciones', 'icon': '🔄', 'response': '30 días con ticket y etiquetas'},
            {'title': '🏷️ Promociones', 'icon': '🏷️', 'response': '20% en 2da prenda, envío gratis +$1,500'},
        ],
    }
    
    if len(menu_options) < 6:
        for opt in generic_options.get(business_type, []):
            if not any(opt['title'].split()[0] in m['title'] for m in menu_options):
                menu_options.append(opt)
    
    # Mensaje de bienvenida
    welcome_flows = flows.get('on_welcome', [])
    welcome_text = '\n'.join(welcome_flows) if welcome_flows else f"¡Hola! Bienvenido a {bot_name}."
    
    # Datos bancarios
    bank_data = {
        'dental': {'bank': 'BBVA', 'clabe': '012180012345678901'},
        'restaurant': {'bank': 'Santander', 'clabe': '014180098765432109'},
        'psychology': {'bank': 'Banorte', 'clabe': '072180056789012345'},
        'salon': {'bank': 'HSBC', 'clabe': '021180067890123456'},
        'retail': {'bank': 'Scotiabank', 'clabe': '044180034567890123'},
    }
    
    bank_info = bank_data.get(business_type, {'bank': 'BBVA', 'clabe': '012180011111111111'})
    
    phone_id_map = {
        'dental': 'demo_dental_001', 'restaurant': 'demo_restaurant_001',
        'psychology': 'demo_psychology_001', 'salon': 'demo_salon_001',
        'retail': 'demo_retail_001',
    }
    
    return {
        'name': f"🤖 Demo {bot_name}",
        'phone_number_id': phone_id_map.get(business_type, f'demo_{business_type}'),
        'email': f"{business_type}@demo.zotek.ia",
        'phone': f"52155000000{hash(bot_id) % 1000:03d}",
        'system_instruction': system_prompt,
        'gemini_prompt': f"Eres el asistente virtual experto de {bot_name}. {system_prompt}",
        'response_type': 'text',
        'calendly_url': f"https://calendly.com/{business_type}-demo" if business_type in ['dental', 'restaurant', 'psychology'] else '',
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
    print("📋 Generador de Datos para 5 Demos")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    demos_dir = base_dir / "data" / "Bots_demo"
    
    files_config = {
        'Demo_Clinica_Dental.json': 'dental',
        'Demo_Psicologo.json': 'psychology',
        'Demo_Restaurante.json': 'restaurant',
        'Demo_SalonBelleza.json': 'salon',
        'Demo_Tienda_Ropa.json': 'retail',
    }
    
    all_demos = []
    
    for filename, business_type in files_config.items():
        filepath = demos_dir / filename
        print(f"\n📄 Procesando: {filename}")
        
        if not filepath.exists():
            print(f"   ❌ No encontrado")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        bot_id = json_data.get('agent_config', {}).get('id', '')
        client_data = convert_to_zotek_format(json_data, business_type)
        
        doc_id = f"demo_{business_type}_{bot_id.split('_')[-1]}"
        
        demo_entry = {'id': doc_id, 'firestore_data': client_data}
        all_demos.append(demo_entry)
        
        print(f"   ✅ {client_data['name']}")
        print(f"   📋 Menú: {len(client_data['menu_json']['options'])} opciones")
    
    # Guardar resultado
    output_file = base_dir / "data" / "demos_convertidos.json"
    export_data = {
        'generated_at': '2026-03-13',
        'total_demos': len(all_demos),
        'demos': all_demos
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"✅ {len(all_demos)} demos generados")
    print(f"💾 Archivo: {output_file}")
    print("=" * 60)
    
    # Mostrar vista previa
    print("\n📋 Vista Previa:")
    for demo in all_demos:
        data = demo['firestore_data']
        print(f"\n🔹 {data['name']}")
        print(f"   ID: {demo['id']}")
        print(f"   Phone Number ID: {data['phone_number_id']}")
        print(f"   Menú: {len(data['menu_json']['options'])} opciones")
        for opt in data['menu_json']['options'][:3]:
            print(f"      {opt['title']}: {opt['response'][:50]}...")

if __name__ == "__main__":
    main()
