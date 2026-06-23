import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# Cargar variables de entorno (forzamos override para usar Supabase y no variables de sistema locales)
# Buscamos el archivo .env en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=env_path, override=True)

DATABASE_URL = os.environ.get("DATABASE_URL")

# Campos cifrados en la tabla clients
_SENSITIVE_FIELDS = {"whatsapp_token", "stripe_api_key", "email_password", "clabe"}

def _decrypt_client(client_dict: dict) -> dict:
    """Descifra los campos sensibles de un cliente leído de la DB."""
    if not client_dict:
        return client_dict
    raw_key = os.environ.get("FIELD_ENCRYPTION_KEY")
    if not raw_key:
        return client_dict
    try:
        from cryptography.fernet import Fernet, InvalidToken
        fernet = Fernet(raw_key.encode())
        for field in _SENSITIVE_FIELDS:
            val = client_dict.get(field)
            if val:
                try:
                    client_dict[field] = fernet.decrypt(val.encode()).decode()
                except (InvalidToken, Exception):
                    pass  # ya estaba en texto plano o formato distinto
    except Exception as e:
        print(f"⚠️ decrypt_client error: {e}")
    return client_dict

def get_connection():
    """Obtiene una conexión a la base de datos PostgreSQL de Supabase."""
    if not DATABASE_URL:
        raise ValueError("⚠️ DATABASE_URL no está configurada.")
    
    try:
        # Usamos sslmode='prefer' para mayor compatibilidad con Supabase Pooler
        conn = psycopg2.connect(DATABASE_URL, sslmode='prefer')
        return conn
    except Exception as e:
        # Intentamos extraer el host para el log
        host = "unknown"
        try:
            if DATABASE_URL:
                host = DATABASE_URL.split("@")[-1].split(":")[0]
        except:
            pass
        print(f"❌ Error conectando a {host}: {e}")
        raise e

_db = None

def get_db():
    """Compatibilidad con código existente que llama get_db()."""
    global _db
    if _db is None:
        _db = get_connection()
    return _db

