"""
Script para importar los 5 Bots Demo desde archivos JSON a Firebase Firestore
Convierte el formato de los JSON al formato del SaaS Zotek con menús completos
"""

import json
import os
from pathlib import Path

# Configurar Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# Ruta al service account (descárgalo de Firebase Console > Project Settings > Service Accounts)
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
        print("💡 Asegúrate de tener el archivo service-account-key.json en functions/")
        return False

def get_icon_for_intent(intent_name, description, business_type):
    """Obtiene un icono emoji apropiado para el intent"""
    icon_map = {
        # Citas y reservas
        'agendar': '📅', 'cita': '📅', 'reserva': '📅', 'reservar': '📅', 'booking': '📅', 'sesion': '📅', 'sesión': '📅',
        # Emergencias
        'emergencia': '🚨', 'urgencia': '🚨', 'dolor': '🚨', 'urgente': '🚨', 'crisis': '🚨',
        # Menús y catálogos
        'menu': '📋', 'menú': '📋', 'catalogo': '👕', 'catálogo': '👕', 'productos': '🛍️', 'prenda': '👕',
        # Servicios
        'servicio': '✨', 'tratamiento': '💊', 'tratamientos': '💊', 'servicios': '✨', 'terapia': '🛋️',
        # Información
        'ubicacion': '📍', 'ubicación': '📍', 'horario': '⏰', 'horarios': '⏰', 'direccion': '📍', 'dirección': '📍',
        # Pagos
        'pago': '💳', 'pagos': '💳', 'precio': '💰', 'precios': '💰', 'costo': '💰', 'costos': '💰', 'seguro': '📄',
        # Domicilios
        'domicilio': '🛵', 'delivery': '🛵', 'envio': '📦', 'envío': '📦', 'pedido': '📝', 'orden': '📋',
        # Belleza
        'corte': '✂️', 'peinado': '💇', 'manicure': '💅', 'pedicure': '💅', 'facial': '💆', 'maquillaje': '🎨', 'tinte': '🎨',
        # Dental
        'dental': '🦷', 'limpieza': '✨', 'blanqueamiento': '✨', 'ortodoncia': '😁', 'diente': '🦷',
        # Restaurante
        'platillo': '🍽️', 'comida': '🍽️', 'mesa': '🍴', 'vegano': '🌱', 'vegetariano': '🌱',
        # Tienda
        'talla': '📏', 'tallas': '📏', 'devolucion': '🔄', 'devolución': '🔄', 'cambio': '🔄', 'devolver': '🔄',
        'promo': '🏷️', 'promocion': '🏷️', 'promoción': '🏷️', 'oferta': '🏷️', 'descuento': '🏷️',
        # Psicología
        'psicolog': '🧠', 'terapia': '🛋️', 'consulta': '👨‍⚕️', 'valoracion': '👨‍⚕️', 'valoración': '👨‍⚕️',
        # Visual
        'imagen': '📷', 'foto': '📷', 'visual': '👁️', 'buscar': '🔍',
        # Rastreo
        'rastrear': '📦', 'track': '📦', 'orden': '📋', 'pedido': '📦',
        # Asesoría
        'asesoria': '💁', 'asesoría': '💁', 'recomendacion': '💁', 'recomendación': '💁', 'estilo': '👔',
    }
    
    text_to_search = f"{intent_name} {description}".lower()
    
    for key, icon in icon_map.items():
        if key in text_to_search:
            return icon
    
    # Iconos por tipo de negocio
    business_icons = {
        'dental': '🦷',
        'restaurant': '🍽️',
        'psychology': '🧠',
        'salon': '💇',
        'retail': '👕',
    }
    
    return business_icons.get(business_type, '💬')

