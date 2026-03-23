import json
import os
from pathlib import Path
import psycopg2
from src.database import get_connection

def convert_to_zotek_format(json_data, file_name=""):
    agent_config = json_data.get('agent_config', {})
    llm_settings = json_data.get('llm_settings', {})
    flows = json_data.get('flows', {})
    intents = json_data.get('intents', [])
    
    system_prompt = llm_settings.get('system_prompt', '')
    
    menu_options = []
    
    for intent in intents:
        intent_name = intent.get('name', '')
        description = intent.get('description', '')
        responses = intent.get('responses', [])
        
        icon_map = {
            'agendar_cita': '📅',
            'hacer_reserva': '📅',
            'pedir_domicilio': '🛵',
            'consultar_menu': '📋',
            'reportar_emergencia': '🚨',
            'validar_seguro': '📄',
            'urgencia': '🚨',
            'servicios': '✨',
            'catalogo': '👕',
            'tallas': '📏',
            'devoluciones': '🔄',
            'tratamientos': '💊',
            'productos': '🧴',
            'reservas': '📅',
            'menu': '🍽️',
        }
        
        icon = '💬'
        for key, emoji in icon_map.items():
            if key in intent_name.lower() or key in description.lower():
                icon = emoji
                break
        
        title_map = {
            'agendar_cita': 'Agendar Cita',
            'hacer_reserva': 'Hacer Reserva',
            'pedir_domicilio': 'Pedir Domicilio',
            'consultar_menu': 'Ver Menú',
            'reportar_emergencia': '🚨 Urgencia',
            'validar_seguro': 'Validar Seguro',
            'servicios': 'Nuestros Servicios',
            'catalogo': 'Ver Catálogo',
            'tratamientos': 'Tratamientos',
            'productos': 'Productos',
        }
        
        title = title_map.get(intent_name, intent_name.replace('_', ' ').title())
        
        if responses:
            response = responses[0]
        else:
            response = f"Para {description.lower()}, por favor proporciona más detalles."
        
        menu_options.append({
            'title': title,
            'icon': icon,
            'response': response
        })
    
    if len(menu_options) < 3:
        generic_options = [
            {'title': '📍 Ubicación', 'icon': '📍', 'response': 'Visítanos en nuestra ubicación principal.'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': 'Nuestro horario es de Lunes a Sábado de 9:00 AM a 8:00 PM'},
            {'title': '💳 Métodos de Pago', 'icon': '💳', 'response': 'Aceptamos efectivo, tarjetas de crédito/débito y transferencias.'},
        ]
        for opt in generic_options:
            if len(menu_options) < 5:
                if not any(opt['title'].split()[1] in m['title'] for m in menu_options):
                    menu_options.append(opt)
    
    welcome_flows = flows.get('on_welcome', [])
    if welcome_flows:
        welcome_text = ' '.join(welcome_flows)
    else:
        welcome_text = f"¡Hola! Bienvenido a {agent_config.get('name', 'nuestro servicio')}. ¿En qué puedo ayudarte hoy?"
    
    fallback_text = "No entendí tu solicitud. Por favor selecciona una de las opciones del menú o sé más específico."
    
    menu_json = {
        'text': welcome_text,
        'options': menu_options,
        'fallback_text': fallback_text
    }
    
    bot_name = agent_config.get('name', 'Bot Demo')
    
    file_name = file_name.lower() if file_name else bot_name.lower()
    
    business_type = 'general'
    if 'dental' in file_name or 'clinica' in file_name:
        business_type = 'dental'
    elif 'restaurante' in file_name:
        business_type = 'restaurant'
    elif 'psicologo' in file_name:
        business_type = 'psychology'
    elif 'salon' in file_name or 'belleza' in file_name:
        business_type = 'salon'
    elif 'tienda' in file_name or 'ropa' in file_name:
        business_type = 'retail'
    
    phone_id_map = {
        'bot_dental_001': 'demo_dental_sonrisa',
        'bot_restaurante_001': 'demo_restaurante_mesa',
        'bot_psicologo_001': 'demo_psicologo_mente',
        'bot_salon_001': 'demo_salon_belleza',
        'bot_tienda_001': 'demo_tienda_estilo',
    }
    
    # generate based on business type to be safe since bot_id was removed
    phone_number_id = f'demo_{business_type}'
    
    bank_data = {
        'dental': {'bank': 'BBVA', 'clabe': '012180012345678901'},
        'restaurant': {'bank': 'Santander', 'clabe': '014180098765432109'},
        'psychology': {'bank': 'Banorte', 'clabe': '072180056789012345'},
        'salon': {'bank': 'HSBC', 'clabe': '021180067890123456'},
        'retail': {'bank': 'Scotiabank', 'clabe': '044180034567890123'},
    }
    
    bank_info = bank_data.get(business_type, {'bank': 'BBVA', 'clabe': '012180011111111111'})
    
    client_data = {
        'name': f"🤖 Demo {bot_name}",
        'phone_number_id': phone_number_id,
        'email': f"{business_type}@demo.zotek.ia",
        'phone': f"52155000000{hash(phone_number_id) % 1000:03d}",
        'system_instruction': system_prompt,
        'gemini_prompt': f"Eres el asistente virtual experto de {bot_name}. {system_prompt}",
        'response_type': 'text',
        'calendly_url': f"https://calendly.com/{business_type}-demo" if business_type != 'retail' else '',
        'bank_name': bank_info['bank'],
        'clabe': bank_info['clabe'],
        'beneficiary_name': f"{bot_name} Demo SA de CV",
        'menu_json': json.dumps(menu_json),
        'whatsapp_token': 'DEMO',
        'verify_token': f'demo_token_{business_type}',
    }
    
    return client_data, business_type

def main():
    print("=" * 60)
    print("🚀 Importación de Bots Demo a PostgreSQL")
    print("=" * 60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    print("🗑️ Eliminando clientes demo existentes...")
    cursor.execute("DELETE FROM clients WHERE phone_number_id LIKE 'demo_%'")
    conn.commit()
    print("✅ Clientes eliminados.")
    
    base_dir = Path(__file__).parent
    demos_dir = base_dir / "data" / "Bots_demo"
    json_files = list(demos_dir.glob("*.json"))
    
    print(f"\n📁 Se encontraron {len(json_files)} archivos JSON")
    
    created_count = 0
    for json_file in json_files:
        print(f"📄 Procesando: {json_file.name}")
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            
        client_data, _ = convert_to_zotek_format(json_data, json_file.name)
        
        cursor.execute('''
            INSERT INTO clients (
                name, whatsapp_token, phone_number_id, verify_token, system_instruction,
                bank_name, clabe, beneficiary_name, menu_json, email, calendly_url
            ) VALUES (
                %(name)s, %(whatsapp_token)s, %(phone_number_id)s, %(verify_token)s, 
                %(system_instruction)s, %(bank_name)s, %(clabe)s, %(beneficiary_name)s, 
                %(menu_json)s, %(email)s, %(calendly_url)s
            )
        ''', client_data)
        created_count += 1
        print(f"✅ Demo insertado: {client_data['name']}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"🚀 Finalizado: Se insertaron {created_count} bots de demo.")

if __name__ == "__main__":
    main()