def init_db():
    """
    Inicializa la base de datos con el esquema multitenencia relacional.
    En producción, las tablas ya deberían existir.
    """
    print("🗄️ Inicializando base de datos PostgreSQL (InsForge)...")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Tabla de Clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                whatsapp_token TEXT NOT NULL,
                phone_number_id TEXT NOT NULL UNIQUE,
                verify_token TEXT NOT NULL,
                system_instruction TEXT,
                stripe_api_key TEXT,
                bank_name TEXT,
                clabe TEXT,
                beneficiary_name TEXT,
                menu_json JSONB,
                plan TEXT DEFAULT 'free',
                email TEXT DEFAULT '',
                calendly_url TEXT DEFAULT '',
                appointment_rate_limit INTEGER DEFAULT 10,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Migración idempotente: agregar columna de límite de citas/hora a tablas ya existentes.
        # (init_db no corre en producción al arrancar; ejecutar manualmente o vía scripts/migrate.)
        cursor.execute('''
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS appointment_rate_limit INTEGER DEFAULT 10
        ''')

        # Tabla de Base de Conocimientos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                source_file TEXT,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de Citas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citas (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                cliente_telefono TEXT,
                paciente_nombre TEXT,
                fecha_hora TEXT,
                motivo TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de Message Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_logs (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                direction TEXT NOT NULL,
                phone_number TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Índices para message_logs
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_client ON message_logs(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_logs_date ON message_logs(created_at)')

        # Tabla de Historial de Conversación
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id SERIAL PRIMARY KEY,
                phone_number TEXT NOT NULL,
                content TEXT NOT NULL,
                is_user INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Índices para conversation_history
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_phone ON conversation_history(phone_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_date ON conversation_history(created_at)')

        # Tabla de Sesiones Sandbox (para demos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sandbox_sessions (
                id SERIAL PRIMARY KEY,
                user_number TEXT NOT NULL,
                phone_number_id TEXT NOT NULL,
                demo_mode TEXT,
                session_data JSONB,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_number, phone_number_id)
            )
        ''')

        # Tabla de Chats (historial por cliente)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_chats (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                user_number TEXT NOT NULL DEFAULT '',
                phone_number TEXT DEFAULT '',
                last_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_chats_client ON client_chats(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_chats_user ON client_chats(user_number)')

        # Tabla de Horarios del Cliente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_schedules (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                schedule_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_schedules_client ON client_schedules(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_schedules_date ON client_schedules(schedule_date)')

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Base de datos PostgreSQL inicializada (Tablas verificadas).")
    except Exception as e:
        print(f"❌ Error al inicializar PostgreSQL: {e}")
        raise e


def get_client_by_phone_id(phone_number_id):
    """Obtiene los datos de un cliente por su Phone Number ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients WHERE phone_number_id = %s", (str(phone_number_id),))
        client = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if client:
            client_dict = dict(client)
            # Convertir menu_json a string si es dict para compatibilidad
            if isinstance(client_dict.get('menu_json'), dict):
                client_dict['menu_json'] = json.dumps(client_dict['menu_json'])
            return _decrypt_client(client_dict)
        return None
    except Exception as e:
        print(f"❌ ERROR get_client_by_phone_id: {e}")
        return None


def get_client_by_email(email):
    """Obtiene un cliente por su email de login."""
    if not email:
        return None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients WHERE email = %s", (str(email).lower().strip(),))
        client = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if client:
            client_dict = dict(client)
            if isinstance(client_dict.get('menu_json'), dict):
                client_dict['menu_json'] = json.dumps(client_dict['menu_json'])
            return _decrypt_client(client_dict)
        return None
    except Exception as e:
        print(f"❌ ERROR get_client_by_email: {e}")
        return None


def save_verification_code(email: str, code: str, expires_minutes: int = 10):
    """Guarda un código de verificación en PostgreSQL"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        email_clean = email.lower().strip()
        cursor.execute('''
            INSERT INTO verification_codes (email, code, expires_at)
            VALUES (%s, %s, NOW() + INTERVAL '1 minute' * %s)
            ON CONFLICT (email) DO UPDATE SET code = EXCLUDED.code, expires_at = NOW() + INTERVAL '1 minute' * %s
        ''', (email_clean, code, expires_minutes, expires_minutes))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR save_verification_code: {e}")
        return False

def get_verification_code(email: str):
    """Obtiene el último código de verificación."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        email_clean = email.lower().strip()
        cursor.execute('''
            SELECT code FROM verification_codes
            WHERE email = %s AND expires_at >= NOW()
        ''', (email_clean,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row['code'] if row else None
    except Exception as e:
        print(f"❌ ERROR get_verification_code: {e}")
        return None


def get_client_by_id(client_id):
    """Obtiene un cliente por su ID."""
    # Demos hardcodeados como respaldo - IDs REALES en PostgreSQL
    _SI_RESTAURANT = """Eres GourmetBot, el asistente virtual del Restaurante "La Mesa Elegante", un restaurante de cocina mexicana contemporánea en el Centro de la Ciudad de México.

━━━━━━━━━━━━━━━━━━━━━━━
📋 INFORMACIÓN DEL RESTAURANTE
━━━━━━━━━━━━━━━━━━━━━━━
Nombre: La Mesa Elegante
Dirección: Av. Juárez #456, Centro Histórico, CDMX
Teléfono: 55-1234-5678
Horario: Lunes a Viernes 1pm–11pm | Sábado y Domingo 12pm–11pm
Reservaciones: Disponibles por WhatsApp o llamada

━━━━━━━━━━━━━━━━━━━━━━━
🍽️ MENÚ COMPLETO CON PRECIOS
━━━━━━━━━━━━━━━━━━━━━━━

ENTRADAS:
• Guacamole de la casa (para 2) — $120
• Sopa de lima estilo yucateco — $95
• Flautas de pollo con crema y queso — $110
• Ceviche de camarón con tostadas — $145

PLATOS FUERTES:
• Arrachera a la parrilla (300g) con papas y ensalada — $285
• Mole negro con pollo y arroz — $210
• Camarones al ajillo con arroz blanco — $265
• Enchiladas verdes con pollo y crema — $175
• Filete de res en salsa de chile pasilla — $320
• Chiles rellenos de queso con caldillo — $190
• Tacos de cochinita pibil (3 piezas) — $155

POSTRES:
• Pastel de tres leches — $85
• Churros con chocolate caliente — $75
• Flan napolitano de la casa — $70

BEBIDAS:
• Aguas frescas (jamaica, horchata, limón) — $45
• Refrescos — $40
• Cerveza nacional — $65
• Vino de la casa (copa) — $95
• Margarita clásica — $110

━━━━━━━━━━━━━━━━━━━━━━━
📌 INSTRUCCIONES DE COMPORTAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━
- Eres amable, cálido y conoces el menú de memoria
- Cuando el usuario pregunte por el menú, muéstralo completo con precios
- Para reservaciones, pregunta: fecha, hora, número de personas y nombre
- Si preguntan por recomendaciones, sugiere el Mole negro o la Arrachera como especialidades
- Siempre termina recordando: "📋 Escribe *menú* para ver opciones o *salir* para volver a Zotek"
- IMPORTANTE: Esta es una DEMOSTRACIÓN de Zotek SolucionesIA. Si el usuario pregunta sobre el bot, explica que es un ejemplo de lo que Zotek puede crear para su negocio."""

    _SI_DENTAL = """Eres SonrisaBot, el asistente virtual de la Clínica Dental "Sonrisa Perfecta", una clínica odontológica moderna en Guadalajara, Jalisco.

━━━━━━━━━━━━━━━━━━━━━━━
🏥 INFORMACIÓN DE LA CLÍNICA
━━━━━━━━━━━━━━━━━━━━━━━
Nombre: Clínica Dental Sonrisa Perfecta
Dirección: Av. Vallarta #1200, Guadalajara, Jalisco
Teléfono: 33-4567-8901
Horario: Lunes a Viernes 9am–7pm | Sábado 9am–2pm | Domingo cerrado
Especialidad: Odontología general, estética y ortodoncia

━━━━━━━━━━━━━━━━━━━━━━━
💎 SERVICIOS Y PRECIOS
━━━━━━━━━━━━━━━━━━━━━━━

ODONTOLOGÍA GENERAL:
• Consulta y revisión general — $350
• Limpieza dental (profilaxis) — $500
• Extracción simple — $600
• Extracción de muela del juicio — $1,200
• Empaste (resina) por pieza — $700
• Tratamiento de conductos (endodoncia) — $2,500

ODONTOLOGÍA ESTÉTICA:
• Blanqueamiento dental profesional — $2,800
• Carillas de porcelana (por pieza) — $4,500
• Diseño de sonrisa (consulta) — $500 (se abona al tratamiento)

ORTODONCIA:
• Consulta de valoración — $500 (gratis si se inicia tratamiento)
• Brackets metálicos (tratamiento completo) — $18,000
• Brackets de zafiro (estéticos) — $24,000
• Alineadores invisibles (Invisalign) — desde $35,000

IMPLANTES:
• Implante dental + corona — $18,000
• Consulta de valoración para implantes — Gratis

━━━━━━━━━━━━━━━━━━━━━━━
📌 INSTRUCCIONES DE COMPORTAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━
- Eres profesional, empático y transmites confianza
- Para agendar cita, pregunta: nombre, servicio que necesita, y preferencia de día/hora
- Si alguien tiene dolor dental, prioriza la atención urgente y ofrece cita el mismo día
- Menciona que el Dr. García Morales tiene más de 15 años de experiencia
- Siempre termina con: "📋 Escribe *servicios* para ver opciones o *salir* para volver a Zotek"
- IMPORTANTE: Esta es una DEMOSTRACIÓN de Zotek SolucionesIA para mostrar cómo un bot puede funcionar para una clínica dental."""

    _SI_PSYCHOLOGY = """Eres MenteSanaBot, el asistente administrativo virtual del consultorio del Dr. Alejandro Ruiz, Psicólogo Clínico en Monterrey, Nuevo León.

━━━━━━━━━━━━━━━━━━━━━━━
🧠 INFORMACIÓN DEL CONSULTORIO
━━━━━━━━━━━━━━━━━━━━━━━
Nombre: Consultorio Psicológico Dr. Alejandro Ruiz
Ubicación: Torre Médica Monterrey, Piso 8, Cons. 803
Dirección: Av. Constitución #890, Monterrey, NL
Teléfono: 81-2345-6789
Horario: Lunes a Viernes 9am–7pm | Sábado 10am–2pm

━━━━━━━━━━━━━━━━━━━━━━━
🩺 ESPECIALIDADES Y SERVICIOS
━━━━━━━━━━━━━━━━━━━━━━━

SERVICIOS INDIVIDUALES:
• Consulta de valoración inicial — $800
• Terapia individual (50 min) — $900
• Terapia de pareja (70 min) — $1,200
• Terapia adolescentes (50 min) — $800

ÁREAS DE ESPECIALIDAD:
• Ansiedad y ataques de pánico
• Depresión y trastornos del estado de ánimo
• Estrés y burnout laboral
• Duelo y pérdidas
• Autoestima y desarrollo personal
• Terapia cognitivo-conductual (TCC)
• Mindfulness y manejo del estrés

MODALIDADES:
• Presencial en consultorio
• En línea (videollamada)
• Modalidad híbrida

━━━━━━━━━━━━━━━━━━━━━━━
📌 INSTRUCCIONES DE COMPORTAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━
- Eres empático, discreto y respetuoso. Nunca minimices los problemas emocionales del usuario
- Tu rol es ADMINISTRATIVO: agendas citas, informas servicios y precios, NO haces terapia
- Para agendar cita, pregunta: nombre, motivo general de consulta, y preferencia de horario
- Si alguien expresa una crisis o urgencia emocional, da el número de emergencias: 800-290-0024 (SAPTEL)
- Siempre mantén confidencialidad y profesionalismo
- Termina con: "📋 Escribe *servicios* para ver opciones o *salir* para volver a Zotek"
- IMPORTANTE: Esta es una DEMOSTRACIÓN de Zotek SolucionesIA para consultorios psicológicos."""

    _SI_SALON = """Eres GlamourBot, el asistente virtual del Salón de Belleza "Estilo & Glamour", un salón premium en Guadalajara, Jalisco.

━━━━━━━━━━━━━━━━━━━━━━━
💇 INFORMACIÓN DEL SALÓN
━━━━━━━━━━━━━━━━━━━━━━━
Nombre: Estilo & Glamour
Dirección: Plaza Andares, Local 145, Zapopan, Jalisco
Teléfono: 33-9876-5432
Horario: Lunes a Sábado 9am–8pm | Domingo 10am–4pm
Instagram: @EstiloGlamourGDL

━━━━━━━━━━━━━━━━━━━━━━━
✂️ SERVICIOS Y PRECIOS
━━━━━━━━━━━━━━━━━━━━━━━

CORTES:
• Corte de cabello dama — $200
• Corte de cabello caballero — $150
• Corte + lavado + secado — $280
• Corte de puntas (mantenimiento) — $150

COLOR Y TÉCNICAS:
• Tinte completo (1 tono) — desde $450
• Mechas californianas — desde $800
• Balayage — desde $1,200
• Rayos o puntas — desde $600
• Decoloración completa — desde $1,000
• Corrección de color — precio a valorar

TRATAMIENTOS:
• Keratina brasileña — desde $1,500
• Alisado japonés — desde $2,000
• Hidratación profunda — $350
• Botox capilar — $600

OTROS SERVICIOS:
• Peinado de fiesta o evento — desde $400
• Recogido para boda o XV años — desde $600
• Maquillaje profesional — desde $700
• Manicure clásica — $150
• Pedicure completo — $200

━━━━━━━━━━━━━━━━━━━━━━━
📌 INSTRUCCIONES DE COMPORTAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━
- Eres entusiasta, fashion-forward y haces que el cliente se sienta especial
- Para citas, pregunta: nombre, servicio deseado, y día/hora preferida
- Menciona que contamos con estilistas certificados en técnicas europeas
- Para servicios de color, recomienda agendar consulta previa sin costo
- Siempre termina con: "💅 Escribe *servicios* para ver más opciones o *salir* para volver a Zotek"
- IMPORTANTE: Esta es una DEMOSTRACIÓN de Zotek SolucionesIA para salones de belleza."""

    _SI_RETAIL = """Eres StyleBot, el Personal Shopper virtual de "Urban Vibe", una marca de moda urbana contemporánea con tienda física y en línea.

━━━━━━━━━━━━━━━━━━━━━━━
🛍️ INFORMACIÓN DE LA TIENDA
━━━━━━━━━━━━━━━━━━━━━━━
Nombre: Urban Vibe
Tienda física: Centro Santa Fe, Local 3B, CDMX
Tienda en línea: urbanvibe.mx
Teléfono / WhatsApp: 55-8765-4321
Horario tienda física: Lunes a Domingo 11am–9pm
Envíos: Todo México (3–5 días hábiles) | Gratis en compras mayores a $800

━━━━━━━━━━━━━━━━━━━━━━━
👕 CATÁLOGO Y PRECIOS
━━━━━━━━━━━━━━━━━━━━━━━

HOMBRE:
• Playeras básicas premium — $299
• Camisas casuales — $499
• Jeans slim fit — $699
• Joggers Urban — $549
• Sudaderas con capucha — $749
• Chamarras de mezclilla — $999

MUJER:
• Blusas de temporada — $349
• Vestidos casuales — $599
• Jeans de tiro alto — $699
• Conjuntos deportivos (2 piezas) — $849
• Sudaderas cropped — $649
• Abrigos oversized — $1,299

ACCESORIOS:
• Gorras Urban Vibe — $249
• Mochilas — $599
• Cinturones de cuero — $349
• Calcetines (pack x3) — $199

COLECCIÓN ACTUAL:
• Colección Verano 2026 "Solar Waves" — nueva llegada
• Tallas disponibles: XS, S, M, L, XL, XXL

━━━━━━━━━━━━━━━━━━━━━━━
📌 INSTRUCCIONES DE COMPORTAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━
- Eres trendy, amigable y ayudas al cliente a encontrar su estilo
- Para pedidos en línea, pide: talla, color preferido y dirección de envío
- Menciona las promociones: 10% de descuento en primera compra con código URBAN10
- Si preguntan por disponibilidad, diles que verifiquen en urbanvibe.mx o que tú puedes apartar por WhatsApp
- Siempre termina con: "🛒 Escribe *catálogo* para ver más productos o *salir* para volver a Zotek"
- IMPORTANTE: Esta es una DEMOSTRACIÓN de Zotek SolucionesIA para tiendas y retail."""

    _MENU_RESTAURANT = json.dumps({
        "text": "🍽️ Bienvenido a *La Mesa Elegante*\n\nCocina mexicana contemporánea en el corazón del Centro Histórico.\n\n¿En qué te puedo ayudar hoy? 👇",
        "options": [
            {
                "title": "📋 Ver el Menú completo",
                "response": "🍽️ *Menú completo — La Mesa Elegante*\n\n*ENTRADAS*\n• Guacamole de la casa (para 2) — $120\n• Sopa de lima estilo yucateco — $95\n• Flautas de pollo con crema y queso — $110\n• Ceviche de camarón con tostadas — $145\n\n*PLATOS FUERTES*\n• Arrachera a la parrilla (300g) — $285\n• Mole negro con pollo y arroz — $210\n• Camarones al ajillo — $265\n• Enchiladas verdes con pollo — $175\n• Filete en salsa de chile pasilla — $320\n• Chiles rellenos de queso — $190\n• Tacos de cochinita pibil (3 pzas) — $155\n\n*POSTRES*\n• Pastel de tres leches — $85\n• Churros con chocolate — $75\n• Flan napolitano — $70\n\n*BEBIDAS*\n• Aguas frescas $45 | Refrescos $40\n• Cerveza nacional $65 | Vino (copa) $95\n• Margarita clásica $110\n\n¿Deseas hacer una *reservación*? 😊"
            },
            {"title": "📅 Hacer una Reservación"},
            {
                "title": "⏰ Horarios y Ubicación",
                "response": "📍 *La Mesa Elegante*\n\n📌 Av. Juárez #456, Centro Histórico, CDMX\n📞 55-1234-5678\n\n🕐 *Horarios:*\n• Lunes a Viernes: 1pm – 11pm\n• Sábado y Domingo: 12pm – 11pm\n\n¿Deseas hacer una *reservación*? 😊"
            },
            {
                "title": "💰 Precios y Promociones",
                "response": "💰 *Precios — La Mesa Elegante*\n\n🥗 Entradas: $95 – $145\n🍽️ Platos fuertes: $155 – $320\n🍮 Postres: $70 – $85\n🍹 Bebidas: $40 – $110\n\n🎉 *Promociones:*\n• Martes y Miércoles: 2x1 en Margaritas\n• Domingo familiar: 10% de descuento en mesa de 4+\n\nEscribe *menú* para ver todas las opciones. 😊"
            },
            {"title": "🚪 Salir (volver a Zotek)"}
        ]
    })

    _MENU_DENTAL = json.dumps({
        "text": "🦷 Bienvenido a *Clínica Dental Sonrisa Perfecta*\n\nTu salud bucal es nuestra prioridad. ¿En qué te podemos ayudar? 👇",
        "options": [
            {"title": "📋 Ver Servicios y Precios"},
            {"title": "📅 Agendar una Cita"},
            {"title": "⏰ Horarios y Ubicación"},
            {"title": "💰 Promociones vigentes"},
            {"title": "🚪 Salir (volver a Zotek)"}
        ]
    })

    _MENU_PSYCHOLOGY = json.dumps({
        "text": "🧠 Bienvenido al consultorio del *Dr. Alejandro Ruiz*\n\nPsicólogo Clínico con 10 años de experiencia. Estamos aquí para apoyarte. 💙\n\n¿En qué te podemos ayudar? 👇",
        "options": [
            {"title": "📋 Ver Servicios y Tarifas"},
            {"title": "📅 Agendar una Cita"},
            {"title": "🩺 Áreas de Especialidad"},
            {"title": "⏰ Horarios y Ubicación"},
            {"title": "🚪 Salir (volver a Zotek)"}
        ]
    })

    _MENU_SALON = json.dumps({
        "text": "💇 Bienvenido a *Estilo & Glamour*\n\nEl salón premium donde tu belleza es lo más importante. ✨\n\n¿Qué servicio buscas hoy? 👇",
        "options": [
            {"title": "✂️ Cortes y Peinados"},
            {"title": "🎨 Color y Técnicas"},
            {"title": "💆 Tratamientos Capilares"},
            {"title": "📅 Agendar mi Cita"},
            {"title": "🚪 Salir (volver a Zotek)"}
        ]
    })

    _MENU_RETAIL = json.dumps({
        "text": "🛍️ Bienvenido a *Urban Vibe*\n\nModa urbana contemporánea para hombre y mujer. Tu estilo, tu actitud. 🔥\n\n¿Qué buscas hoy? 👇",
        "options": [
            {"title": "👕 Ropa para Hombre"},
            {"title": "👗 Ropa para Mujer"},
            {"title": "👜 Accesorios"},
            {"title": "🚚 Envíos y Devoluciones"},
            {"title": "🚪 Salir (volver a Zotek)"}
        ]
    })

    demo_ids = {
        "demo_restaurant": {"id": "demo_restaurant", "name": "🤖 Demo GourmetBot 2026", "phone_number_id": "demo_restaurant", "system_instruction": _SI_RESTAURANT, "menu_json": _MENU_RESTAURANT, "is_active": True, "whatsapp_token": None},
        "demo_dental":     {"id": "demo_dental",     "name": "🤖 Demo SonrisaPerfecta IA", "phone_number_id": "demo_dental",     "system_instruction": _SI_DENTAL,      "menu_json": _MENU_DENTAL,      "is_active": True, "whatsapp_token": None},
        "demo_psychology": {"id": "demo_psychology", "name": "🤖 Demo MenteSana Bot",      "phone_number_id": "demo_psychology", "system_instruction": _SI_PSYCHOLOGY,  "menu_json": _MENU_PSYCHOLOGY,  "is_active": True, "whatsapp_token": None},
        "demo_salon":      {"id": "demo_salon",      "name": "🤖 Demo GlamourBot 2026",    "phone_number_id": "demo_salon",      "system_instruction": _SI_SALON,       "menu_json": _MENU_SALON,       "is_active": True, "whatsapp_token": None},
        "demo_retail":     {"id": "demo_retail",     "name": "🤖 Demo StyleBot 2026",      "phone_number_id": "demo_retail",     "system_instruction": _SI_RETAIL,      "menu_json": _MENU_RETAIL,      "is_active": True, "whatsapp_token": None},
        # IDs alternativos con _001 para compatibilidad
        "demo_restaurant_001": {"id": "demo_restaurant_001", "name": "🤖 Demo GourmetBot 2026",    "phone_number_id": "demo_restaurant_001", "system_instruction": _SI_RESTAURANT, "menu_json": _MENU_RESTAURANT, "is_active": True, "whatsapp_token": None},
        "demo_dental_001":     {"id": "demo_dental_001",     "name": "🤖 Demo SonrisaPerfecta IA", "phone_number_id": "demo_dental_001",     "system_instruction": _SI_DENTAL,      "menu_json": _MENU_DENTAL,      "is_active": True, "whatsapp_token": None},
        "demo_psychology_001": {"id": "demo_psychology_001", "name": "🤖 Demo MenteSana Bot",      "phone_number_id": "demo_psychology_001", "system_instruction": _SI_PSYCHOLOGY,  "menu_json": _MENU_PSYCHOLOGY,  "is_active": True, "whatsapp_token": None},
        "demo_salon_001":      {"id": "demo_salon_001",      "name": "🤖 Demo GlamourBot 2026",    "phone_number_id": "demo_salon_001",      "system_instruction": _SI_SALON,       "menu_json": _MENU_SALON,       "is_active": True, "whatsapp_token": None},
        "demo_retail_001":     {"id": "demo_retail_001",     "name": "🤖 Demo StyleBot 2026",      "phone_number_id": "demo_retail_001",     "system_instruction": _SI_RETAIL,      "menu_json": _MENU_RETAIL,      "is_active": True, "whatsapp_token": None},
    }

    cid_str = str(client_id)
    if cid_str in demo_ids:
        return demo_ids[cid_str]

    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
        client = cursor.fetchone()
        cursor.close()
        conn.close()

        if client:
            client_dict = dict(client)
            if isinstance(client_dict.get('menu_json'), dict):
                client_dict['menu_json'] = json.dumps(client_dict['menu_json'])
            return _decrypt_client(client_dict)
        return None
    except Exception as e:
        print(f"❌ ERROR get_client_by_id: {e}")
        return None


def get_client_knowledge(client_id):
    """Retorna el contenido de la base de conocimientos de un cliente."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM knowledge_base WHERE client_id = %s", (client_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            return "Sin base de conocimiento configurada."
        return "\n\n".join([row[0] for row in rows])
    except Exception as e:
        print(f"❌ ERROR get_client_knowledge: {e}")
        return ""


def add_knowledge_entry(client_id, content, source_file=None):
    """Agrega una nueva entrada a la base de conocimientos de un cliente."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO knowledge_base (client_id, content, source_file)
            VALUES (%s, %s, %s)
        ''', (client_id, content, source_file))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR add_knowledge_entry: {e}")
        return False


