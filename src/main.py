# Deploy Trigger: Force redeploy to fix persistent NameError in production.
# SaaS Improvements: Security, caching, metrics, conversation history
import os
import json
import logging
import random
import smtplib
import hmac
import hashlib
import time
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from collections import deque, defaultdict
from dotenv import load_dotenv
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# Local imports
from . import database
from .config import Config
from .services import whatsapp_service
from .services.gemini_service import GeminiEngine
from .services.vapi_service import vapi as vapi_service
from .services import twilio_service

# Load configuration (already loaded in config.py, but keeping for backward compatibility)
load_dotenv()

# Use Config class for centralized configuration
GEMINI_API_KEY = Config.GEMINI_API_KEY
VERIFY_TOKEN = Config.VERIFY_TOKEN
SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.JWT_ALGORITHM
ADMIN_EMAIL = Config.ADMIN_EMAIL
EMAIL_PASSWORD = Config.EMAIL_APP_PASSWORD
WHATSAPP_APP_SECRET = Config.WHATSAPP_APP_SECRET
VAPI_WEBHOOK_SECRET = os.getenv("VAPI_WEBHOOK_SECRET")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/verify-code")

# In-memory storage for 2FA codes (In production use Redis)
verification_codes = {} # {email: {"code": str, "expiry": datetime}}

# ============================================
# RATE LIMITING (Simple in-memory implementation)
# ============================================
class RateLimiter:
    """Rate limiter simple en memoria para producción."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Verifica si una request está permitida.
        
        Args:
            key: Identificador único (IP, email, etc.)
            max_requests: Máximo de requests en la ventana
            window_seconds: Ventana de tiempo en segundos
        
        Returns:
            True si está permitido, False si excedió límite
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Limpiar requests antiguos
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        
        # Verificar límite
        if len(self.requests[key]) >= max_requests:
            return False
        
        # Agregar request actual
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Obtiene requests restantes en la ventana actual."""
        now = time.time()
        window_start = now - window_seconds
        current_count = len([t for t in self.requests[key] if t > window_start])
        return max(0, max_requests - current_count)

# Rate limiter global
rate_limiter = RateLimiter()

# ============================================
# MÉTRICAS EN MEMORIA
# ============================================
metrics = {
    'total_messages': 0,
    'messages_by_client': defaultdict(int),
    'avg_response_time_ms': 0,
    'gemini_errors': 0,
    'whatsapp_errors': 0,
    'webhook_requests': 0,
    'rate_limited_requests': 0,
    'start_time': time.time(),
}

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW_DIR = os.path.join(BASE_DIR, "www")
ADMIN_DIR = os.path.join(WWW_DIR, "admin")

logger.info("--- SERVER STARTUP DIAGNOSTICS ---")
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"WWW_DIR: {WWW_DIR}")
logger.info(f"ADMIN_DIR: {ADMIN_DIR}")
logger.info(f"Rate limiting: {Config.RATE_LIMIT_MESSAGES_PER_MINUTE}/min")
logger.info("----------------------------------")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://zotek-ia.web.app",
        "https://zotek-ia.firebaseapp.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.exception_handler(404)
async def custom_404_handler(request: Request, __):
    logger.warning(f"404 Not Found: {request.url.path}")
    return JSONResponse(status_code=404, content={"detail": f"Ruta {request.url.path} no encontrada"})

@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.get("/login")
async def login_page():
    return FileResponse(os.path.join(ADMIN_DIR, "login.html"))

@app.get("/admin-control")
async def admin_dashboard():
    return FileResponse(os.path.join(ADMIN_DIR, "index.html"))

# Cache for WhatsApp retries
PROCESSED_MESSAGES = deque(maxlen=100)