def get_title_for_intent(intent_name, business_type):
    """Obtiene un título legible para el intent"""
    title_map = {
        'agendar_cita': '📅 Agendar Cita',
        'agendar_sesion': '📅 Agendar Sesión',
        'hacer_reserva': '📅 Hacer Reserva',
        'reservar_mesa': '📅 Reservar Mesa',
        'pedir_domicilio': '🛵 Pedir Domicilio',
        'consultar_menu': '📋 Ver Menú',
        'reportar_emergencia': '🚨 Urgencia',
        'crisis_urgencia': '🚨 Crisis/Emergencia',
        'validar_seguro': '📄 Validar Seguro',
        'info_terapia': 'ℹ️ Info Terapia',
        'info_sesion': 'ℹ️ Información',
        'servicios': '✨ Servicios',
        'tratamientos': '💊 Tratamientos',
        'ver_catalogo': '👕 Ver Catálogo',
        'ver_productos': '🛍️ Productos',
        'buscar_prenda_imagen': '📷 Buscar con Foto',
        'asesoria_tallas': '📏 Guía de Tallas',
        'rastrear_pedido': '📦 Rastrear Pedido',
        'consultar_precios': '💰 Consultar Precios',
        'cancelar_cita': '🔄 Cancelar/Reagendar',
        'ubicacion': '📍 Ubicación',
        'horarios': '⏰ Horarios',
        'contacto': '📞 Contacto',
        'metodos_pago': '💳 Métodos de Pago',
        'garantia': '✅ Garantía',
        'tallas': '📏 Tallas',
        'devoluciones': '🔄 Cambios/Devoluciones',
        'promociones': '🏷️ Promociones',
        'citas_online': '📅 Citas en Línea',
        'terapias': '🛋️ Terapias',
        'valoracion': '👨‍⚕️ Valoración',
        'valoración': '👨‍⚕️ Valoración',
        'limpieza_dental': '🦷 Limpieza Dental',
        'blanqueamiento': '✨ Blanqueamiento',
        'ortodoncia': '😁 Ortodoncia',
        'ordenar_comida': '🍽️ Ordenar Comida',
        'menu_del_dia': '📋 Menú del Día',
        'opciones_veganas': '🌱 Opciones Veganas',
        'corte_peinado': '✂️ Corte y Peinado',
        'manicure_pedicure': '💅 Manicure/Pedicure',
        'tratamientos_faciales': '💆 Faciales',
        'tintes_color': '🎨 Tintes/Color',
        'maquillaje': '🎨 Maquillaje',
    }
    
    if intent_name in title_map:
        return title_map[intent_name]
    
    # Generar título automático
    title = intent_name.replace('_', ' ').title()
    return f"💬 {title}"