def list_clients():
    """Retorna una lista de todos los clientes registrados."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clients ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        clients = []
        for row in rows:
            client_dict = dict(row)
            if isinstance(client_dict.get('menu_json'), dict):
                client_dict['menu_json'] = json.dumps(client_dict['menu_json'])
            clients.append(_decrypt_client(client_dict))
        return clients
    except Exception as e:
        print(f"❌ ERROR list_clients: {e}")
        return []


def add_client(data):
    """Crea un nuevo cliente en PostgreSQL."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Preparar datos
        menu_json = data.pop('menu_json', None)
        if isinstance(menu_json, str):
            try:
                menu_json = json.loads(menu_json)
            except:
                menu_json = None
        
        cursor.execute('''
            INSERT INTO clients (
                name, whatsapp_token, phone_number_id, verify_token,
                system_instruction, email, calendly_url, menu_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data.get('name', ''),
            data.get('whatsapp_token', ''),
            data.get('phone_number_id', ''),
            data.get('verify_token', ''),
            data.get('system_instruction', ''),
            data.get('email', ''),
            data.get('calendly_url', ''),
            menu_json,
        ))
        
        new_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR add_client: {e}")
        return False


_ALLOWED_UPDATE_FIELDS = {
    'name', 'system_instruction', 'email', 'calendly_url', 'menu_json',
    'plan', 'is_active', 'bank_name', 'beneficiary_name',
    'whatsapp_token', 'phone_number_id', 'verify_token', 'stripe_api_key', 'clabe',
    'email_password', 'appointment_rate_limit',
}

def update_client(client_id, data):
    """Actualiza la configuración de un cliente existente."""
    try:
        # Eliminar campos que no se deben actualizar y aplicar whitelist de columnas
        data = {k: v for k, v in data.items() if k in _ALLOWED_UPDATE_FIELDS}
        
        if not data:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Construir UPDATE dinámico
        fields = []
        values = []
        for key, value in data.items():
            if key == 'menu_json' and isinstance(value, str):
                try:
                    value = json.loads(value)
                except:
                    pass
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            fields.append(f"{key} = %s")
            values.append(value)
        
        values.append(client_id)
        query = f"UPDATE clients SET {', '.join(fields)} WHERE id = %s"
        cursor.execute(query, values)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR update_client: {e}")
        return False


def delete_client_db_entry(client_id):
    """Elimina un cliente y sus datos relacionados."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eliminar en cascada (las FK tienen ON DELETE CASCADE)
        cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return deleted
    except Exception as e:
        print(f"❌ ERROR delete_client: {e}")
        return False


def duplicate_client(original_id):
    """Duplica un cliente incluyendo su base de conocimientos."""
    import time
    
    original = get_client_by_id(original_id)
    if not original:
        return None

    timestamp = int(time.time() * 1000)
    new_name = f"{original.get('name', 'Copia')} (Copia {time.strftime('%Y-%m-%d')})"
    new_phone_number_id = f"client_{timestamp}"
    new_verify_token = f"verify_{timestamp}"

    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        menu_json = original.get('menu_json')
        if isinstance(menu_json, str):
            try:
                menu_json = json.loads(menu_json)
            except:
                menu_json = None

        cursor.execute('''
            INSERT INTO clients (
                name, whatsapp_token, phone_number_id, verify_token,
                system_instruction, email, calendly_url, menu_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            new_name,
            "",  # whatsapp_token vacío para el nuevo cliente
            new_phone_number_id,
            new_verify_token,
            original.get('system_instruction', ''),
            "",
            original.get('calendly_url', ''),
            menu_json,
        ))

        new_client_id = cursor.fetchone()['id']

        # Copiar base de conocimientos
        cursor.execute("SELECT content, source_file FROM knowledge_base WHERE client_id = %s", (original_id,))
        kb_docs = cursor.fetchall()
        for doc in kb_docs:
            cursor.execute('''
                INSERT INTO knowledge_base (client_id, content, source_file)
                VALUES (%s, %s, %s)
            ''', (new_client_id, doc['content'], doc['source_file']))

        conn.commit()
        cursor.close()
        conn.close()

        return get_client_by_id(new_client_id)
    except Exception as e:
        print(f"❌ ERROR duplicate_client: {e}")
        return None


