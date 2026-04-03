"""
Script de configuración: Crea el cliente de Mtra. Liliana Bauza en la DB de Zotek.
Ejecutar desde: /functions/  con el venv activo
  cd /Users/omar_morentin/Documents/apps/ZotekAI/Zotekweboficial/functions
  python ../scripts/create_lilibauza_client.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../functions')

from dotenv import load_dotenv
load_dotenv(os.path.dirname(os.path.abspath(__file__)) + '/../functions/.env')

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("ERROR: DATABASE_URL no encontrada en .env")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# ── 1. Asegurar que existe la columna appointment_duration ──────────────────
cur.execute("""
    ALTER TABLE clients ADD COLUMN IF NOT EXISTS appointment_duration INTEGER DEFAULT 60
""")
conn.commit()

# ── 2. Verificar si ya existe el cliente ───────────────────────────────────
cur.execute("SELECT id, name FROM clients WHERE phone_number_id = 'lilibauza_web_widget'")
existing = cur.fetchone()
if existing:
    print(f"El cliente ya existe: ID={existing['id']}  name={existing['name']}")
    print("Si quieres recrearlo, elimínalo primero desde el dashboard.")
    cur.close(); conn.close(); sys.exit(0)

# ── 3. System Instruction ──────────────────────────────────────────────────
SYSTEM_INSTRUCTION = """
Eres el asistente virtual de la Mtra. Liliana Bauza, Psicóloga Clínica en Villa de Álvarez, Colima.
Tu función es atender a pacientes potenciales con calidez y profesionalismo, responder sus dudas sobre los servicios y ayudarles a agendar su cita.

PERSONALIDAD:
- Cálida, empática y profesional.
- Habla en español, tutea al paciente.
- Nunca des diagnósticos ni consejos clínicos. Si el paciente está en crisis, proporciona la línea de crisis: 800 290 0024.

INFORMACIÓN CLAVE:
- Nombre: Mtra. Liliana Bauza | Cédula: 3398478
- Especialidad: Trauma y conducta compulsiva
- Experiencia: +30 años | +228 reseñas verificadas en Doctoralia
- Idiomas: Español e Inglés
- Ubicación: Ceiba 105, Colonia Leandro Valle, Villa de Álvarez, Colima
- Teléfono: 312 145 6877 | Email: contacto@lilianabauza.com
- WhatsApp: https://wa.me/523121456877

SERVICIOS Y PRECIOS:
- Primera Consulta: $700-$800 MXN | 2 horas
- Consultas de Seguimiento: $700 MXN | 50 min
- Consulta en Línea: $700 MXN | 50 min (videollamada)
- Terapia de Pareja: $800 MXN | 80 min
- Terapia Familiar: $900 MXN | 90 min
- EMDR: $700 MXN | 50 min
- Estrés Postraumático: $700 MXN | 50 min
- Ansiedad y Depresión: $700 MXN | 50 min
- Autoestima y Crecimiento Personal: $700 MXN | 50 min

PAGO: Efectivo, tarjeta de crédito/débito, transferencia bancaria. NO acepta seguros de gastos médicos mayores.
POLÍTICA: Cancelación gratuita hasta 24 horas antes.

ENFOQUES TERAPÉUTICOS: Terapia Estratégica, Sistémica Breve, Conductual, Humanista y EMDR.

FLUJO DE CITA (ya definido por el sistema, solo sigue las reglas del sistema):
Cuando el paciente quiera agendar, usa la herramienta mostrar_horarios. Luego pide nombre y teléfono. Luego registra la cita.
""".strip()

# ── 4. Insertar cliente ────────────────────────────────────────────────────
cur.execute("""
    INSERT INTO clients
        (name, whatsapp_token, phone_number_id, verify_token,
         system_instruction, plan, email, appointment_duration)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
""", (
    "Mtra. Liliana Bauza",
    "no_whatsapp",           # widget-only, sin WhatsApp por ahora
    "lilibauza_web_widget",  # identificador único
    "lilibauza_verify",
    SYSTEM_INSTRUCTION,
    "pro",
    "contacto@lilianabauza.com",
    50,                      # duración estándar de sesión en minutos
))
new_client = cur.fetchone()
CLIENT_ID = new_client["id"]
conn.commit()
print(f"✅ Cliente creado: ID={CLIENT_ID}")

# ── 5. Base de conocimiento ────────────────────────────────────────────────
KNOWLEDGE = """
SOBRE LA MTRA. LILIANA BAUZA
Soy especialista en trauma y conducta compulsiva, con más de 30 años de experiencia acompañando a personas en su proceso de sanación emocional. Mi enfoque combina la Terapia Estratégica, Terapia Sistémica Breve, Terapia Conductual y Terapia Humanista.

