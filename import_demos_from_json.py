"""
Script para importar los 5 bots demo desde archivos JSON a Firebase Firestore
Convierte el formato de los JSON al formato del SaaS Zotek
"""

import json
import os
from pathlib import Path

# Configurar Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Firebase (ajusta la ruta a tu service account)
SERVICE_ACCOUNT_PATH = "functions/service-account-key.json"  # Ajusta esta ruta

def initialize_firebase():
    """Inicializa Firebase Admin SDK"""
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
        print("✅ Firebase inicializado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar Firebase: {e}")
        print("💡 Asegúrate de que el archivo service-account-key.json exista en functions/")
        return False

def convert_to_zotek_format(json_data):
    """
    Convierte el formato del JSON de ejemplo al formato del SaaS Zotek
    """
    agent_config = json_data.get('agent_config', {})
    llm_settings = json_data.get('llm_settings', {})
    flows = json_data.get('flows', {})
    knowledge_base = json_data.get('knowledge_base', {})
    intents = json_data.get('intents', [])
    
    # Extraer información del system prompt
    system_prompt = llm_settings.get('system_prompt', '')
    
    # Construir menú basado en intents y flows
    menu_options = []
    
    # Analizar intents para crear opciones de menú
    for intent in intents:
        intent_name = intent.get('name', '')
        description = intent.get('description', '')
        responses = intent.get('responses', [])
        
        # Asignar iconos basados en el tipo de intent
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
        
        # Buscar icono apropiado
        icon = '💬'  # Default
        for key, emoji in icon_map.items():
            if key in intent_name.lower() or key in description.lower():
                icon = emoji
                break
        
        # Crear título legible
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
        
        # Respuesta por defecto
        if responses:
            response = responses[0]
        else:
            response = f"Para {description.lower()}, por favor proporciona más detalles."
        
        menu_options.append({
            'title': title,
            'icon': icon,
            'response': response
        })
    
    # Agregar opciones genéricas si el menú es muy corto
    if len(menu_options) < 3:
        generic_options = [
            {'title': '📍 Ubicación', 'icon': '📍', 'response': 'Visítanos en nuestra ubicación principal.'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': 'Nuestro horario es de Lunes a Sábado de 9:00 AM a 8:00 PM'},
            {'title': '💳 Métodos de Pago', 'icon': '💳', 'response': 'Aceptamos efectivo, tarjetas de crédito/débito y transferencias.'},
        ]
        for opt in generic_options:
            if len(menu_options) < 5:
                # Verificar que no exista ya
                if not any(opt['title'].split()[1] in m['title'] for m in menu_options):
                    menu_options.append(opt)
    
    # Construir mensaje de bienvenida
    welcome_flows = flows.get('on_welcome', [])
    if welcome_flows:
        welcome_text = ' '.join(welcome_flows)
    else:
        welcome_text = f"¡Hola! Bienvenido a {agent_config.get('name', 'nuestro servicio')}. ¿En qué puedo ayudarte hoy?"
    
    # Construir fallback text
    fallback_text = "No entendí tu solicitud. Por favor selecciona una de las opciones del menú o sé más específico."
    
    # Construir menu_json en formato Zotek
    menu_json = {
        'text': welcome_text,
        'options': menu_options,
        'fallback_text': fallback_text
    }
    
    # Construir datos del cliente en formato Zotek
    bot_name = agent_config.get('name', 'Bot Demo')
    bot_id = agent_config.get('id', 'demo_unknown')
    
    # Extraer tipo de negocio del nombre del archivo o del bot
    business_type = 'general'
    if 'dental' in bot_name.lower() or 'dental' in json.dumps(json_data).lower():
        business_type = 'dental'
    elif 'restaurante' in bot_name.lower() or 'restaurante' in json.dumps(json_data).lower():
        business_type = 'restaurant'
    elif 'psicologo' in bot_name.lower() or 'psicolog' in json.dumps(json_data).lower():
        business_type = 'psychology'
    elif 'salon' in bot_name.lower() or 'belleza' in bot_name.lower():
        business_type = 'salon'
    elif 'tienda' in bot_name.lower() or 'ropa' in bot_name.lower():
        business_type = 'retail'
    
    # Generar phone_number_id único para demo
    phone_id_map = {
        'bot_dental_001': 'demo_dental_sonrisa',
        'bot_restaurante_001': 'demo_restaurante_mesa',
        'bot_psicologo_001': 'demo_psicologo_mente',
        'bot_salon_001': 'demo_salon_belleza',
        'bot_tienda_001': 'demo_tienda_estilo',
    }
    
    phone_number_id = phone_id_map.get(bot_id, f'demo_{business_type}')
    
    # Datos bancarios ficticios
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
        'menu_json': menu_json,
        'created_at': '2026-03-13 00:00:00',
        # Campos adicionales para compatibilidad
        'whatsapp_token': '',
        'verify_token': f'demo_token_{business_type}',
    }
    
    return client_data, bot_id

def create_demo_in_firestore(client_data, bot_id):
    """
    Crea o actualiza un cliente demo en Firestore
    """
    db = firestore.client()
    
    # Verificar si ya existe
    doc_ref = db.collection('clients').document(bot_id)
    doc = doc_ref.get()
    
    if doc.exists:
        print(f"⚠️  El demo '{bot_id}' YA existe en Firestore")
        return False
    
    # Crear el documento
    doc_ref.set(client_data)
    print(f"✅ Demo '{bot_id}' creado exitosamente: {client_data['name']}")
    return True

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 Importación de Bots Demo a Firebase Firestore")
    print("=" * 60)
    
    # Inicializar Firebase
    if not initialize_firebase():
        return
    
    # Ruta a los archivos JSON
    base_dir = Path(__file__).parent
    demos_dir = base_dir / "data" / "Bots_demo"
    
    if not demos_dir.exists():
        print(f"❌ No se encontró el directorio: {demos_dir}")
        return
    
    # Obtener todos los archivos JSON
    json_files = list(demos_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No se encontraron archivos JSON en {demos_dir}")
        return
    
    print(f"\n📁 Se encontraron {len(json_files)} archivos JSON")
    print("-" * 60)
    
    # Procesar cada archivo
    created_count = 0
    skipped_count = 0
    
    for json_file in json_files:
        print(f"\n📄 Procesando: {json_file.name}")
        
        try:
            # Leer JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Convertir al formato Zotek
            client_data, bot_id = convert_to_zotek_format(json_data)
            
            # Crear en Firestore
            if create_demo_in_firestore(client_data, bot_id):
                created_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"❌ Error procesando {json_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 Resumen de Importación")
    print("=" * 60)
    print(f"✅ Demos creados: {created_count}")
    print(f"⚠️  Demos saltados (ya existían): {skipped_count}")
    print(f"📁 Total archivos procesados: {len(json_files)}")
    print("=" * 60)
    
    if created_count > 0:
        print("\n✨ ¡Importación completada exitosamente!")
        print("\n💡 Los nuevos demos estarán disponibles en:")
        print("   https://zotek-ia.web.app/admin-control")
    else:
        print("\nℹ️  No se crearon nuevos demos (todos ya existían)")

if __name__ == "__main__":
    main()