def list_client_documents(client_id):
    """Lista los archivos de conocimiento de un cliente."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, source_file, updated_at 
            FROM knowledge_base 
            WHERE client_id = %s
            ORDER BY updated_at DESC
        ''', (client_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        docs = []
        for row in rows:
            docs.append({
                'id': row['id'],
                'source_file': row['source_file'] or 'Documento sin nombre',
                'updated_at': str(row['updated_at']) if row['updated_at'] else ''
            })
        return docs
    except Exception as e:
        print(f"❌ ERROR list_client_documents: {e}")
        return []


def delete_knowledge_entry(client_id, doc_id):
    """Elimina una entrada de la base de conocimientos."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM knowledge_base 
            WHERE client_id = %s AND id = %s
        ''', (client_id, doc_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR delete_knowledge_entry: {e}")
        return False


def save_chat_message(client_id, user_number, message, response):
    """Registra un intercambio de mensajes en client_chats.
    El parámetro `message` (input del usuario) se descarta porque el schema
    actual no lo modela; se conserva la `response` como `last_message`.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO client_chats (client_id, user_number, phone_number, last_message)
            VALUES (%s, %s, %s, %s)
        ''', (client_id, user_number, user_number, response))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR save_chat_message: {e}")
        return False


def get_client_chats(client_id, limit=50):
    """Obtiene las últimas conversaciones de un cliente.
    Mantiene el contrato {id, user_number, message, response, timestamp}
    aunque el schema solo guarda `last_message` (mapeado a `response`).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, user_number, phone_number, last_message, created_at, updated_at
            FROM client_chats
            WHERE client_id = %s
            ORDER BY COALESCE(updated_at, created_at) DESC
            LIMIT %s
        ''', (client_id, limit))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        chats = []
        for row in rows:
            ts = row['updated_at'] or row['created_at']
            chats.append({
                'id': row['id'],
                'user_number': row['user_number'] or row['phone_number'] or '',
                'message': '',
                'response': row['last_message'] or '',
                'timestamp': str(ts) if ts else ''
            })
        return chats
    except Exception as e:
        print(f"❌ ERROR get_client_chats: {e}")
        return []


# --- GESTIÓN DE SESIONES DE DEMO (SANDBOX) ---

def get_user_session(user_number, phone_number_id):
    """Obtiene la sesión de sandbox actual para un usuario y bot."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT demo_mode, session_data, updated_at
            FROM sandbox_sessions
            WHERE user_number = %s AND phone_number_id = %s
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (user_number, phone_number_id))
        session = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if session:
            result = dict(session)
            # Parsear session_data si es JSON string
            if isinstance(result.get('session_data'), str):
                try:
                    result['session_data'] = json.loads(result['session_data'])
                except:
                    result['session_data'] = {}
            return result
        return None
    except Exception as e:
        print(f"❌ ERROR get_user_session: {e}")
        return None