# ============================================
# SEGURIDAD: Validación de firma de WhatsApp
# ============================================
def verify_whatsapp_signature(body: bytes, expected_signature: str) -> bool:
    """
    Verifica que el webhook viene realmente de WhatsApp.
    """
    if not WHATSAPP_APP_SECRET:
        return True

    try:
        signature = hmac.new(
            WHATSAPP_APP_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        expected_sig_value = expected_signature.replace('sha256=', '')
        return hmac.compare_digest(signature, expected_sig_value)
    except Exception as e:
        logger.error(f"Error verificando firma WhatsApp: {e}")
        return False


# Lazy initialization using app events or on first request to ensure DB is ready
@app.on_event("startup")
async def startup_event():
    database.init_db()
    global gemini
    gemini = GeminiEngine(api_key=GEMINI_API_KEY)

@app.get("/webhook")
async def verify_webhook(request: Request):
    token = request.query_params.get(Config.WEBHOOK_VERIFY_TOKEN_PARAM)
    if token == VERIFY_TOKEN:
        challenge = request.query_params.get(Config.WEBHOOK_CHALLENGE_PARAM)
        return PlainTextResponse(challenge) if challenge else PlainTextResponse("Ok")
    return "Error auth", 403

@app.post("/webhook")
async def recibir_mensaje(request: Request):
    start_time = time.time()
    metrics['webhook_requests'] += 1
    
    # Leer body una sola vez
    raw_body = await request.body()

    # ============================================
    # SEGURIDAD: Validar firma en producción
    # ============================================
    if Config.IS_PRODUCTION and WHATSAPP_APP_SECRET:
        signature = request.headers.get("X-Hub-Signature-256")
        if signature and not verify_whatsapp_signature(raw_body, signature):
            logger.warning("Firma de WhatsApp inválida — webhook rechazado")
            raise HTTPException(status_code=401, detail="Invalid signature")

    # ============================================
    # RATE LIMITING: Prevenir abuso
    # ============================================
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(
        f"webhook:{client_ip}",
        Config.RATE_LIMIT_MESSAGES_PER_MINUTE,
        60
    ):
        metrics['rate_limited_requests'] += 1
        logger.warning(f"Rate limit excedido para IP: {client_ip}")
        return {"status": "rate_limited"}, 429

    try:
        data = json.loads(raw_body)

        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})

        if 'messages' in value:
            message = value['messages'][0]
            message_id = message.get('id')

            if message_id in PROCESSED_MESSAGES:
                return {"status": "already_processed"}

            PROCESSED_MESSAGES.append(message_id)

            numero_usuario = message['from']
            msg_type = message.get('type', 'text')
            if msg_type == 'interactive':
                interactive = message.get('interactive', {})
                if 'button_reply' in interactive:
                    texto_usuario = interactive['button_reply'].get('title', '')
                elif 'list_reply' in interactive:
                    texto_usuario = interactive['list_reply'].get('title', '')
                else:
                    texto_usuario = ''
            else:
                texto_usuario = message.get('text', {}).get('body', '')
            texto_lower = texto_usuario.lower()
            texto_menu = ""
            phone_number_id = value['metadata']['phone_number_id']

            # Mexico normalization
            if numero_usuario.startswith("521"):
                numero_usuario = numero_usuario.replace("521", "52", 1)

            # ============================================
            # PRIVACIDAD: Logs sanitizados
            # ============================================
            phone_sanitized = database.sanitize_phone(numero_usuario)
            message_preview = database.sanitize_message_preview(texto_usuario)
            logger.info(f"Mensaje de {phone_sanitized} para {phone_number_id}: {message_preview}")

            # 2. Get client data from DB
            client_data = database.get_client_by_phone_id(phone_number_id)

            if not client_data:
                logger.warning(f"Negocio no registrado: {phone_number_id}")
                return {"status": "unrecognized_client"}

            # ============================================
            # ROUTING: Manejar Demos en el mismo número
            # ============================================
            # Si es el número maestro de Zotek, permitimos enrutar a demos
            if phone_number_id == "980996958435648":
                                # Mapa de palabras clave a phone_number_id de los bots demo
                keyword_map = {
                    "clínica dental": "demo_dental",
                    "psicólogo": "demo_psychology",
                    "psicologo": "demo_psychology",
                    "restaurante": "demo_restaurant",
                    "salón de belleza": "demo_salon",
                    "belleza": "demo_salon",
                    "tienda de ropa": "demo_retail",
                    "ropa": "demo_retail",
                    "mente sana": "demo_psychology",
                    "gourmet": "demo_restaurant"
                }
                
                # 1. Detectar si el usuario quiere iniciar una nueva demo
                demo_found = False
                if any(k in texto_lower for k in ["quiero probar la demo de", "probar demo", "demo de"]):
                    for keyword, target_id in keyword_map.items():
                        if keyword in texto_lower:
                            DEMO_SESSIONS[numero_usuario] = target_id
                            client_data = database.get_client_by_phone_id(target_id)
                            logger.info(f"Iniciando sesión DEMO: {target_id} para {phone_sanitized}")
                            demo_found = True
                            break
                elif "reiniciar" in texto_lower:
                    if numero_usuario in DEMO_SESSIONS:
                        del DEMO_SESSIONS[numero_usuario]
                        logger.info(f"Sesión DEMO limpiada para {phone_sanitized}")
                        # Volver al client_data original (Zotek)
                        client_data = database.get_client_by_phone_id(phone_number_id)
                        demo_found = True # Para que no intente continuar una sesión demo
                
                # 2. Si no es un inicio, pero ya tiene una sesión activa, usar la data del bot demo
                if not demo_found and numero_usuario in DEMO_SESSIONS:
                    target_id = DEMO_SESSIONS[numero_usuario]
                    demo_client = database.get_client_by_phone_id(target_id)
                    if demo_client:
                        client_data = demo_client
                        logger.info(f"Continuando sesión DEMO: {target_id} para {phone_sanitized}")
                    else:
                        # Si por algo ya no existe el bot demo, limpiar sesión
                        del DEMO_SESSIONS[numero_usuario]

            # ============================================
            # MONETIZACIÓN: Verificar límite de mensajes
            # ============================================
            client_plan = client_data.get('plan', 'free')
            allowed, limit_msg = database.check_message_limit(client_data['id'], client_plan)
            if not allowed:
                logger.warning(f"Límite excedido para cliente {client_data['id']}: {limit_msg}")
                # Enviar mensaje de límite alcanzado
                whatsapp_service.enviar_mensaje_whatsapp(
                    numero=numero_usuario,
                    texto=f" Has alcanzado tu límite de mensajes este mes ({limit_msg}). Por favor contacta a soporte para actualizar tu plan.",
                    whatsapp_token=client_data['whatsapp_token'],
                    phone_number_id=client_data['phone_number_id']
                )
                return {"status": "limit_exceeded"}

            # 3. Procesar con Gemini (agente con herramientas e historial)
            resultado_ai = gemini.generar_respuesta_agente(
                texto_usuario,
                client_data,
                numero_usuario,
            )
            respuesta_ai = resultado_ai.get("text", "")
            tool_calls   = resultado_ai.get("tool_calls", [])

            # 4. Ejecutar herramientas que Gemini solicitó
            logger.info(f"[TOOLS] tool_calls={[t.get('name') for t in tool_calls]} | texto='{respuesta_ai[:60]}'")
            for tool in tool_calls:
                nombre = tool.get("name")
                args   = tool.get("args", {})
                logger.info(f"[TOOL] Ejecutando: {nombre} | args={dict(args)}")

                if nombre == "enviar_menu_interactivo":
                    whatsapp_service.enviar_menu_interactivo(
                        numero=numero_usuario,
                        texto=args.get("mensaje", "Elige una opción:"),
                        opciones=list(args.get("opciones", [])),
                        whatsapp_token=client_data['whatsapp_token'],
                        phone_number_id=client_data['phone_number_id'],
                    )

                elif nombre == "registrar_cita":
                    cita_id = database.save_appointment(
                        client_id=client_data['id'],
                        paciente_nombre=args.get("paciente_nombre", ""),
                        cliente_telefono=args.get("cliente_telefono", numero_usuario),
                        fecha_hora=args.get("fecha_hora", ""),
                        motivo=args.get("motivo", ""),
                    )
                    if cita_id:
                        confirmacion = (
                            f"✅ ¡Cita registrada!\n"
                            f"👤 {args.get('paciente_nombre', '')}\n"
                            f"📅 {args.get('fecha_hora', '')}\n"
                            f"📍 {args.get('motivo', 'Consulta')}\n\n"
                            f"Te enviaremos un recordatorio. ¡Hasta pronto!"
                        )
                        whatsapp_service.enviar_mensaje_whatsapp(
                            numero=numero_usuario,
                            texto=confirmacion,
                            whatsapp_token=client_data['whatsapp_token'],
                            phone_number_id=client_data['phone_number_id'],
                        )
                        respuesta_ai = ""  # La confirmación ya fue enviada

                elif nombre == "mostrar_horarios":
                    duracion = int(client_data.get("appointment_duration") or args.get("duracion_cita", 60))
                    todos_slots = database.get_available_slots_v2(client_data['id'], duracion_min=duracion)
                    libres = [s for s in todos_slots if not s["ocupado"]]
                    logger.info(f"[TOOL] mostrar_horarios total={len(todos_slots)} libres={len(libres)}")
                    if libres:
                        # Enviar todos los slots en una sola lista interactiva (máx 10)
                        opciones = [s["label"] for s in libres[:10]]
                        ok = whatsapp_service.enviar_lista(
                            numero=numero_usuario,
                            texto="📅 Horarios disponibles — ¿cuál te viene mejor?",
                            opciones=opciones,
                            titulo_boton="Ver horarios",
                            whatsapp_token=client_data['whatsapp_token'],
                            phone_number_id=client_data['phone_number_id'],
                        )
                        logger.info(f"[TOOL] enviar_lista horarios ok={ok}")
                    else:
                        whatsapp_service.enviar_mensaje_whatsapp(
                            numero=numero_usuario,
                            texto="Por el momento no hay horarios disponibles. Por favor contáctanos para agendar.",
                            whatsapp_token=client_data['whatsapp_token'],
                            phone_number_id=client_data['phone_number_id'],
                        )
                    respuesta_ai = ""

                elif nombre == "llamar_ahora":
                    motivo = args.get("motivo", "consulta")
                    nombre_bot = client_data.get("name", "nuestro equipo")
                    aviso = f"📞 Estamos iniciando una llamada a tu número. ¡Un momento!"
                    whatsapp_service.enviar_mensaje_whatsapp(
                        numero=numero_usuario,
                        texto=aviso,
                        whatsapp_token=client_data['whatsapp_token'],
                        phone_number_id=client_data['phone_number_id'],
                    )
                    numero_e164 = numero_usuario if numero_usuario.startswith("+") else f"+{numero_usuario}"
                    twilio_service.llamar_inmediatamente(
                        numero_destino=numero_e164,
                        mensaje_voz=f"Hola, te llama {nombre_bot} por tu solicitud de {motivo}. Un momento por favor.",
                    )
                    respuesta_ai = ""  # El aviso ya fue enviado

                elif nombre == "capturar_lead":
                    database.save_lead(
                        client_id=client_data['id'],
                        nombre=args.get("nombre", ""),
                        telefono=numero_usuario,
                        interes=args.get("interes", ""),
                    )

            # 5. Enviar respuesta de texto si hay
            if respuesta_ai and respuesta_ai.strip():
                send_success = whatsapp_service.enviar_mensaje_whatsapp(
                    numero=numero_usuario,
                    texto=respuesta_ai,
                    whatsapp_token=client_data['whatsapp_token'],
                    phone_number_id=client_data['phone_number_id'],
                )
            else:
                send_success = True
            
            if not send_success:
                metrics['whatsapp_errors'] += 1
                logger.error(f"Error enviando WhatsApp a {phone_sanitized}")
            else:
                logger.info(f"Respuesta enviada con éxito a {phone_sanitized}")

            # ============================================
            # TRACKING: Registrar mensaje para métricas
            # ============================================
            database.track_message(
                client_id=client_data['id'],
                direction="outbound",
                phone_number=numero_usuario
            )
            database.track_message(
                client_id=client_data['id'],
                direction="inbound",
                phone_number=numero_usuario
            )
            
            # ============================================
            # MÉTRICAS: Actualizar estadísticas
            # ============================================
            metrics['total_messages'] += 1
            metrics['messages_by_client'][client_data['id']] += 1
            
            response_time_ms = (time.time() - start_time) * 1000
            # Promedio móvil exponencial
            metrics['avg_response_time_ms'] = (
                metrics['avg_response_time_ms'] * 0.9 + response_time_ms * 0.1
            )

    except Exception as e:
        metrics['gemini_errors'] += 1
        logger.error(f"Error en Webhook: {e}")

    return {"status": "ok"}


