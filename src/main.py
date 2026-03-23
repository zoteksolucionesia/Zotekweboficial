# Deploy Trigger: Force redeploy to fix persistent NameError in production.
# SaaS Improvements: Security, caching, metrics, conversation history
import os
import json
import random
import smtplib
import hmac
import hashlib
import time
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from collections import deque, defaultdict
from dotenv import load_dotenv
from typing import Dict, Any

# Local imports
from . import database
from .config import Config
from .services import whatsapp_service
from .services.gemini_service import GeminiEngine

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

print(f"--- SERVER STARTUP DIAGNOSTICS ---")
print(f"BASE_DIR: {BASE_DIR}")
print(f"WWW_DIR: {WWW_DIR}")
print(f"ADMIN_DIR: {ADMIN_DIR}")
print(f"Rate limiting: {Config.RATE_LIMIT_MESSAGES_PER_MINUTE}/min")
print(f"Metrics tracking: Enabled")
print(f"----------------------------------")

app = FastAPI()

# Initialize Database Schema
database.init_db()

@app.exception_handler(404)
async def custom_404_handler(request: Request, __):
    print(f"404 Error: {request.url.path}")
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
def verify_whatsapp_signature(request: Request, expected_signature: str) -> bool:
    """
    Verifica que el webhook viene realmente de WhatsApp.
    
    Args:
        request: Request de FastAPI
        expected_signature: Firma esperada del header X-Hub-Signature-256
    
    Returns:
        True si la firma es válida, False si no
    """
    if not WHATSAPP_APP_SECRET:
        return True  # Skip validation if secret not configured
    
    try:
        # Obtener body raw (necesario para verificar firma)
        body = request.scope.get('body', b'')
        
        # Calcular firma HMAC-SHA256
        signature = hmac.new(
            WHATSAPP_APP_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        expected_sig_value = expected_signature.replace('sha256=', '')
        
        # Comparar de manera segura contra timing attacks
        return hmac.compare_digest(signature, expected_sig_value)
    except Exception as e:
        print(f" ERROR verificando firma WhatsApp: {e}")
        return False


# Lazy initialization using app events or on first request to ensure DB is ready
@app.on_event("startup")
async def startup_event():
    if not os.environ.get('K_SERVICE'):
        database.init_db()

    global gemini
    gemini = GeminiEngine(api_key=GEMINI_API_KEY)

@app.get("/webhook")
async def verify_webhook(request: Request):
    token = request.query_params.get(Config.WEBHOOK_VERIFY_TOKEN_PARAM)
    if token == VERIFY_TOKEN:
        challenge = request.query_params.get(Config.WEBHOOK_CHALLENGE_PARAM)
        return int(challenge) if challenge else "Ok"
    return "Error auth", 403

@app.post("/webhook")
async def recibir_mensaje(request: Request):
    start_time = time.time()
    metrics['webhook_requests'] += 1
    
    # ============================================
    # SEGURIDAD: Validar firma en producción
    # ============================================
    if Config.IS_PRODUCTION and WHATSAPP_APP_SECRET:
        signature = request.headers.get("X-Hub-Signature-256")
        if signature and not verify_whatsapp_signature(request, signature):
            print(" Firma de WhatsApp inválida")
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
        print(f" Rate limit excedido para IP: {client_ip}")
        return {"status": "rate_limited"}, 429
    
    try:
        data = await request.json()

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
            texto_usuario = message.get('text', {}).get('body', "")
            texto_menu = ""  # Default to empty string to avoid NameError
            phone_number_id = value['metadata']['phone_number_id']

            # Mexico normalization
            if numero_usuario.startswith("521"):
                numero_usuario = numero_usuario.replace("521", "52", 1)

            # ============================================
            # PRIVACIDAD: Logs sanitizados
            # ============================================
            phone_sanitized = database.sanitize_phone(numero_usuario)
            message_preview = database.sanitize_message_preview(texto_usuario)
            print(f"📩 Mensaje de {phone_sanitized} para {phone_number_id}: {message_preview}")

            # 2. Get client data from DB
            client_data = database.get_client_by_phone_id(phone_number_id)

            if not client_data:
                print(f" Negocio no registrado: {phone_number_id}")
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
                            print(f" Iniciando sesión DEMO: {target_id} para {phone_sanitized}")
                            demo_found = True
                            break
                elif "reiniciar" in texto_lower:
                    if numero_usuario in DEMO_SESSIONS:
                        del DEMO_SESSIONS[numero_usuario]
                        print(f"🧹 Sesión DEMO limpiada para {phone_sanitized}")
                        # Volver al client_data original (Zotek)
                        client_data = database.get_client_by_phone_id(phone_number_id)
                        demo_found = True # Para que no intente continuar una sesión demo
                
                # 2. Si no es un inicio, pero ya tiene una sesión activa, usar la data del bot demo
                if not demo_found and numero_usuario in DEMO_SESSIONS:
                    target_id = DEMO_SESSIONS[numero_usuario]
                    demo_client = database.get_client_by_phone_id(target_id)
                    if demo_client:
                        client_data = demo_client
                        print(f"🔄 Continuando sesión DEMO: {target_id} para {phone_sanitized}")
                    else:
                        # Si por algo ya no existe el bot demo, limpiar sesión
                        del DEMO_SESSIONS[numero_usuario]

            # ============================================
            # MONETIZACIÓN: Verificar límite de mensajes
            # ============================================
            client_plan = client_data.get('plan', 'free')
            allowed, limit_msg = database.check_message_limit(client_data['id'], client_plan)
            if not allowed:
                print(f" Límite excedido para cliente {client_data['id']}: {limit_msg}")
                # Enviar mensaje de límite alcanzado
                whatsapp_service.enviar_mensaje_whatsapp(
                    numero=numero_usuario,
                    texto=f" Has alcanzado tu límite de mensajes este mes ({limit_msg}). Por favor contacta a soporte para actualizar tu plan.",
                    whatsapp_token=client_data['whatsapp_token'],
                    phone_number_id=client_data['phone_number_id']
                )
                return {"status": "limit_exceeded"}

            # 3. Process with Gemini (con caché e historial)
            respuesta_ai = gemini.generar_respuesta(
                texto_usuario, 
                client_data, 
                numero_usuario,
                usar_historial=True  # Usar historial de conversación
            )

            # 4. Send via WhatsApp
            send_success = whatsapp_service.enviar_mensaje_whatsapp(
                numero=numero_usuario,
                texto=respuesta_ai,
                whatsapp_token=client_data['whatsapp_token'],
                phone_number_id=client_data['phone_number_id']
            )
            
            if not send_success:
                metrics['whatsapp_errors'] += 1
                print(f" Error enviando WhatsApp a {phone_sanitized}")
            else:
                print(f" Respuesta enviada con éxito a {phone_sanitized}")

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
        print(f"🔥 Error en Webhook: {e}")

    return {"status": "ok"}


# ============================================
# SEGURIDAD: Helpers
# ============================================

def create_access_token(data: dict, expires_delta: timedelta = None):
    print(f"🔑 Generating access token for: {data.get('sub')}")
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"DEBUG: Token generated. Secret Key length: {len(SECRET_KEY)}")
    return token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"🕵 Validating token: {token[:10]}...{token[-10:] if len(token) > 20 else ''}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        print(f" Token decoded successfully for: {email}")
        if email is None:
            print(" Token payload missing 'sub'")
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError as e:
        print(f" JWT Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def send_security_code(email: str, code: str):
    if not EMAIL_PASSWORD:
        print(" ERROR: EMAIL_APP_PASSWORD no configurada en .env")
        return False
    
    print(f"📧 Intentando enviar email a {email}...")
    print(f"DEBUG: Enviando desde {ADMIN_EMAIL} (Pass length: {len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 0})")
    
    try:
        import smtplib
        msg = MIMEText(f"Tu código de acceso para Zotek Admin es: {code}\nExpira en 10 minutos.")
        msg['Subject'] = f"{code} es tu código de verificación de Zotek"
        msg['From'] = ADMIN_EMAIL
        msg['To'] = email

        # Using SMTP with STARTTLS on 587 (Often more reliable for Gmail)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.set_debuglevel(1) # Extra verbosity in logs
            server.starttls()
            server.login(ADMIN_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        import traceback
        print(f" Error enviando email: {e}")
        traceback.print_exc()
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

@app.get("/debug-paths")
async def debug_paths():
    return {
        "BASE_DIR": BASE_DIR,
        "WWW_DIR": WWW_DIR,
        "ADMIN_DIR": ADMIN_DIR,
        "index_exists": os.path.exists(os.path.join(WWW_DIR, "index.html")),
        "admin_index_exists": os.path.exists(os.path.join(ADMIN_DIR, "index.html")),
        "login_exists": os.path.exists(os.path.join(ADMIN_DIR, "login.html"))
    }

# --- Auth API ---

@app.post("/api/auth/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    print(f"📩 Login attempt: Email={email}")
    
    if email != ADMIN_EMAIL or password != getattr(Config, 'ADMIN_PASSWORD', None):
        print(f" Login failed for {email}")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    print(f" Login successful for {email}")
    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me")
async def get_me(current_user: str = Depends(get_current_user)):
    print(f"👤 GET /api/me called for: {current_user}")
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
    print(f"📥 PUT /api/clients/{client_id} called")
    data = await request.json()
    print(f"📦 Request data keys: {list(data.keys())}")
    
    # Map 'menu' from frontend to 'menu_json' in DB
    if 'menu' in data:
        print(f"🔄 Converting 'menu' to 'menu_json'...")
        try:
            data['menu_json'] = json.dumps(data.pop('menu'))
            print(f" menu_json created successfully")
        except Exception as e:
            print(f" Error serializing menu: {e}")
            raise HTTPException(status_code=400, detail=f"Error serializing menu: {str(e)}")
    
    # Convertir a int si es un ID numérico
    try:
        client_id_int = int(client_id)
    except (ValueError, TypeError):
        client_id_int = client_id  # Usar el string original si no es numérico

    print(f" Calling database.update_client with client_id={client_id_int}")
    if database.update_client(client_id_int, data):
        return {"status": "updated"}
    else:
        print(f" database.update_client returned False")
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
    print(f"📥 DELETE /api/clients/{client_id} called")
    
    # Convertir a int si es un ID numérico
    try:
        client_id_int = int(client_id)
    except (ValueError, TypeError):
        client_id_int = client_id  # Usar el string original si no es numérico
    
    print(f" Using client_id_int={client_id_int} (type: {type(client_id_int).__name__})")
    
    # Prevenir eliminación de demos hardcodeados
    if client_id_int in [9991, 9992, 9993]:
        print(f" Attempted to delete demo client {client_id_int}")
        raise HTTPException(status_code=403, detail="No se pueden eliminar clientes de demostración")
    
    if database.delete_client_db_entry(client_id_int):
        return {"status": "deleted"}
    else:
        print(f" Failed to delete client {client_id_int}")
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


# ============================================
# ENDPOINTS DE EMAIL CONFIGURATION
# ============================================

@app.get("/api/clients/{client_id}/email-config")
async def get_email_config(client_id: int, current_user: str = Depends(get_current_user)):
    """Obtiene la configuración de email de un cliente"""
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
        raise HTTPException(status_code=500, detail=f"Error al enviar email: {str(e)}")


# ============================================
# ENDPOINTS DE LEAD TRACKING
# ============================================

@app.get("/api/clients/{client_id}/leads")
async def get_client_leads(client_id: int, status: str = None, limit: int = 50,
                          current_user: str = Depends(get_current_user)):
    """Obtiene los leads de un cliente"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT * FROM lead_tracking
            WHERE client_id = %s
        """
        params = [client_id]

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY last_interaction DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        leads = cursor.fetchall()
        cursor.close()
        conn.close()

        return {"leads": [dict(lead) for lead in leads], "total": len(leads)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients/{client_id}/leads/cold")
async def get_cold_leads(client_id: int, hours: int = 24,
                         current_user: str = Depends(get_current_user)):
    """Obtiene leads fríos (no han respondido en X horas)"""
    try:
        conn = database.get_connection()
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
        conn.close()

        return {"leads": [dict(lead) for lead in leads], "total": len(leads), "hours": hours}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DE APPOINTMENTS
# ============================================

@app.get("/api/clients/{client_id}/appointments")
async def get_client_appointments(client_id: int, status: str = None,
                                  current_user: str = Depends(get_current_user)):
    """Obtiene las citas de un cliente"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if status == 'tomorrow':
            # Citas de mañana
            from datetime import datetime, timedelta
            tomorrow = datetime.now().date() + timedelta(days=1)
            tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
            tomorrow_end = datetime.combine(tomorrow, datetime.max.time())

            cursor.execute("""
                SELECT a.*, c.name as client_name
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                WHERE a.client_id = %s
                  AND a.appointment_date >= %s
                  AND a.appointment_date < %s
                  AND a.status IN ('pending', 'confirmed')
                ORDER BY a.appointment_date ASC
            """, (client_id, tomorrow_start, tomorrow_end))
        elif status:
            cursor.execute("""
                SELECT a.*, c.name as client_name
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                WHERE a.client_id = %s AND a.status = %s
                ORDER BY a.appointment_date ASC
            """, (client_id, status))
        else:
            cursor.execute("""
                SELECT a.*, c.name as client_name
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                WHERE a.client_id = %s
                  AND a.status = 'pending'
                  AND a.appointment_date >= CURRENT_TIMESTAMP
                ORDER BY a.appointment_date ASC
            """, (client_id,))

        appointments = cursor.fetchall()
        cursor.close()
        conn.close()

        return {"appointments": [dict(apt) for apt in appointments], "total": len(appointments)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clients/{client_id}/appointments")
async def create_appointment(client_id: int, request: Request,
                            current_user: str = Depends(get_current_user)):
    """Crea una nueva cita"""
    data = await request.json()

    # Parsear fecha
    try:
        from datetime import datetime
        appointment_date = datetime.fromisoformat(data.get('appointment_date'))
    except:
        raise HTTPException(status_code=400, detail="Fecha inválida. Usa formato ISO")

    try:
        conn = database.get_connection()
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
        conn.close()

        return {"status": "created", "appointment_id": appointment_id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/clients/{client_id}/appointments/{appointment_id}/confirm")
async def confirm_appointment(client_id: int, appointment_id: int,
                             current_user: str = Depends(get_current_user)):
    """Confirma una cita"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE appointments
            SET status = 'confirmed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (appointment_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "confirmed", "message": "Cita confirmada"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/clients/{client_id}/appointments/{appointment_id}/cancel")
async def cancel_appointment(client_id: int, appointment_id: int,
                            current_user: str = Depends(get_current_user)):
    """Cancela una cita"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE appointments
            SET status = 'cancelled',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (appointment_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "cancelled", "message": "Cita cancelada"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Static Files Mounts (After all specific routes)
if os.path.exists(WWW_DIR):
    print(f" Mounting static files from {WWW_DIR}")
    app.mount("/", StaticFiles(directory=WWW_DIR, html=True), name="root")
else:
    print(f"ℹ Skipping static files mount (Directory not found: {WWW_DIR})")

# Production entry point handled by Firebase or Uvicorn from shell