def save_user_session(user_number, phone_number_id, session_data):
    """Guarda o actualiza la sesión de sandbox (manual upsert sin ON CONFLICT)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        demo_mode = session_data.get('demo_mode', '')
        session_data_json = json.dumps(session_data)

        # Manual UPSERT: UPDATE first, INSERT if no row exists
        cursor.execute(
            "UPDATE sandbox_sessions SET demo_mode = %s, session_data = %s, updated_at = CURRENT_TIMESTAMP WHERE user_number = %s AND phone_number_id = %s",
            (demo_mode, session_data_json, user_number, phone_number_id)
        )
        if cursor.rowcount == 0:
            cursor.execute(
                "INSERT INTO sandbox_sessions (user_number, phone_number_id, demo_mode, session_data) VALUES (%s, %s, %s, %s)",
                (user_number, phone_number_id, demo_mode, session_data_json)
            )

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR save_user_session: {e}")
        return False


def delete_user_session(user_number, phone_number_id):
    """Elimina la sesión de sandbox de un usuario."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM sandbox_sessions
            WHERE user_number = %s AND phone_number_id = %s
        ''', (user_number, phone_number_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR delete_user_session: {e}")
        return False


def track_message(client_id, direction="outbound", phone_number=None):
    """Registra un mensaje en message_logs para métricas."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO message_logs (client_id, direction, phone_number)
            VALUES (%s, %s, %s)
        ''', (client_id, direction, phone_number))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ ERROR track_message: {e}")