# ============================================
# SEGURIDAD: Helpers
# ============================================

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_client_access(client_id: int, current_user: str):
    """Verifica que el usuario autenticado tiene acceso al cliente solicitado.
    Los admins tienen acceso total. Los clientes solo a sus propios datos."""
    if current_user == ADMIN_EMAIL:
        return
    client = database.get_client_by_id(client_id)
    if not client or client.get("email", "").lower() != current_user.lower():
        raise HTTPException(status_code=403, detail="Acceso denegado a este cliente")


def send_security_code(email: str, code: str):
    if not EMAIL_PASSWORD:
        logger.error("EMAIL_APP_PASSWORD no configurada en .env")
        return False

    logger.info(f"Enviando código de verificación a {email}")
    
    try:
        import smtplib
        msg = MIMEText(f"Tu código de acceso para Zotek Admin es: {code}\nExpira en 10 minutos.")
        msg['Subject'] = f"{code} es tu código de verificación de Zotek"
        msg['From'] = ADMIN_EMAIL
        msg['To'] = email

        # Using SMTP with STARTTLS on 587 (Often more reliable for Gmail)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(ADMIN_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        import traceback
        logger.error(f"Error enviando email: {e}")
        return False


# ============================================
# MÉTRICAS ENDPOINT
# ============================================
@app.get("/api/metrics")
async def get_metrics(current_user: str = Depends(get_current_user)):
    """
    Retorna métricas del sistema para el dashboard admin.
    
    Incluye:
    - Total de mensajes
    - Tiempo promedio de respuesta
    - Errores de Gemini y WhatsApp
    - Estadísticas por cliente
    """
    uptime_seconds = time.time() - metrics['start_time']
    
    # Obtener estadísticas globales de la BD
    db_stats = database.get_message_stats()
    
    return {
        'uptime_seconds': round(uptime_seconds, 2),
        'uptime_human': f"{uptime_seconds / 3600:.2f} horas",
        'total_messages': metrics['total_messages'],
        'avg_response_time_ms': round(metrics['avg_response_time_ms'], 2),
        'gemini_errors': metrics['gemini_errors'],
        'whatsapp_errors': metrics['whatsapp_errors'],
        'webhook_requests': metrics['webhook_requests'],
        'rate_limited_requests': metrics['rate_limited_requests'],
        'db_stats': db_stats,
        'messages_by_client': dict(metrics['messages_by_client']),
    }


