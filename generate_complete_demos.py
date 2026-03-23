"""
Script para generar los 5 Bots Demo completos para Firebase Firestore
Crea datos ficticios coherentes para cada tipo de negocio con menús detallados
"""

import json
from pathlib import Path

def generate_demos():
    """Genera los 5 demos completos"""
    
    demos = []
    
    # ============================================
    # DEMO 1: CLÍNICA DENTAL - SonrisaPerfecta IA
    # ============================================
    demo_dental = {
        'id': 'demo_dental_sonrisa',
        'firestore_data': {
            'name': '🦷 Demo Clínica Sonrisa Perfecta',
            'phone_number_id': 'demo_dental_001',
            'email': 'dental@demo.zotek.ia',
            'phone': '5215500000001',
            'system_instruction': 'Eres el asistente virtual de la clínica "Sonrisa Perfecta". Eres profesional, empático y claro. Tu principal función es agendar citas, hacer triage dental básico (identificar urgencias como dolor intenso o sangrado) y enviar recordatorios. NUNCA des diagnósticos médicos, sugiere siempre una valoración presencial.',
            'gemini_prompt': 'Eres el asistente virtual experto de Sonrisa Perfecta IA. Eres profesional, empático y claro. Tu principal función es agendar citas, hacer triage dental básico y enviar recordatorios. NUNCA des diagnósticos médicos.',
            'response_type': 'text',
            'calendly_url': 'https://calendly.com/dental-demo',
            'bank_name': 'BBVA',
            'clabe': '012180012345678901',
            'beneficiary_name': 'Sonrisa Perfecta Demo SA de CV',
            'menu_json': {
                'text': '¡Hola! Gracias por comunicarte con Clínica Sonrisa Perfecta 🦷.\nSoy tu asistente virtual. ¿En qué puedo ayudarte hoy?',
                'options': [
                    {
                        'title': '📅 Agendar Cita',
                        'icon': '📅',
                        'response': '¡Claro! Con gusto te ayudo a agendar una cita. ¿Es tu primera visita o ya eres paciente de la clínica?'
                    },
                    {
                        'title': '🚨 Urgencia Dental',
                        'icon': '🚨',
                        'response': 'Entiendo, esto parece ser una urgencia. Por favor, comunícate inmediatamente al número de emergencias 24/7: 555-0199 o acude a la clínica. ¿Deseas que notifique al doctor de guardia?'
                    },
                    {
                        'title': '🦷 Servicios',
                        'icon': '🦷',
                        'response': 'Ofrecemos: Limpieza dental ($800), Blanqueamiento ($2500), Ortodoncia (desde $3500), Implantes, Carillas, Endodoncias y más. ¿Te gustaría agendar una valoración?'
                    },
                    {
                        'title': '💰 Costos y Pagos',
                        'icon': '💰',
                        'response': 'Aceptamos tarjetas de crédito con 3, 6 y 9 meses sin intereses en tratamientos mayores a $3,000 MXN. También aceptamos seguros de gastos médicos.'
                    },
                    {
                        'title': '⏰ Horarios',
                        'icon': '⏰',
                        'response': 'Nuestro horario es:\nLunes a Viernes: 9:00 AM - 8:00 PM\nSábados: 9:00 AM - 3:00 PM\nDomingos: Solo urgencias'
                    },
                    {
                        'title': '📍 Ubicación',
                        'icon': '📍',
                        'response': 'Estamos en Av. Reforma #123, Piso 5, Ciudad de México.\n🗺️ Ver ubicación: https://maps.google.com/sonrisa-perfecta'
                    }
                ],
                'fallback_text': 'No entendí tu solicitud dental. Por favor selecciona una opción del menú o escribe "Agendar cita", "Urgencia", o "Servicios".'
            },
            'created_at': '2026-03-13 00:00:00',
            'whatsapp_token': '',
            'verify_token': 'demo_token_dental'
        }
    }
    demos.append(demo_dental)
    
    # ============================================
    # DEMO 2: RESTAURANTE - GourmetBot 2026
    # ============================================
    demo_restaurant = {
        'id': 'demo_restaurante_mesa',
        'firestore_data': {
            'name': '🍽️ Demo Restaurante La Mesa Elegante',
            'phone_number_id': 'demo_restaurant_001',
            'email': 'restaurant@demo.zotek.ia',
            'phone': '5215500000002',
            'system_instruction': 'Eres el asistente virtual experto del Restaurante "La Mesa Elegante". Tu objetivo es tomar pedidos, gestionar reservas y resolver dudas. Responde de manera amable, rápida y apetitosa. Si te envían notas de voz, procésalas para extraer el pedido. Si el usuario tiene restricciones alimentarias, prioriza recomendar platillos seguros.',
            'gemini_prompt': 'Eres el asistente virtual experto de La Mesa Elegante. Tu objetivo es tomar pedidos, gestionar reservas y resolver dudas. Responde de manera amable, rápida y apetitosa.',
            'response_type': 'text',
            'calendly_url': 'https://calendly.com/restaurant-demo',
            'bank_name': 'Santander',
            'clabe': '014180098765432109',
            'beneficiary_name': 'La Mesa Elegante Demo SA de CV',
            'menu_json': {
                'text': '¡Hola! Bienvenido a La Mesa Elegante 🍽️. Soy tu asistente virtual.\n¿Qué se te antoja hoy?',
                'options': [
                    {
                        'title': '📅 Reservar Mesa',
                        'icon': '📅',
                        'response': '¡Con gusto! Para hacer tu reserva, necesito saber:\n📅 ¿Para qué fecha?\n⏰ ¿A qué hora?\n👥 ¿Cuántas personas?'
                    },
                    {
                        'title': '🛵 Pedir Domicilio',
                        'icon': '🛵',
                        'response': '¡Excelente elección! Nuestro servicio a domicilio está disponible de 1:00 PM a 10:00 PM. ¿Qué platillo te gustaría ordenar?'
                    },
                    {
                        'title': '📋 Ver Menú',
                        'icon': '📋',
                        'response': '🍽️ *Nuestro Menú:*\n\n🥗 Entradas: Ensalada César ($120), Carpaccio ($180)\n🍝 Fuertes: Pasta Alfredo ($220), Ribeye ($450), Salmón ($380)\n🍰 Postres: Tiramisú ($95), Flan ($75)\n\n¿Qué te gustaría probar?'
                    },
                    {
                        'title': '🌱 Opciones Veganas',
                        'icon': '🌱',
                        'response': '¡Sí! Contamos con menú 100% plant-based: Ensalada Buddha Bowl ($140), Pasta Primavera vegana ($190), Burger de lentejas ($165). Todos certificados gluten-free.'
                    },
                    {
                        'title': '⏰ Horarios',
                        'icon': '⏰',
                        'response': '🕐 *Horarios:*\nMartes a Domingo: 1:00 PM - 11:00 PM\nLunes: Cerrado por descanso del personal'
                    },
                    {
                        'title': '📍 Ubicación',
                        'icon': '📍',
                        'response': '📍 Av. Presidente Masaryk #456, Polanco, CDMX\n🅿️ Contamos con valet parking\n🐕 Somos pet-friendly en terraza\n🗺️ https://maps.google.com/la-mesa-elegante'
                    }
                ],
                'fallback_text': 'No entendí tu solicitud. Por favor selecciona una opción: "Reservar", "Domicilio", "Menú", o hazme una pregunta sobre nuestros platillos.'
            },
            'created_at': '2026-03-13 00:00:00',
            'whatsapp_token': '',
            'verify_token': 'demo_token_restaurant'
        }
    }
    demos.append(demo_restaurant)
    
    # ============================================
    # DEMO 3: PSICÓLOGO - MenteSana IA
    # ============================================
    demo_psychology = {
        'id': 'demo_psychology_mente',
        'firestore_data': {
            'name': '🧠 Demo Psicólogo Mente Sana',
            'phone_number_id': 'demo_psychology_001',
            'email': 'psychology@demo.zotek.ia',
            'phone': '5215500000003',
            'system_instruction': 'Eres el asistente virtual del centro de psicología "Mente Sana". Eres empático, comprensivo y profesional. Tu función es agendar sesiones de terapia, proporcionar información sobre servicios de salud mental y ofrecer recursos de apoyo. En caso de crisis emocional o pensamientos de autolesión, proporciona inmediatamente los números de emergencia.',
            'gemini_prompt': 'Eres el asistente virtual experto de Mente Sana. Eres empático, comprensivo y profesional. Agendas sesiones de terapia y proporcionas información sobre salud mental. En crisis, proporciona números de emergencia.',
            'response_type': 'text',
            'calendly_url': 'https://calendly.com/psychology-demo',
            'bank_name': 'Banorte',
            'clabe': '072180056789012345',
            'beneficiary_name': 'Mente Sana Demo SC',
            'menu_json': {
                'text': '¡Hola! Bienvenido a Mente Sana 🧠.\nSoy tu asistente virtual. Estoy aquí para apoyarte en tu bienestar emocional. ¿En qué puedo ayudarte?',
                'options': [
                    {
                        'title': '🛋️ Agendar Terapia',
                        'icon': '🛋️',
                        'response': 'Me da mucho gusto que des el paso de cuidar tu salud mental. 🌟\n\nPara agendar, necesito saber:\n📅 ¿Qué días prefieres?\n⏰ ¿Mañana, tarde o noche?\n👤 ¿Terapia individual, de pareja o familiar?'
                    },
                    {
                        'title': '👨‍⚕️ Valoración Gratuita',
                        'icon': '👨‍⚕️',
                        'response': '¡Ofrecemos una primera valoración sin costo! 🎉\n\nDurante 20 minutos conocerás al terapeuta y resolverás dudas. ¿Te gustaría agendarla?'
                    },
                    {
                        'title': '💰 Costos y Seguros',
                        'icon': '💰',
                        'response': '💵 *Inversión por sesión:*\nIndividual (50 min): $800\nPareja (60 min): $1,200\nFamiliar (75 min): $1,500\n\n📄 Aceptamos seguros: AXA, GNP, MetLife, Planes Personales'
                    },
                    {
                        'title': '🚨 Crisis o Emergencia',
                        'icon': '🚨',
                        'response': 'Si estás en crisis o tienes pensamientos de autolesión, por favor llama inmediatamente:\n\n📞 Línea de la Vida: 800 911 2000 (24/7, gratuito)\n📞 Cruz Roja: 55 5555 0505\n\nNo estás solo. Hay personas que quieren ayudarte.'
                    },
                    {
                        'title': '📍 Ubicación y Online',
                        'icon': '📍',
                        'response': '🏢 *Presencial:*\nAv. Insurgentes #789, Roma Norte, CDMX\n\n💻 *Online:*\nSesiones por videollamada disponibles para todo México y el extranjero.'
                    },
                    {
                        'title': '⏰ Horarios',
                        'icon': '⏰',
                        'response': '🕐 *Horarios de atención:*\nLunes a Viernes: 8:00 AM - 9:00 PM\nSábados: 9:00 AM - 3:00 PM\n\n🌙 También contamos con horarios nocturnos para personas con jornadas laborales extensas.'
                    }
                ],
                'fallback_text': 'Gracias por escribir. No entendí completamente tu solicitud. Por favor selecciona una opción del menú o cuéntame más sobre lo que necesitas.'
            },
            'created_at': '2026-03-13 00:00:00',
            'whatsapp_token': '',
            'verify_token': 'demo_token_psychology'
        }
    }
    demos.append(demo_psychology)
    
    # ============================================
    # DEMO 4: SALÓN DE BELLEZA - BellezaTotal IA
    # ============================================
    demo_salon = {
        'id': 'demo_salon_belleza',
        'firestore_data': {
            'name': '💇 Demo Salón Belleza Total',
            'phone_number_id': 'demo_salon_001',
            'email': 'salon@demo.zotek.ia',
            'phone': '5215500000004',
            'system_instruction': 'Eres el asistente virtual del Salón "Belleza Total". Eres amable, entusiasta y conocedor de tendencias de belleza. Tu función es agendar citas para servicios de cabello, uñas, maquillaje y tratamientos faciales. Recomienda servicios basados en las necesidades del cliente y proporciona información sobre productos.',
            'gemini_prompt': 'Eres el asistente virtual experto de Belleza Total. Eres amable, entusiasta y conocedor de tendencias de belleza. Agendas citas y recomiendas servicios.',
            'response_type': 'text',
            'calendly_url': '',
            'bank_name': 'HSBC',
            'clabe': '021180067890123456',
            'beneficiary_name': 'Belleza Total Demo SA de CV',
            'menu_json': {
                'text': '¡Hola! Bienvenido a Belleza Total 💇‍♀️.\n¡Estoy aquí para consentirte! ¿Qué servicio te gustaría hoy?',
                'options': [
                    {
                        'title': '✂️ Corte y Peinado',
                        'icon': '✂️',
                        'response': '¡Me encanta! ✨\n\nNuestros servicios de cabello incluyen:\n💇 Corte: $350\n💇‍♀️ Corte + Peinado: $500\n🎨 Tinte: desde $800\n✨ Mechas/Balayage: desde $1,500\n\n¿Qué estilo tienes en mente?'
                    },
                    {
                        'title': '💅 Manicure y Pedicure',
                        'icon': '💅',
                        'response': '¡Tus uñas merecen lo mejor! 💅\n\nManicure tradicional: $200\nManicure en gel: $350\nUñas acrílicas: $500\nPedicure spa: $300\n\n¿Qué color te gustaría?'
                    },
                    {
                        'title': '💆 Tratamientos Faciales',
                        'icon': '💆',
                        'response': '¡Tu piel radiante te lo agradecerá! ✨\n\nLimpieza facial: $600\nHidratación profunda: $800\nMicrodermoabrasión: $1,200\nTratamiento anti-edad: $1,500\n\n¿Te gustaría una valoración gratuita?'
                    },
                    {
                        'title': '🎨 Maquillaje Profesional',
                        'icon': '🎨',
                        'response': '¡Para esas ocasiones especiales! 💄\n\nMaquillaje social: $800\nMaquillaje de novia: desde $2,500\nMaquillaje de XV años: $1,800\n\n¿Para qué evento lo necesitas?'
                    },
                    {
                        'title': '📅 Agendar Cita',
                        'icon': '📅',
                        'response': '¡Con gusto! Para agendar necesito:\n📅 ¿Qué día te gustaría?\n⏰ ¿Mañana o tarde?\n💇 ¿Qué servicio te interesa?\n\n¡Te esperamos!'
                    },
                    {
                        'title': '📍 Ubicación',
                        'icon': '📍',
                        'response': '📍 Plaza Las Américas, Local 45\nAv. Universidad #321, CDMX\n\n🅿️ Estacionamiento gratuito 2 horas\n📱 55-1234-5678'
                    }
                ],
                'fallback_text': '¡Hola! No entendí completamente. Por favor selecciona un servicio: "Corte", "Uñas", "Facial", "Maquillaje" o "Agendar Cita".'
            },
            'created_at': '2026-03-13 00:00:00',
            'whatsapp_token': '',
            'verify_token': 'demo_token_salon'
        }
    }
    demos.append(demo_salon)
    
    # ============================================
    # DEMO 5: TIENDA DE ROPA - EstiloUrbano IA
    # ============================================
    demo_retail = {
        'id': 'demo_retail_estilo',
        'firestore_data': {
            'name': '👕 Demo Tienda Estilo Urbano',
            'phone_number_id': 'demo_retail_001',
            'email': 'retail@demo.zotek.ia',
            'phone': '5215500000005',
            'system_instruction': 'Eres el asistente virtual de la tienda de ropa "Estilo Urbano". Eres amable, conocedor de moda y tendencias. Tu función es ayudar a los clientes con el catálogo, recomendar tallas, procesar cambios y devoluciones, y proporcionar información sobre promociones y métodos de pago.',
            'gemini_prompt': 'Eres el asistente virtual experto de Estilo Urbano. Eres amable, conocedor de moda y tendencias. Ayudas con catálogo, tallas, cambios y promociones.',
            'response_type': 'text',
            'calendly_url': '',
            'bank_name': 'Scotiabank',
            'clabe': '044180034567890123',
            'beneficiary_name': 'Estilo Urbano Demo SA de CV',
            'menu_json': {
                'text': '¡Hola! Bienvenido a Estilo Urbano 👕.\n¡Estoy aquí para ayudarte a lucir increíble! ¿Qué estás buscando hoy?',
                'options': [
                    {
                        'title': '👗 Ver Catálogo',
                        'icon': '👗',
                        'response': '¡Nuestra nueva colección está increíble! ✨\n\n👚 *Damas:*\nBlusas: $350-$600\nVestidos: $700-$1,500\nPantalones: $500-$900\n\n👔 *Caballeros:*\nCamisas: $450-$800\nPantalones: $600-$1,200\nSacos: $1,500-$3,000\n\n¿Qué categoría te interesa?'
                    },
                    {
                        'title': '📏 Guía de Tallas',
                        'icon': '📏',
                        'response': '¡Te ayudo a encontrar tu talla perfecta! 📏\n\n👗 *Damas:*\nXS: Busto 80cm, Cintura 64cm\nS: Busto 84cm, Cintura 68cm\nM: Busto 88cm, Cintura 72cm\nL: Busto 92cm, Cintura 76cm\n\n👔 *Caballeros:*\nS: Pecho 90cm, Cintura 76cm\nM: Pecho 96cm, Cintura 82cm\nL: Pecho 102cm, Cintura 88cm\n\n¿Necesitas ayuda con alguna prenda específica?'
                    },
                    {
                        'title': '🔄 Cambios y Devoluciones',
                        'icon': '🔄',
                        'response': '¡Tu satisfacción es primero! 😊\n\n✅ Tienes 30 días para cambios o devoluciones\n✅ Con ticket de compra\n✅ Prenda sin usar y con etiquetas\n\n📍 Cambios en tienda: Sin costo\n📦 Cambios por envío: Nosotros cubrimos el envío'
                    },
                    {
                        'title': '🏷️ Promociones',
                        'icon': '🏷️',
                        'response': '¡Aprovecha nuestras ofertas! 🎉\n\n🔥 *Esta semana:*\n- 20% en segunda prenda\n- 30% en selección de outlet\n- Envío gratis en compras +$1,500\n\n💳 *Meses sin intereses:*\n3, 6 y 9 MSI en compras +$1,000'
                    },
                    {
                        'title': '📦 Envíos a Domicilio',
                        'icon': '📦',
                        'response': '¡Llevamos la moda hasta tu puerta! 🚚\n\n📍 CDMX y Área Metropolitana: $80 (2-3 días)\n📍 Resto de la República: $120 (5-7 días)\n🆓 Envío GRATIS en compras +$1,500\n\n📱 Recibe notificaciones de tu pedido por WhatsApp'
                    },
                    {
                        'title': '💳 Métodos de Pago',
                        'icon': '💳',
                        'response': 'Aceptamos todas las formas de pago:\n\n💵 Efectivo\n💳 Tarjetas de crédito/débito\n📱 Transferencia SPEI\n🏦 Meses sin intereses (3, 6, 9, 12 MSI)\n\n¿Tienes alguna duda sobre tu compra?'
                    }
                ],
                'fallback_text': '¡Hola! No entendí tu solicitud. Por favor selecciona: "Catálogo", "Tallas", "Cambios", "Promociones", "Envíos" o "Pagos".'
            },
            'created_at': '2026-03-13 00:00:00',
            'whatsapp_token': '',
            'verify_token': 'demo_token_retail'
        }
    }
    demos.append(demo_retail)
    
    return demos

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 Generador de 5 Bots Demo Completos")
    print("=" * 60)
    
    # Generar demos
    demos = generate_demos()
    
    # Guardar en archivo JSON
    base_dir = Path(__file__).parent
    output_file = base_dir / "data" / "demos_completos_firestore.json"
    
    export_data = {
        'generated_at': '2026-03-13',
        'total_demos': len(demos),
        'demos': demos
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(demos)} demos generados exitosamente")
    print(f"💾 Archivo guardado: {output_file}")
    print("\n" + "=" * 60)
    print("📋 Resumen de Demos")
    print("=" * 60)
    
    for demo in demos:
        data = demo['firestore_data']
        print(f"\n🔹 {data['name']}")
        print(f"   ID: {demo['id']}")
        print(f"   Phone Number ID: {data['phone_number_id']}")
        print(f"   Email: {data['email']}")
        print(f"   Banco: {data['bank_name']}")
        print(f"   Menú: {len(data['menu_json']['options'])} opciones")
        
        # Mostrar menú
        print(f"   \n   Opciones del menú:")
        for opt in data['menu_json']['options']:
            print(f"      {opt['title']}: {opt['response'][:60]}...")
    
    print("\n" + "=" * 60)
    print("💡 Instrucciones para importar a Firebase Firestore")
    print("=" * 60)
    print("""
    Método 1 - Firebase Console (Manual):
    1. Ve a https://console.firebase.google.com
    2. Selecciona tu proyecto: zotek-ia
    3. Ve a Firestore Database
    4. Crea colección 'clients' (si no existe)
    5. Para cada demo:
       a. Click en "Add Document"
       b. Document ID: usa el valor de 'id' (ej: demo_dental_sonrisa)
       c. Agrega cada campo de 'firestore_data'
       d. Para menu_json, usa tipo 'map' y copia la estructura
    
    Método 2 - Script con Firebase Admin SDK:
    1. Consigue tu service-account-key.json de Firebase
    2. Guárdalo en functions/service-account-key.json
    3. Ejecuta: python import_demos_to_firestore.py
    
    Método 3 - Firebase CLI (Recomendado):
    1. firebase login
    2. firebase firestore:import data/demos_completos_firestore.json
    """)
    print("=" * 60)
    
    # Generar script de importación
    generate_import_script()
    
    return demos

def generate_import_script():
    """Genera un script Python para importar los demos a Firestore"""
    
    script_content = '''"""
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
    
    print(f"\\n📥 Importando {len(demos)} demos a Firestore...\\n")
    
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
    
    print(f"\\n" + "=" * 60)
    print(f"✅ Importados: {imported}")
    print(f"⚠️  Saltados: {skipped}")
    print("=" * 60)

if __name__ == "__main__":
    if initialize_firebase():
        import_demos()
'''
    
    base_dir = Path(__file__).parent
    script_file = base_dir / "import_demos_to_firestore.py"
    
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"\n📝 Script de importación generado: {script_file}")

if __name__ == "__main__":
    main()
