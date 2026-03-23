"""
Script para generar datos de Bots Demo en formato Firebase Firestore
Este script genera un archivo JSON con los datos listos para importar
o puede usarse como referencia para creación manual en Firebase Console.

Los 5 bots se basan en los archivos JSON de ejemplo en data/Bots_demo/
"""

import json
from pathlib import Path

def load_json_file(filepath):
    """Carga un archivo JSON"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {filepath}: {e}")
        return None

def convert_to_zotek_format(json_data, bot_id, demo_name):
    """
    Convierte el formato del JSON de ejemplo al formato del SaaS Zotek
    Con menús, submenús y iconos apropiados
    """
    agent_config = json_data.get('agent_config', {})
    llm_settings = json_data.get('llm_settings', {})
    flows = json_data.get('flows', {})
    knowledge_base = json_data.get('knowledge_base', {})
    intents = json_data.get('intents', [])
    capabilities = json_data.get('capabilities', [])
    
    # Extraer system prompt
    system_prompt = llm_settings.get('system_prompt', '')
    
    # ============================================
    # CONSTRUIR MENÚ PRINCIPAL CON SUBMENÚS
    # ============================================
    
    # Mapeo de iconos por tipo de negocio/intent
    icon_map = {
        # Citas y reservas
        'agendar': '📅', 'cita': '📅', 'reserva': '📅', 'reservar': '📅', 'booking': '📅',
        # Emergencias
        'emergencia': '🚨', 'urgencia': '🚨', 'dolor': '🚨', 'urgente': '🚨',
        # Menús y catálogos
        'menu': '📋', 'menú': '📋', 'catalogo': '👕', 'catálogo': '👕', 'productos': '🛍️',
        # Servicios
        'servicio': '✨', 'tratamiento': '💊', 'tratamientos': '💊', 'servicios': '✨',
        # Información
        'ubicacion': '📍', 'ubicación': '📍', 'horario': '⏰', 'horarios': '⏰',
        'direccion': '📍', 'dirección': '📍', 'contacto': '📞',
        # Pagos
        'pago': '💳', 'pagos': '💳', 'precio': '💰', 'precios': '💰', 'costo': '💰',
        'seguro': '📄', 'garantia': '✅', 'garantía': '✅',
        # Domicilios
        'domicilio': '🛵', 'delivery': '🛵', 'envio': '📦', 'envío': '📦',
        # Belleza y cuidado
        'corte': '✂️', 'peinado': '💇', 'manicure': '💅', 'facial': '💆',
        # Psicología
        'terapia': '🧠', 'sesion': '🛋️', 'sesión': '🛋️', 'consulta': '👨‍⚕️',
        # Dental
        'dental': '🦷', 'limpieza': '✨', 'blanqueamiento': '✨', 'ortodoncia': '😁',
        # Restaurante
        'platillo': '🍽️', 'orden': '📝', 'pedido': '📝', 'mesa': '🍴',
        # Tienda
        'talla': '📏', 'tallas': '📏', 'devolucion': '🔄', 'devolución': '🔄', 'cambio': '🔄',
        'promo': '🏷️', 'promocion': '🏷️', 'promoción': '🏷️', 'oferta': '🏷️',
    }
    
    def get_icon_for_text(text):
        """Obtiene un icono basado en el texto"""
        text_lower = text.lower()
        for key, icon in icon_map.items():
            if key in text_lower:
                return icon
        return '💬'  # Default
    
    def get_title_for_intent(intent_name):
        """Obtiene un título legible para el intent"""
        title_map = {
            'agendar_cita': '📅 Agendar Cita',
            'hacer_reserva': '📅 Hacer Reserva',
            'pedir_domicilio': '🛵 Pedir Domicilio',
            'consultar_menu': '📋 Ver Menú',
            'reportar_emergencia': '🚨 Urgencia',
            'validar_seguro': '📄 Validar Seguro',
            'ver_servicios': '✨ Nuestros Servicios',
            'ver_catalogo': '👕 Ver Catálogo',
            'ver_productos': '🛍️ Productos',
            'tratamientos': '💊 Tratamientos',
            'promociones': '🏷️ Promociones',
            'ubicacion': '📍 Ubicación',
            'horarios': '⏰ Horarios',
            'contacto': '📞 Contacto',
            'metodos_pago': '💳 Métodos de Pago',
            'garantia': '✅ Garantía',
            'tallas': '📏 Guía de Tallas',
            'devoluciones': '🔄 Devoluciones',
            'citas_online': '📅 Citas en Línea',
            'terapias': '🧠 Terapias',
            'valoracion': '👨‍⚕️ Valoración Gratis',
            'limpieza_dental': '🦷 Limpieza Dental',
            'blanqueamiento': '✨ Blanqueamiento',
            'ortodoncia': '😁 Ortodoncia',
            'reservar_mesa': '📅 Reservar Mesa',
            'ordenar_comida': '🍽️ Ordenar Comida',
            'menu_del_dia': '📋 Menú del Día',
            'corte_peinado': '✂️ Corte y Peinado',
            'manicure_pedicure': '💅 Manicure',
            'tratamientos_faciales': '💆 Facial',
            'tintes_color': '🎨 Tintes',
        }
        
        if intent_name in title_map:
            return title_map[intent_name]
        
        # Generar título automático
        return intent_name.replace('_', ' ').title()
    
    # Construir opciones del menú principal
    menu_options = []
    
    # Agregar opciones basadas en intents
    for intent in intents:
        intent_name = intent.get('name', '')
        description = intent.get('description', '')
        responses = intent.get('responses', [])
        
        icon = get_icon_for_text(intent_name + ' ' + description)
        title = get_title_for_intent(intent_name)
        
        # Si el título ya tiene icono, no agregar otro
        if title[0] not in icon_map.values():
            title = f"{icon} {title}"
        
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
    
    # ============================================
    # AGREGAR OPCIONES GENÉRICAS (si faltan)
    # ============================================
    
    generic_options = {
        '📍 Ubicación': '📍',
        '⏰ Horarios': '⏰',
        '💳 Métodos de Pago': '💳',
        '📞 Contacto': '📞',
        '🏷️ Promociones': '🏷️',
    }
    
    # Agregar solo las que no existan
    existing_titles = [opt['title'] for opt in menu_options]
    for title, icon in generic_options.items():
        if not any(title in t for t in existing_titles):
            menu_options.append({
                'title': title,
                'icon': icon,
                'response': f"Información sobre {title.lower()}."
            })
    
    # ============================================
    # CONSTRUIR MENÚ CON JERARQUÍA (SUBMENÚS)
    # ============================================
    
    # Detectar tipo de negocio
    business_type = 'general'
    all_text = json.dumps(json_data).lower()
    
    if 'dental' in all_text or 'sonrisa' in all_text:
        business_type = 'dental'
    elif 'restaurante' in all_text or 'mesa' in all_text or 'comida' in all_text:
        business_type = 'restaurant'
    elif 'psicolog' in all_text or 'terapia' in all_text or 'mente' in all_text:
        business_type = 'psychology'
    elif 'salon' in all_text or 'belleza' in all_text or 'corte' in all_text:
        business_type = 'salon'
    elif 'tienda' in all_text or 'ropa' in all_text:
        business_type = 'retail'
    
    # Crear estructura con submenús si hay muchas opciones
    if len(menu_options) > 6:
        # Agrupar opciones en categorías
        categorized_menu = {
            'text': '',
            'options': [],
            'fallback_text': ''
        }
        
        # Categoría principal basada en negocio
        categories = {
            'dental': {
                '🦷 Servicios': ['🦷 Limpieza', '✨ Blanqueamiento', '😁 Ortodoncia', '💊 Tratamientos'],
                '📅 Citas': ['📅 Agendar', '👨‍⚕️ Valoración'],
                'ℹ️ Información': ['⏰ Horarios', '📍 Ubicación', '💳 Pagos'],
            },
            'restaurant': {
                '🍽️ Menú': ['📋 Ver Menú', '🍴 Ordenar', '🛵 Domicilio'],
                '📅 Reservas': ['📅 Reservar Mesa'],
                'ℹ️ Información': ['⏰ Horarios', '📍 Ubicación', '💳 Pagos'],
            },
            'psychology': {
                '🧠 Servicios': ['🛋️ Terapias', '👨‍⚕️ Valoración', '📅 Citas'],
                'ℹ️ Información': ['⏰ Horarios', '📍 Ubicación', '💳 Pagos', '📄 Seguro'],
            },
            'salon': {
                '💇 Servicios': ['✂️ Corte', '💅 Manicure', '💆 Facial', '🎨 Tintes'],
                '📅 Citas': ['📅 Agendar Cita'],
                'ℹ️ Información': ['⏰ Horarios', '📍 Ubicación', '💳 Pagos'],
            },
            'retail': {
                '👕 Catálogo': ['🛍️ Productos', '📏 Tallas', '🏷️ Promociones'],
                '🔄 Servicio': ['🔄 Devoluciones', '✅ Garantía'],
                '💳 Compra': ['💳 Métodos de Pago', '📦 Envíos'],
            },
        }
        
        # Usar categorías predefinidas o generar dinámicamente
        if business_type in categories:
            categorized_menu['options'] = []
            for category_title, sub_items in categories[business_type].items():
                # Buscar opciones que coincidan
                matching_responses = []
                for opt in menu_options:
                    for sub in sub_items:
                        if sub.split()[-1].lower() in opt['title'].lower():
                            matching_responses.append(opt['response'])
                
                response = ' | '.join(matching_responses[:2]) if matching_responses else f"Opciones de {category_title.lower()}."
                
                categorized_menu['options'].append({
                    'title': category_title,
                    'icon': category_title.split()[0],
                    'response': response
                })
            
            # Agregar todas las opciones originales también
            categorized_menu['options'].extend(menu_options[:3])  # Primeras 3 opciones
            categorized_menu['fallback_text'] = "No entendí tu solicitud. Por favor selecciona una categoría o servicio del menú."
        else:
            categorized_menu = {
                'text': '',
                'options': menu_options,
                'fallback_text': "No entendí tu solicitud. Por favor selecciona una opción del menú."
            }
    else:
        categorized_menu = {
            'text': '',
            'options': menu_options,
            'fallback_text': "No entendí tu solicitud. Por favor selecciona una opción del menú."
        }
    
    # ============================================
    # CONSTRUIR MENSAJE DE BIENVENIDA
    # ============================================
    
    welcome_flows = flows.get('on_welcome', [])
    if welcome_flows:
        welcome_text = ' '.join(welcome_flows)
    else:
        bot_name = agent_config.get('name', 'nuestro servicio')
        welcome_text = f"¡Hola! Bienvenido a {bot_name}. ¿En qué puedo ayudarte hoy?"
    
    categorized_menu['text'] = welcome_text
    
    # ============================================
    # DATOS BANCARIOS FICTICIOS
    # ============================================
    
    bank_data = {
        'dental': {'bank': 'BBVA', 'clabe': '012180012345678901'},
        'restaurant': {'bank': 'Santander', 'clabe': '014180098765432109'},
        'psychology': {'bank': 'Banorte', 'clabe': '072180056789012345'},
        'salon': {'bank': 'HSBC', 'clabe': '021180067890123456'},
        'retail': {'bank': 'Scotiabank', 'clabe': '044180034567890123'},
    }
    
    bank_info = bank_data.get(business_type, {'bank': 'BBVA', 'clabe': '012180011111111111'})
    
    # ============================================
    # CONSTRUIR DATOS FINALES DEL CLIENTE
    # ============================================
    
    bot_name = agent_config.get('name', 'Bot Demo')
    
    client_data = {
        'name': f"🤖 Demo {bot_name}",
        'phone_number_id': f'demo_{business_type}_{bot_id}',
        'email': f"{business_type}@demo.zotek.ia",
        'phone': f"52155000000{hash(bot_id) % 1000:03d}",
        'system_instruction': system_prompt,
        'gemini_prompt': f"Eres el asistente virtual experto de {bot_name}. {system_prompt}",
        'response_type': 'text',
        'calendly_url': f"https://calendly.com/{business_type}-demo" if business_type != 'retail' else '',
        'bank_name': bank_info['bank'],
        'clabe': bank_info['clabe'],
        'beneficiary_name': f"{bot_name} Demo SA de CV",
        'menu_json': categorized_menu,
        'created_at': '2026-03-13 00:00:00',
        'whatsapp_token': '',
        'verify_token': f'demo_token_{business_type}',
    }
    
    return client_data

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 Generador de Bots Demo para Firebase Firestore")
    print("=" * 60)
    
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
    all_demos = []
    
    for json_file in json_files:
        print(f"\n📄 Procesando: {json_file.name}")
        
        try:
            # Leer JSON
            json_data = load_json_file(json_file)
            if not json_data:
                continue
            
            # Extraer bot_id del JSON o del nombre del archivo
            bot_id = json_data.get('agent_config', {}).get('id', '')
            if not bot_id:
                bot_id = json_file.stem.lower().replace('demo_', 'bot_')
            
            # Extraer nombre descriptivo
            demo_name = json_data.get('agent_config', {}).get('name', bot_id)
            
            # Convertir al formato Zotek
            client_data = convert_to_zotek_format(json_data, bot_id, demo_name)
            
            # Agregar ID único para Firestore
            demo_entry = {
                'id': bot_id,
                'firestore_data': client_data
            }
            
            all_demos.append(demo_entry)
            
            print(f"   ✅ Convertido: {client_data['name']}")
            print(f"   📋 Opciones de menú: {len(client_data['menu_json']['options'])}")
            
        except Exception as e:
            print(f"❌ Error procesando {json_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # ============================================
    # GUARDAR RESULTADOS
    # ============================================
    
    output_file = base_dir / "data" / "demos_firestore_export.json"
    
    export_data = {
        'generated_at': '2026-03-13',
        'total_demos': len(all_demos),
        'demos': all_demos
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("📊 Resumen")
    print("=" * 60)
    print(f"✅ Demos procesados: {len(all_demos)}")
    print(f"💾 Archivo guardado: {output_file}")
    print("=" * 60)
    
    # ============================================
    # MOSTRAR EJEMPLO DE CADA DEMO
    # ============================================
    
    print("\n" + "=" * 60)
    print("📋 Vista Previa de Demos")
    print("=" * 60)
    
    for demo in all_demos:
        data = demo['firestore_data']
        print(f"\n🔹 {data['name']}")
        print(f"   ID: {demo['id']}")
        print(f"   Phone Number ID: {data['phone_number_id']}")
        print(f"   Email: {data['email']}")
        print(f"   Menú: {len(data['menu_json']['options'])} opciones")
        
        # Mostrar primeras 3 opciones del menú
        print(f"   Opciones:")
        for opt in data['menu_json']['options'][:3]:
            print(f"      {opt['title']}: {opt['response'][:50]}...")
    
    print("\n" + "=" * 60)
    print("💡 Para importar estos demos a Firebase:")
    print("=" * 60)
    print("""
    Opción 1 - Usando Firebase Console:
    1. Ve a https://console.firebase.google.com
    2. Selecciona tu proyecto: zotek-ia
    3. Ve a Firestore Database
    4. Crea una colección 'clients' (si no existe)
    5. Para cada demo, crea un documento con:
       - ID del documento: el valor de 'id'
       - Campos: copia los valores de 'firestore_data'
    
    Opción 2 - Usando script con Admin SDK:
    1. Asegúrate de tener el service-account-key.json
    2. Ejecuta: python import_demos_from_json.py
    
    Opción 3 - Usando Firebase CLI:
    1. firebase firestore:import data/demos_firestore_export.json
    """)
    print("=" * 60)

if __name__ == "__main__":
    main()