@app.get("/api/metrics/usage")
async def get_usage_metrics(client_id: int = None, current_user: str = Depends(get_current_user)):
    """
    Retorna métricas de uso para facturación.
    
    Args:
        client_id: ID del cliente (None para todos)
    """
    if client_id:
        client_data = database.get_client_by_id(client_id)
        if not client_data:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        plan = client_data.get('plan', 'free')
        monthly_count = database.get_monthly_message_count(client_id)
        allowed, message = database.check_message_limit(client_id, plan)
        
        return {
            'client_id': client_id,
            'client_name': client_data.get('name'),
            'plan': plan,
            'monthly_messages': monthly_count,
            'limit_allowed': allowed,
            'message': message,
        }
    else:
        # Estadísticas de todos los clientes
        clients = database.list_clients()
        usage_data = []
        
        for client in clients:
            monthly_count = database.get_monthly_message_count(client['id'])
            plan = client.get('plan', 'free')
            allowed, message = database.check_message_limit(client['id'], plan)
            
            usage_data.append({
                'client_id': client['id'],
                'client_name': client.get('name'),
                'plan': plan,
                'monthly_messages': monthly_count,
                'limit_allowed': allowed,
            })
        
        return {'clients': usage_data}


# --- Routes ---

# --- Auth API ---