Frase personal: "La vida no es una serie de errores, mistakes y malas decisiones; es un conjunto de oportunidades nuevas y cambiantes para colectar experiencias de madurez, responsabilidad y felicidad."

FORMACIÓN ACADÉMICA
- Maestría en Terapia Familiar — CEFAP & Universidad Autónoma de Campeche (2017)
- Diplomado en Intervención de Crisis — CONTACTO, Jalisco (2017)
- Diplomado en Terapia Breve y MRI — CEFAP (2015)
- Terapia Humanista Centrada en la Persona — UVM México (1995)

ESPECIALIDADES
- Trauma y Estrés Postraumático (EMDR)
- Conducta Compulsiva
- Terapia Estratégica
- Terapia Familiar
- Ansiedad y Depresión
- Autoestima y Crecimiento Personal

QUÉ ESPERAR EN TU PRIMERA SESIÓN
1. Primer Contacto: Agenda tu cita inicial, presencial en Villa de Álvarez o en línea.
2. Evaluación Inicial (2 horas, $700-$800 MXN): Conocer tu historia, evaluar la situación y definir objetivos.
3. Plan Terapéutico: Plan personalizado según tus necesidades (EMDR, Estratégica, Sistémica).
4. Seguimiento: Sesiones de 50 min ($700 MXN) semanales o quincenales.

TESTIMONIOS DE PACIENTES
- "Muy contenta con el profesionalismo y objetividad de la Mtra. Bauza. La terapia nos apoya muchísimo en la vida diaria." — Cristina
- "Una experiencia gratificante y reconfortante. Muy profesional, amable y abierta. La recomiendo ampliamente." — Daniel Rincón
- "Su empatía y paciencia al explicar cada detalle me hace valorarla como mi psicóloga." — Paulina Sánchez
- "Buena amabilidad, consejos para mejorar y resultados rápidos. Muy recomendada." — Paulo Rgez.
- "¡Superó mis expectativas! Muy profesional, comprensiva y respetuosa." — Alejandro Juárez
- "Mi autoestima ha cambiado completamente después de un año de terapia." — A.L.

ESTADÍSTICAS
- +228 reseñas verificadas en Doctoralia
- +30 años de experiencia
- +1000 pacientes atendidos
- 100% confidencialidad
""".strip()

cur.execute("""
    INSERT INTO knowledge_base (client_id, content, source_file)
    VALUES (%s, %s, %s)
""", (CLIENT_ID, KNOWLEDGE, "landing_page_lilibauza.web.app"))
conn.commit()
print("✅ Base de conocimiento cargada")

# ── 6. Horarios de atención ────────────────────────────────────────────────
# Lunes(1) a Viernes(5): 9:00-14:00 y 16:00-20:00
# Sábado(6): 9:00-13:00
# day_of_week: 1=Lunes ... 7=Domingo
schedules = [
    # Lunes a Viernes mañana
    *[{"day_of_week": d, "start_time": "09:00", "end_time": "14:00"} for d in range(1, 6)],
    # Lunes a Viernes tarde
    *[{"day_of_week": d, "start_time": "16:00", "end_time": "20:00"} for d in range(1, 6)],
    # Sábado mañana
    {"day_of_week": 6, "start_time": "09:00", "end_time": "13:00"},
]

cur.execute("DELETE FROM client_schedules WHERE client_id = %s", (CLIENT_ID,))
for s in schedules:
    cur.execute("""
        INSERT INTO client_schedules (client_id, day_of_week, start_time, end_time)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (client_id, day_of_week, start_time) DO UPDATE SET end_time = EXCLUDED.end_time
    """, (CLIENT_ID, s["day_of_week"], s["start_time"], s["end_time"]))
conn.commit()
print(f"✅ Horarios configurados: Lun-Vie 9-14h y 16-20h | Sáb 9-13h | Sesiones de 50 min")

cur.close()
conn.close()

print(f"\n{'='*50}")
print(f"  Bot de Lili Bauza creado exitosamente")
print(f"  ID del cliente: {CLIENT_ID}")
print(f"  Actualiza ZOTEK_BOT_ID en lilibauza-web/src/app/page.tsx")
print(f"{'='*50}")