# --- GESTIÓN DE HORARIOS ---

def get_client_schedules(client_id):
    """Obtiene los horarios configurados para un cliente."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT schedule_date, start_time, end_time 
            FROM client_schedules 
            WHERE client_id = %s AND schedule_date >= CURRENT_DATE
            ORDER BY schedule_date ASC, start_time ASC
        ''', (client_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"❌ ERROR get_client_schedules: {e}")
        return []

def get_appointment_by_token(token: str):
    """Obtiene una cita por su token UUID. Incluye nombre del negocio desde clients."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT a.id, a.date_time, a.name, a.phone, a.email, a.status, a.notes, a.token,
                   c.name AS business_name, c.id AS client_id, c.email AS business_email,
                   c.system_instruction, c.vapi_professional_phone, c.email_user, c.calendly_url
            FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE a.token = %s::uuid
        ''', (token,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[DB] ERROR get_appointment_by_token: {e}")
        return None


def get_client_session_duration(client_id):
    """Obtiene la duración de sesión (minutos) guardada en menu_json del cliente."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT menu_json FROM clients WHERE id = %s", (int(client_id),))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and row.get('menu_json'):
            menu = row['menu_json']
            if isinstance(menu, str):
                menu = json.loads(menu)
            return int(menu.get('session_duration', 60))
    except Exception as e:
        print(f"❌ ERROR get_client_session_duration: {e}")
    return 60

def set_client_session_duration(client_id, duration_minutes):
    """Guarda la duración de sesión en menu_json del cliente sin pisar otros campos."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clients
            SET menu_json = COALESCE(menu_json, '{}'::jsonb) || %s::jsonb
            WHERE id = %s
        """, (json.dumps({"session_duration": int(duration_minutes)}), int(client_id)))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR set_client_session_duration: {e}")
        return False

def save_client_schedules(client_id, schedules, week_start=None):
    """Guarda horarios para un cliente, scoped a la semana indicada (no borra otras semanas)."""
    try:
        client_id = int(client_id)
        conn = get_connection()
        cursor = conn.cursor()

        if week_start:
            from datetime import datetime, timedelta
            monday = datetime.strptime(week_start, '%Y-%m-%d').date()
            sunday = monday + timedelta(days=6)
            cursor.execute(
                "DELETE FROM client_schedules WHERE client_id = %s AND schedule_date >= %s AND schedule_date <= %s",
                (client_id, str(monday), str(sunday))
            )
        else:
            dates = list({s.get('schedule_date') for s in schedules if s.get('schedule_date')})
            if dates:
                for d in dates:
                    cursor.execute(
                        "DELETE FROM client_schedules WHERE client_id = %s AND schedule_date = %s",
                        (client_id, d)
                    )

        for sch in schedules:
            cursor.execute('''
                INSERT INTO client_schedules (client_id, schedule_date, start_time, end_time)
                VALUES (%s, %s, %s, %s)
            ''', (client_id, sch.get('schedule_date'), sch.get('start_time'), sch.get('end_time')))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ ERROR save_client_schedules: {e}")
        return False

if __name__ == "__main__":
    # Prueba de conexión
    print("Probando conexión a PostgreSQL...")
    try:
        init_db()
        print("✅ Conexión exitosa")
    except Exception as e:
        print(f"❌ Error: {e}")