@app.post("/api/auth/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    if email != ADMIN_EMAIL or password != getattr(Config, 'ADMIN_PASSWORD', None):
        logger.warning(f"Login fallido para: {email}")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    logger.info(f"Login exitoso para: {email}")
    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me")
async def get_me(current_user: str = Depends(get_current_user)):
    return {
        "email": current_user,
        "role": "admin" if current_user == ADMIN_EMAIL else "client"
    }

# --- Protected Admin API ---

@app.get("/api/clients")
async def list_clients(current_user: str = Depends(get_current_user)):
    return database.list_clients()

@app.post("/api/clients")
async def create_client(request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()
    # Map 'menu' from frontend to 'menu_json' in DB
    if 'menu' in data:
        data['menu_json'] = json.dumps(data.pop('menu'))
        
    if database.add_client(data):
        return {"status": "created"}
    raise HTTPException(status_code=400, detail="Error creating client")

@app.post("/api/clients/{client_id}/duplicate")
async def duplicate_client(client_id: str, current_user: str = Depends(get_current_user)):
    try:
        client_id_int = int(client_id)
    except (ValueError, TypeError):
        client_id_int = client_id
        
    new_client = database.duplicate_client(client_id_int)
    if new_client:
        return {"status": "duplicated", "new_client_id": new_client["id"]}
    raise HTTPException(status_code=400, detail="Error duplicating client")

@app.put("/api/clients/{client_id}")
async def update_client(client_id: str, request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()

    # Map 'menu' from frontend to 'menu_json' in DB
    if 'menu' in data:
        try:
            data['menu_json'] = json.dumps(data.pop('menu'))
        except Exception as e:
            logger.error(f"Error serializando menú para cliente {client_id}: {e}")
            raise HTTPException(status_code=400, detail="Error al procesar menú")

    # Convertir a int si es un ID numérico
    try:
        client_id_int = int(client_id)
    except (ValueError, TypeError):
        client_id_int = client_id

    if database.update_client(client_id_int, data):
        return {"status": "updated"}
    else:
        logger.error(f"database.update_client devolvió False para cliente {client_id_int}")
        raise HTTPException(status_code=400, detail="Error updating client")

@app.get("/api/clients/{client_id}/menu")
async def get_client_menu(client_id: str, current_user: str = Depends(get_current_user)):
    """Obtiene la configuración del menú de un cliente (soporta IDs numéricos y strings como demo_restaurant)."""
    # Intentar obtener por ID numérico primero, luego por string
    client = None

    # Intentar como entero
    try:
        client_id_int = int(client_id)
        client = database.get_client_by_id(client_id_int)
    except (ValueError, TypeError):
        pass

    # Si no se encontró como entero, intentar como phone_number_id
    if not client:
        client = database.get_client_by_phone_id(client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    menu_data = client.get("menu_json")
    if menu_data:
        try:
            if isinstance(menu_data, str):
                return json.loads(menu_data)
            else:
                return menu_data
        except:
            return {"options": []}
    return {"options": []}

@app.post("/api/clients/{client_id}/reset")
async def reset_client(client_id: str, current_user: str = Depends(get_current_user)):
    """Resetea un cliente demo, eliminando sus personalizaciones en BD."""
    # Convertir a int si es un ID numérico
    try:
        client_id_int = int(client_id)
    except (ValueError, TypeError):
        client_id_int = client_id  # Usar el string original si no es numérico

    if database.delete_client_db_entry(client_id_int):
        return {"status": "reset_successful"}
    raise HTTPException(status_code=400, detail="Error resetting client")

@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: str, current_user: str = Depends(get_current_user)):
    """Elimina permanentemente un cliente de la base de datos."""
    # Convertir a int si es un ID numérico
    try:
        client_id_int = int(client_id)
    except (ValueError, TypeError):
        client_id_int = client_id

    # Prevenir eliminación de demos hardcodeados
    if client_id_int in [9991, 9992, 9993]:
        raise HTTPException(status_code=403, detail="No se pueden eliminar clientes de demostración")

    if database.delete_client_db_entry(client_id_int):
        return {"status": "deleted"}
    else:
        logger.error(f"Fallo al eliminar cliente {client_id_int}")
        raise HTTPException(status_code=400, detail="Error deleting client")

@app.get("/api/clients/{client_id}")
async def get_client(client_id: int, current_user: str = Depends(get_current_user)):
    client = database.get_client_by_id(client_id)
    if client:
        return client
    raise HTTPException(status_code=404, detail="Client not found")

@app.get("/api/clients/{client_id}/documents")
async def list_documents(client_id: int, current_user: str = Depends(get_current_user)):
    return database.list_client_documents(client_id)

@app.get("/api/clients/{client_id}/schedules")
async def get_schedules(client_id: int, current_user: str = Depends(get_current_user)):
    return database.get_client_schedules(client_id)

@app.post("/api/clients/{client_id}/schedules")
async def save_schedules(client_id: int, request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()
    schedules = data.get("schedules", [])
    if database.save_client_schedules(client_id, schedules):
        return {"status": "ok"}
    raise HTTPException(status_code=500, detail="Error guardando horarios.")

@app.get("/api/clients/{client_id}/available-slots")
async def get_available_slots(client_id: int, current_user: str = Depends(get_current_user)):
    client = database.get_client_by_id(client_id)
    duracion = int(client.get("appointment_duration") or 60) if client else 60
    slots = database.get_available_slots_v2(client_id, duracion_min=duracion)
    return {"slots": slots}

@app.post("/api/clients/{client_id}/upload-pdf")
async def upload_pdf(client_id: int, request: Request, current_user: str = Depends(get_current_user)):
    import io
    try:
        from pypdf import PdfReader
    except ImportError:
        raise HTTPException(status_code=500, detail="Biblioteca pypdf no instalada. Ejecuta: pip install pypdf")

    form = await request.form()
    file = form.get("file")

    if not file or not hasattr(file, "filename"):
        raise HTTPException(status_code=400, detail="No se recibió ningún archivo.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"Solo se permiten archivos PDF. Recibido: {file.filename}")

    contents = await file.read()
    if not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido.")

    try:
        reader = PdfReader(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo PDF: {str(e)}")

    text_content = ""
    for page in reader.pages:
        try:
            extracted = page.extract_text()
            if extracted:
                text_content += extracted + "\n"
        except Exception:
            continue

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF. El archivo parece contener solo imágenes.")

    result = database.add_knowledge_entry(client_id, text_content, source_file=file.filename)
    if result:
        return {"status": "success", "message": f"PDF '{file.filename}' procesado.", "extracted_length": len(text_content), "pages": len(reader.pages)}
    raise HTTPException(status_code=500, detail="Error guardando en la base de datos.")

@app.delete("/api/clients/{client_id}/documents/{doc_id}")
async def delete_document(client_id: int, doc_id: int, current_user: str = Depends(get_current_user)):
    if database.delete_knowledge_entry(client_id, doc_id):
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Error eliminando documento.")


# ============================================
# ENDPOINTS DE EMAIL CONFIGURATION
# ============================================

@app.get("/api/clients/{client_id}/email-config")
async def get_email_config(client_id: int, current_user: str = Depends(get_current_user)):
    """Obtiene la configuración de email de un cliente"""
    verify_client_access(client_id, current_user)
    client = database.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return {
        "email_smtp_server": client.get('email_smtp_server', 'smtp.gmail.com'),
        "email_smtp_port": client.get('email_smtp_port', 587),
        "email_user": client.get('email_user', ''),
        "email_from_name": client.get('email_from_name', ''),
        "email_notifications_enabled": client.get('email_notifications_enabled', False),
        "configured": bool(client.get('email_user'))
    }

@app.post("/api/clients/{client_id}/email-config")
async def update_email_config(client_id: int, request: Request, current_user: str = Depends(get_current_user)):
    """Actualiza la configuración de email de un cliente"""
    verify_client_access(client_id, current_user)
    data = await request.json()

    # Actualizar configuración
    config = {
        'email_smtp_server': data.get('smtp_server', 'smtp.gmail.com'),
        'email_smtp_port': data.get('smtp_port', 587),
        'email_user': data.get('email_user', ''),
        'email_password': data.get('email_password', ''),
        'email_from_name': data.get('email_from_name', ''),
        'email_notifications_enabled': data.get('notifications_enabled', False)
    }

    if database.update_client(client_id, config):
        return {"status": "updated", "message": "Configuración de email guardada"}
    raise HTTPException(status_code=400, detail="Error al guardar configuración")

@app.post("/api/clients/{client_id}/email-test")
async def test_email_config(client_id: int, request: Request, current_user: str = Depends(get_current_user)):
    """Prueba la configuración de email enviando un email de prueba"""
    verify_client_access(client_id, current_user)
    import smtplib
    from email.mime.text import MIMEText

    data = await request.json()
    test_email = data.get('email', '')

    if not test_email:
        raise HTTPException(status_code=400, detail="Email de prueba requerido")

    client = database.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Obtener configuración
    smtp_server = client.get('email_smtp_server', 'smtp.gmail.com')
    smtp_port = client.get('email_smtp_port', 587)
    email_user = client.get('email_user', '')
    email_password = client.get('email_password', '')
    email_from_name = client.get('email_from_name', '')

    if not email_user or not email_password:
        raise HTTPException(status_code=400, detail="Configuración de email incompleta")

    try:
        # Crear mensaje
        msg = MIMEText("Esta es una prueba de configuración de email de Zotek IA.\n\n¡Todo funciona correctamente!", 'plain', 'utf-8')
        msg['Subject'] = "✅ Configuración de email exitosa - Zotek IA"
        msg['From'] = f"{email_from_name} <{email_user}>"
        msg['To'] = test_email

        # Conectar y enviar
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()

        server.login(email_user, email_password)
        server.sendmail(email_user, [test_email], msg.as_string())
        server.quit()

        return {"status": "success", "message": "Email de prueba enviado correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al enviar email de prueba")


# ============================================
# ENDPOINTS DE LEAD TRACKING
# ============================================

@app.get("/api/clients/{client_id}/leads")
async def get_client_leads(client_id: int, status: str = None, limit: int = 50,
                          current_user: str = Depends(get_current_user)):
    """Obtiene los leads de un cliente"""
    verify_client_access(client_id, current_user)
    conn = database.get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = "SELECT * FROM lead_tracking WHERE client_id = %s"
        params = [client_id]

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY last_interaction DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        leads = cursor.fetchall()
        cursor.close()
        return {"leads": [dict(lead) for lead in leads], "total": len(leads)}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener leads")
    finally:
        conn.close()

@app.get("/api/clients/{client_id}/leads/cold")
async def get_cold_leads(client_id: int, hours: int = 24,
                         current_user: str = Depends(get_current_user)):
    """Obtiene leads fríos (no han respondido en X horas)"""
    verify_client_access(client_id, current_user)
    try:
        conn = database.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT lt.*, c.name as client_name, c.phone_number_id as business_phone
                FROM lead_tracking lt
                JOIN clients c ON lt.client_id = c.id
                WHERE lt.client_id = %s
                  AND lt.status IN ('new', 'contacted', 'cold')
                  AND lt.last_interaction < CURRENT_TIMESTAMP - INTERVAL '%s hours'
                ORDER BY lt.last_interaction ASC
            """, (client_id, hours))
            leads = cursor.fetchall()
            cursor.close()
            return {"leads": [dict(lead) for lead in leads], "total": len(leads), "hours": hours}
        finally:
            conn.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener leads fríos")


# ============================================
# ENDPOINTS DE APPOINTMENTS
# ============================================

@app.get("/api/appointments")
async def get_all_appointments(current_user: str = Depends(get_current_user)):
    """Retorna todas las citas de todos los clientes (para el dashboard admin)."""
    return database.get_all_appointments()

@app.get("/api/clients/{client_id}/appointments")
async def get_client_appointments(client_id: int, current_user: str = Depends(get_current_user)):
    """Retorna las citas agendadas de un cliente desde la tabla citas (para el dashboard admin)."""
    return database.get_appointments_by_client(client_id)

@app.post("/api/clients/{client_id}/appointments")
async def create_appointment(client_id: int, request: Request,
                            current_user: str = Depends(get_current_user)):
    """Crea una nueva cita"""
    verify_client_access(client_id, current_user)
    data = await request.json()

    # Parsear fecha
    try:
        from datetime import datetime
        appointment_date = datetime.fromisoformat(data.get('appointment_date'))
    except:
        raise HTTPException(status_code=400, detail="Fecha inválida. Usa formato ISO")

    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments
            (client_id, phone_number, appointment_date, customer_name, notes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (client_id, data.get('phone_number', ''), appointment_date,
              data.get('customer_name', ''), data.get('notes', '')))
        appointment_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"status": "created", "appointment_id": appointment_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error creando la cita")
    finally:
        conn.close()

@app.post("/api/clients/{client_id}/appointments/{appointment_id}/confirm")
async def confirm_appointment(client_id: int, appointment_id: int,
                             current_user: str = Depends(get_current_user)):
    """Confirma una cita"""
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments SET status = 'confirmed', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (appointment_id,))
        conn.commit()
        cursor.close()
        return {"status": "confirmed", "message": "Cita confirmada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error confirmando la cita")
    finally:
        conn.close()

@app.post("/api/clients/{client_id}/appointments/{appointment_id}/cancel")
async def cancel_appointment(client_id: int, appointment_id: int,
                            current_user: str = Depends(get_current_user)):
    """Cancela una cita"""
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (appointment_id,))
        conn.commit()
        cursor.close()
        return {"status": "cancelled", "message": "Cita cancelada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error cancelando la cita")
    finally:
        conn.close()



# ============================================
# VAPI - SERVICIO DE LLAMADAS DE RECORDATORIO
# ============================================

@app.post("/api/cron/reminders")
async def cron_reminders(request: Request):
    """
    Endpoint para cron-job.org. Protegido por CRON_SECRET en header X-Cron-Secret.
    Envía recordatorios de citas del día siguiente por WhatsApp a todos los pacientes.
    """
    secret = request.headers.get("X-Cron-Secret", "")
    if not Config.CRON_SECRET or secret != Config.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    _ensure_initialized()

    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_end = tomorrow + " 23:59"

    try:
        from psycopg2.extras import RealDictCursor as RDC
        conn = database.get_connection()
        cursor = conn.cursor(cursor_factory=RDC)
        cursor.execute("""
            SELECT c.id AS cita_id, c.paciente_nombre, c.cliente_telefono,
                   c.fecha_hora, c.motivo, c.client_id,
                   cl.name AS client_name, cl.phone_number_id
            FROM citas c
            JOIN clients cl ON cl.id = c.client_id
            WHERE c.fecha_hora::text >= %s AND c.fecha_hora::text <= %s
              AND (c.reminder_status IS NULL OR c.reminder_status = 'pending')
        """, (tomorrow, tomorrow_end))
        citas = [dict(r) for r in cursor.fetchall()]
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"cron_reminders DB error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    enviados = 0
    errores = 0
    for cita in citas:
        try:
            client_data = database.get_client_by_id(cita["client_id"])
            token_wa = client_data["whatsapp_token"]
            fecha_legible = str(cita["fecha_hora"])[:16]
            texto = (
                f"👋 Hola {cita['paciente_nombre']}, te recordamos tu cita con "
                f"*{cita['client_name']}* mañana {fecha_legible}."
            )
            if cita.get("motivo"):
                texto += f"\n📋 Motivo: {cita['motivo']}"
            texto += "\n\nSi necesitas cancelar o cambiar, responde este mensaje."

            ok = whatsapp_service.enviar_mensaje_whatsapp(
                numero=cita["cliente_telefono"],
                texto=texto,
                whatsapp_token=token_wa,
                phone_number_id=cita["phone_number_id"],
            )
            if ok:
                enviados += 1
                conn2 = database.get_connection()
                cur2 = conn2.cursor()
                cur2.execute(
                    "UPDATE citas SET reminder_status = 'sent' WHERE id = %s",
                    (cita["cita_id"],)
                )
                conn2.commit()
                cur2.close()
                conn2.close()
            else:
                errores += 1
        except Exception as e:
            logger.error(f"cron_reminders cita {cita['cita_id']}: {e}")
            errores += 1

    logger.info(f"cron_reminders: {enviados} enviados, {errores} errores")
    return {"status": "ok", "enviados": enviados, "errores": errores, "total": len(citas)}

@app.post("/api/reminders/run")
async def run_reminder_job(current_user: str = Depends(get_current_user)):
    """
    Ejecuta el trabajo de recordatorios: busca citas próximas (24h) y
    llama a los pacientes usando VAPI en nombre del cliente profesional.
    
    Puede ser invocado por:
    - Cloud Scheduler (CRON) cada hora
    - El administrador desde el panel manualmente
    
    Solo aplica a clientes con plan 'pro' o 'enterprise'.
    """
    from .services.vapi_service import vapi
    from .services.calendar_service import (
        get_upcoming_appointments_for_reminders,
        format_fecha_legible,
    )

    if not Config.VAPI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="VAPI no configurado. Agrega VAPI_API_KEY en .env"
        )

    resultados = {
        "citas_encontradas": 0,
        "llamadas_iniciadas": 0,
        "errores": 0,
        "detalle": []
    }

    citas = get_upcoming_appointments_for_reminders(
        hours_ahead=Config.VAPI_REMINDER_HOURS_AHEAD
    )
    resultados["citas_encontradas"] = len(citas)

    for cita in citas:
        cita_id = cita["cita_id"]
        numero = cita.get("cliente_telefono", "")
        nombre_paciente = cita.get("paciente_nombre", "Paciente")
        nombre_profesional = cita.get("client_name", "el profesional")
        fecha_raw = cita.get("fecha_hora", "")
        motivo = cita.get("motivo")

        if not numero:
            logger.warning(f"Cita {cita_id}: sin número de teléfono, omitiendo.")
            resultados["errores"] += 1
            resultados["detalle"].append({"cita_id": cita_id, "error": "sin_telefono"})
            continue

        # Marcar como 'llamando' antes de disparar
        database.update_appointment_reminder_status(cita_id, "llamando")

        fecha_legible = format_fecha_legible(fecha_raw)

        resultado_vapi = vapi.iniciar_llamada_recordatorio(
            numero_paciente=numero,
            nombre_paciente=nombre_paciente,
            fecha_cita=fecha_legible,
            nombre_profesional=nombre_profesional,
            motivo=motivo,
        )

        if resultado_vapi.get("success"):
            call_id = resultado_vapi.get("call_id")
            database.update_appointment_reminder_status(cita_id, "llamado", call_id)
            resultados["llamadas_iniciadas"] += 1
            resultados["detalle"].append({"cita_id": cita_id, "call_id": call_id, "status": "ok"})
        else:
            error_msg = resultado_vapi.get("error", "desconocido")
            database.update_appointment_reminder_status(cita_id, "fallido")
            resultados["errores"] += 1
            resultados["detalle"].append({"cita_id": cita_id, "error": error_msg})

    logger.info(f"VAPI CRON: {resultados['llamadas_iniciadas']} llamadas / {resultados['errores']} errores")
    return resultados


@app.post("/api/vapi/webhook")
async def vapi_webhook(request: Request):
    """
    Webhook que VAPI llama cuando termina una llamada.
    Actualiza el estado final de la cita en la base de datos.
    
    VAPI envía: call_id, status ('ended', 'failed'), summary, transcript, etc.
    """
    if VAPI_WEBHOOK_SECRET:
        auth = request.headers.get("x-vapi-secret", "")
        if not hmac.compare_digest(auth, VAPI_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        data = await request.json()
        call_id = data.get("id") or data.get("call", {}).get("id")
        status = data.get("status", "")
        end_reason = data.get("endedReason", "")

        logger.info(f"VAPI Webhook: call_id={call_id}, status={status}, end_reason={end_reason}")

        if call_id:
            final_status = "llamado" if status in ("ended",) else "fallido"
            conn = database.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE citas SET reminder_status = %s WHERE vapi_call_id = %s
                """, (final_status, call_id))
                conn.commit()
                cursor.close()
                logger.info(f"VAPI Webhook: cita actualizada a '{final_status}' para call_id={call_id}")
            except Exception as db_err:
                logger.error(f"VAPI Webhook DB error: {db_err}")
            finally:
                conn.close()

        return {"status": "received"}
    except Exception as e:
        logger.error(f"VAPI Webhook Error: {e}")
        return {"status": "error"}


@app.post("/api/clients/{client_id}/appointments")
async def create_appointment(client_id: int, request: Request,
                             current_user: str = Depends(get_current_user)):
    """
    Crea una nueva cita para un cliente.
    El bot de WhatsApp también puede crear citas cuando registra una reserva.
    """
    data = await request.json()
    paciente_nombre = data.get("paciente_nombre", "")
    cliente_telefono = data.get("cliente_telefono", "")
    fecha_hora = data.get("fecha_hora", "")
    motivo = data.get("motivo")

    if not all([paciente_nombre, cliente_telefono, fecha_hora]):
        raise HTTPException(
            status_code=400,
            detail="paciente_nombre, cliente_telefono y fecha_hora son requeridos"
        )

    cita_id = database.save_appointment(
        client_id=client_id,
        paciente_nombre=paciente_nombre,
        cliente_telefono=cliente_telefono,
        fecha_hora=fecha_hora,
        motivo=motivo,
    )
    if cita_id:
        return {"status": "created", "cita_id": cita_id}
    raise HTTPException(status_code=400, detail="Error creando la cita")


@app.post("/api/reminders/test-call")
async def test_vapi_call(request: Request, current_user: str = Depends(get_current_user)):
    """
    Endpoint de prueba para verificar la conexión con VAPI.
    Permite al admin hacer una llamada de prueba sin necesidad de una cita real.
    """
    from .services.vapi_service import vapi

    data = await request.json()
    numero = data.get("numero")  # ej. '+5215512345678'
    if not numero:
        raise HTTPException(status_code=400, detail="'numero' es requerido (formato: +52155...)")

    resultado = vapi.iniciar_llamada_recordatorio(
        numero_paciente=numero,
        nombre_paciente=data.get("nombre_paciente", "Usuario de Prueba"),
        fecha_cita=data.get("fecha_cita", "mañana a las 3 de la tarde"),
        nombre_profesional=data.get("nombre_profesional", "la Dra. González"),
        nombre_consultorio=data.get("nombre_consultorio", "el consultorio"),
    )
    return resultado


# Static Files Mounts (After all specific routes)
if os.path.exists(WWW_DIR):
    logger.info(f"Mounting static files from {WWW_DIR}")
    app.mount("/", StaticFiles(directory=WWW_DIR, html=True), name="root")
else:
    logger.warning(f"Skipping static files mount (Directory not found: {WWW_DIR})")

# Production entry point handled by Firebase or Uvicorn from shell