def convert_to_zotek_format(json_data, business_type):
    """
    Convierte el formato del JSON de ejemplo al formato del SaaS Zotek
    """
    agent_config = json_data.get('agent_config', {})
    llm_settings = json_data.get('llm_settings', {})
    flows = json_data.get('flows', {})
    knowledge_base = json_data.get('knowledge_base', {})
    intents = json_data.get('intents', [])
    capabilities = json_data.get('capabilities', [])
    
    # Extraer system prompt
    system_prompt = llm_settings.get('system_prompt', '')
    bot_name = agent_config.get('name', 'Bot Demo')
    bot_id = agent_config.get('id', 'demo_unknown')
    
    # ============================================
    # CONSTRUIR MENÚ PRINCIPAL
    # ============================================
    
    menu_options = []
    
    # Agregar opciones basadas en intents
    for intent in intents:
        intent_name = intent.get('name', '')
        description = intent.get('description', '')
        responses = intent.get('responses', [])
        
        icon = get_icon_for_intent(intent_name, description, business_type)
        title = get_title_for_intent(intent_name, business_type)
        
        # Si el título ya tiene icono, no agregar otro
        if len(title) > 0 and title[0] not in '📅🚨📋👕🛍️✨💊📍⏰📞💳💰📄🛵📦🔄🏷️🧠🛋️👨‍⚕️🦷😁🍽️🍴🌱✂️💇💅💆🎨📷🔍💁👔✅ℹ️':
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
    # AGREGAR OPCIONES GENÉRICAS COMPLEMENTARIAS
    # ============================================
    
    generic_options_config = {
        'dental': [
            {'title': '💰 Costos y Pagos', 'icon': '💰', 'response': 'Aceptamos tarjetas de crédito con 3, 6 y 9 meses sin intereses en tratamientos mayores a $3,000 MXN. También aceptamos seguros de gastos médicos.'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': 'Nuestro horario es:\nLunes a Viernes: 9:00 AM - 8:00 PM\nSábados: 9:00 AM - 3:00 PM\nDomingos: Solo urgencias'},
            {'title': '📍 Ubicación', 'icon': '📍', 'response': 'Estamos en Av. Reforma #123, Piso 5, Ciudad de México.\n🗺️ Ver ubicación: https://maps.google.com/sonrisa-perfecta'},
        ],
        'restaurant': [
            {'title': '🌱 Opciones Veganas', 'icon': '🌱', 'response': '¡Sí! Contamos con menú 100% plant-based: Ensalada Buddha Bowl ($140), Pasta Primavera vegana ($190), Burger de lentejas ($165). Todos certificados gluten-free.'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': '🕐 *Horarios:*\nMartes a Domingo: 1:00 PM - 11:00 PM\nLunes: Cerrado por descanso del personal'},
            {'title': '📍 Ubicación', 'icon': '📍', 'response': '📍 Av. Presidente Masaryk #456, Polanco, CDMX\n🅿️ Contamos con valet parking\n🐕 Somos pet-friendly en terraza'},
        ],
        'psychology': [
            {'title': '💰 Costos y Seguros', 'icon': '💰', 'response': '💵 *Inversión por sesión:*\nIndividual (50 min): $800\nPareja (60 min): $1,200\nFamiliar (75 min): $1,500\n\n📄 Aceptamos seguros: AXA, GNP, MetLife, Planes Personales'},
            {'title': '📍 Ubicación y Online', 'icon': '📍', 'response': '🏢 *Presencial:*\nAv. Insurgentes #789, Roma Norte, CDMX\n\n💻 *Online:*\nSesiones por videollamada disponibles para todo México y el extranjero.'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': '🕐 *Horarios de atención:*\nLunes a Viernes: 8:00 AM - 9:00 PM\nSábados: 9:00 AM - 3:00 PM'},
        ],
        'salon': [
            {'title': '📅 Agendar Cita', 'icon': '📅', 'response': '¡Con gusto! Para agendar necesito:\n📅 ¿Qué día te gustaría?\n⏰ ¿Mañana o tarde?\n💇 ¿Qué servicio te interesa?\n\n¡Te esperamos!'},
            {'title': '📍 Ubicación', 'icon': '📍', 'response': '📍 Plaza Las Américas, Local 45\nAv. Universidad #321, CDMX\n\n🅿️ Estacionamiento gratuito 2 horas\n📱 55-1234-5678'},
            {'title': '⏰ Horarios', 'icon': '⏰', 'response': '🕐 *Horarios:*\nMartes a Sábado: 10:00 AM - 8:00 PM\nDomingo: 10:00 AM - 3:00 PM\nLunes: Cerrado'},
        ],
        'retail': [
            {'title': '📏 Guía de Tallas', 'icon': '📏', 'response': '¡Te ayudo a encontrar tu talla perfecta! 📏\n\n👗 *Damas:*\nXS: Busto 80cm, Cintura 64cm\nS: Busto 84cm, Cintura 68cm\nM: Busto 88cm, Cintura 72cm\nL: Busto 92cm, Cintura 76cm'},
            {'title': '🔄 Cambios y Devoluciones', 'icon': '🔄', 'response': '¡Tu satisfacción es primero! 😊\n\n✅ Tienes 30 días para cambios o devoluciones\n✅ Con ticket de compra\n✅ Prenda sin usar y con etiquetas'},
            {'title': '🏷️ Promociones', 'icon': '🏷️', 'response': '¡Aprovecha nuestras ofertas! 🎉\n\n🔥 *Esta semana:*\n- 20% en segunda prenda\n- 30% en selección de outlet\n- Envío gratis en compras +$1,500'},
        ],
    }
    
    # Agregar opciones genéricas si hay menos de 6 opciones
    if len(menu_options) < 6:
        generic_options = generic_options_config.get(business_type, [])
        existing_titles = [opt['title'].split()[-1] if len(opt['title'].split()) > 1 else opt['title'] for opt in menu_options]
        
        for opt in generic_options:
            # Verificar que no exista ya una opción similar
            title_word = opt['title'].split()[-1]
            if not any(title_word in t for t in existing_titles):
                menu_options.append(opt)
    
    # ============================================
    # CONSTRUIR MENSAJE DE BIENVENIDA
    # ============================================
    
    welcome_flows = flows.get('on_welcome', [])
    if welcome_flows:
        welcome_text = '\n'.join(welcome_flows)
    else:
        welcome_text = f"¡Hola! Bienvenido a {bot_name}. ¿En qué puedo ayudarte hoy?"
    
    menu_json = {
        'text': welcome_text,
        'options': menu_options,
        'fallback_text': f"No entendí tu solicitud. Por favor selecciona una opción del menú o sé más específico."
    }
    
    # ============================================
    # DATOS BANCARIOS Y DE CONTACTO FICTICIOS
    # ============================================
    
    bank_data = {
        'dental': {'bank': 'BBVA', 'clabe': '012180012345678901'},
        'restaurant': {'bank': 'Santander', 'clabe': '014180098765432109'},
        'psychology': {'bank': 'Banorte', 'clabe': '072180056789012345'},
        'salon': {'bank': 'HSBC', 'clabe': '021180067890123456'},
        'retail': {'bank': 'Scotiabank', 'clabe': '044180034567890123'},
    }
    
    bank_info = bank_data.get(business_type, {'bank': 'BBVA', 'clabe': '012180011111111111'})
    
    # Generar phone_number_id único
    phone_id_map = {
        'dental': 'demo_dental_sonrisa',
        'restaurant': 'demo_restaurant_mesa',
        'psychology': 'demo_psychology_mente',
        'salon': 'demo_salon_glamour',
        'retail': 'demo_retail_style',
    }
    
    phone_number_id = phone_id_map.get(business_type, f'demo_{business_type}')
    
    # ============================================
    # CONSTRUIR DATOS FINALES DEL CLIENTE
    # ============================================
    
    client_data = {
        'name': f"🤖 Demo {bot_name}",
        'phone_number_id': phone_number_id,
        'email': f"{business_type}@demo.zotek.ia",
        'phone': f"52155000000{hash(bot_id) % 1000:03d}",
        'system_instruction': system_prompt,
        'gemini_prompt': f"Eres el asistente virtual experto de {bot_name}. {system_prompt}",
        'response_type': 'text',
        'calendly_url': f"https://calendly.com/{business_type}-demo" if business_type in ['dental', 'restaurant', 'psychology'] else '',
        'bank_name': bank_info['bank'],
        'clabe': bank_info['clabe'],
        'beneficiary_name': f"{bot_name} Demo SA de CV",
        'menu_json': menu_json,
        'created_at': '2026-03-13 00:00:00',
        'whatsapp_token': '',
        'verify_token': f'demo_token_{business_type}',
    }
    
    return client_data

def import_demo_to_firestore(client_data, doc_id):
    """
    Importa un demo a Firestore si no existe
    """
    db = firestore.client()
    
    # Verificar si ya existe
    doc_ref = db.collection('clients').document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        print(f"⚠️  '{doc_id}' ya existe - Saltando")
        return False
    
    # Crear documento
    doc_ref.set(client_data)
    print(f"✅ '{doc_id}' importado: {client_data['name']}")
    return True

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 Importación de 5 Bots Demo a Firebase Firestore")
    print("=" * 60)
    
    # Inicializar Firebase
    if not initialize_firebase():
        print("\n💡 Para obtener el service-account-key.json:")
        print("   1. Ve a https://console.firebase.google.com")
        print("   2. Selecciona tu proyecto: zotek-ia")
        print("   3. Ve a Project Settings > Service Accounts")
        print("   4. Click en 'Generate new private key'")
        print("   5. Guarda el archivo como: functions/service-account-key.json")
        return
    
    # Ruta a los archivos JSON
    base_dir = Path(__file__).parent
    demos_dir = base_dir / "data" / "Bots_demo"
    
    if not demos_dir.exists():
        print(f"❌ No se encontró el directorio: {demos_dir}")
        return
    
    # Mapeo de archivos a tipos de negocio
    files_config = {
        'Demo_Clinica_Dental.json': 'dental',
        'Demo_Psicologo.json': 'psychology',
        'Demo_Restaurante.json': 'restaurant',
        'Demo_SalonBelleza.json': 'salon',
        'Demo_Tienda_Ropa.json': 'retail',
    }
    
    print(f"\n📁 Procesando archivos en: {demos_dir}")
    print("-" * 60)
    
    # Procesar cada archivo
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    for filename, business_type in files_config.items():
        filepath = demos_dir / filename
        print(f"\n📄 Procesando: {filename}")
        
        if not filepath.exists():
            print(f"   ❌ Archivo no encontrado")
            error_count += 1
            continue
        
        try:
            # Leer JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extraer bot_id del JSON
            bot_id = json_data.get('agent_config', {}).get('id', '')
            if not bot_id:
                bot_id = filepath.stem.lower().replace('demo_', 'bot_')
            
            # Convertir al formato Zotek
            client_data = convert_to_zotek_format(json_data, business_type)
            
            # Generar ID único para Firestore
            doc_id = f"demo_{business_type}_{bot_id.split('_')[-1]}"
            
            # Importar a Firestore
            if import_demo_to_firestore(client_data, doc_id):
                imported_count += 1
            else:
                skipped_count += 1
            
            # Mostrar resumen del menú
            menu = client_data['menu_json']
            print(f"   📋 Menú: {len(menu['options'])} opciones")
            for opt in menu['options'][:3]:
                print(f"      {opt['title']}: {opt['response'][:50]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 Resumen de Importación")
    print("=" * 60)
    print(f"✅ Importados exitosamente: {imported_count}")
    print(f"⚠️  Saltados (ya existían): {skipped_count}")
    print(f"❌ Errores: {error_count}")
    print(f"📁 Total procesados: {imported_count + skipped_count + error_count}")
    print("=" * 60)
    
    if imported_count > 0:
        print("\n✨ ¡Importación completada exitosamente!")
        print("\n💡 Los nuevos demos estarán disponibles en:")
        print("   https://zotek-ia.web.app/admin-control")
        print("\n🔍 Para verificar:")
        print("   1. Ve a Firebase Console > Firestore Database")
        print("   2. Busca la colección 'clients'")
        print("   3. Deberías ver los 5 nuevos documentos demo")
    elif skipped_count > 0:
        print("\nℹ️  No se crearon nuevos demos (todos ya existían)")
        print("   Para reimportar, elimina los documentos existentes primero")
    else:
        print("\n❌ No se pudo completar la importación")

if __name__ == "__main__":
    main()
