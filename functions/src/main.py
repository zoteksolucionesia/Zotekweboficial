import os
# Triggering redeploy for dynamic prompt fix
import random
import threading
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from collections import deque
import sys # Added for sys.stdout.flush()

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import io
import sqlite3
import traceback # Added for traceback.format_exc()

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Local imports
from . import database
from .services import whatsapp_service
from .services.gemini_service import GeminiEngine

# Load configuration
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY", "ZOTEK_SECRET_DEFAULT_CHANGE_ME")
ALGORITHM = "HS256"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "zoteksolucionesia@gmail.com")
ADMIN_EMAILS = [
    ADMIN_EMAIL,
    "morentinomar@gmail.com"
]
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/verify-code")

# In-memory storage for 2FA codes (In production use Redis)
verification_codes = {}  # {email: {"code": str, "expiry": datetime}}

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# En Firebase, el código está en /workspace/functions, por lo que BASE_DIR es /workspace/functions
# Pero el hosting sirve desde el root /workspace/www
# Es mejor no depender de archivos estáticos en FastAPI si usamos Firebase Hosting.

app = FastAPI()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/test-whatsapp")
async def test_whatsapp(to: str = "523123173431"):
    """Diagnostic endpoint: tests WhatsApp API send capability."""
    import sys
    results = {"steps": [], "target": to}
    
    try:
        # Step 1: Get first client
        clients = database.list_clients()
        if not clients:
            return {"error": "No clients in Firestore", "steps": results["steps"]}
        client = clients[0]
        results["steps"].append(f"1. Client found: {client.get('name')}")
        
        # Step 2: Check token
        token = client.get('whatsapp_token', '')
        phone_id = client.get('phone_number_id', '')
        results["steps"].append(f"2. Token present: {bool(token)}")
        results["steps"].append(f"3. phone_number_id: {phone_id}")
        
        # Step 4: Test WhatsApp API - Send Message
        import requests as req
        url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": "Test diagnostic message from Bot server"}
        }
        
        results["steps"].append(f"4. Attempting send to {to}...")
        resp = req.post(url, headers=headers, json=data)
        results["status_code"] = resp.status_code
        results["response_body"] = resp.json() if resp.status_code != 204 else {}
        
        if resp.status_code == 200:
            results["result"] = "SUCCESS"
        else:
            results["result"] = "FAILED"
            
    except Exception as e:
        import traceback
        results["error"] = f"{type(e).__name__}: {e}"
        results["traceback"] = traceback.format_exc()
    
    return results

# El resto de rutas de UI (/login, /admin-control) han sido eliminadas
# ya que Firebase Hosting las maneja mediante rewrites en firebase.json


# Cache for WhatsApp retries
PROCESSED_MESSAGES = deque(maxlen=100)

# Initialize DB at module level (Firebase copies DB to /tmp, locally creates tables)
database.init_db()

# Initialize Gemini at module level (startup events don't fire in our custom ASGI bridge)
gemini = None
print(f"GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}, starts: {GEMINI_API_KEY[:10] if GEMINI_API_KEY else 'NONE'}"); sys.stdout.flush()
try:
    gemini = GeminiEngine(api_key=GEMINI_API_KEY)
    print("GeminiEngine initialized OK"); sys.stdout.flush()
except Exception as e:
    print(f"GeminiEngine INIT FAILED: {e}"); sys.stdout.flush()
    gemini = None


# === WEBHOOK ===

@app.get("/webhook")
async def verify_webhook(request: Request):
    token = request.query_params.get("hub.verify_token")
    if token == VERIFY_TOKEN:
        challenge = request.query_params.get("hub.challenge")
        return int(challenge) if challenge else "Ok"
    return "Error auth", 403




@app.post("/webhook")
async def recibir_mensaje(request: Request):
    try:
        data = await request.json()
        print(f"DEBUG: Webhook data received: {data}"); sys.stdout.flush()
        
        if data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    if 'messages' in value:
                        message = value['messages'][0]
                        message_id = message.get('id')
                        
                        if message_id in PROCESSED_MESSAGES:
                            print(f"DEBUG: Message {message_id} already processed."); sys.stdout.flush()
                            return {"status": "already_processed"}
                        
                        PROCESSED_MESSAGES.append(message_id)
                        if len(PROCESSED_MESSAGES) > 100: PROCESSED_MESSAGES.pop(0)

                        numero_usuario = message['from']
                        phone_number_id = value['metadata']['phone_number_id']
                        
                        print(f"[Webhook] Message from {numero_usuario}, phoneID={phone_number_id}"); sys.stdout.flush()
                        
                        # --- VERIFICAR SESIÓN DEMO PRIMERO ---
                        session = database.get_user_session(numero_usuario)
                        demo_client_id = None
                        if session and session.get("demo_mode"):
                            demo_mode = session.get("demo_mode")
                            if demo_mode == "Restaurante": demo_client_id = "demo_restaurante"
                            elif demo_mode == "Clínica" or demo_mode == "Clinica": demo_client_id = "demo_clinica"
                            elif demo_mode == "Tienda": demo_client_id = "demo_tienda"
                        
                        # Obtener siempre el cliente real primero (propietario del número base)
                        real_client = database.get_client_by_phone_id(phone_number_id)

                        client_data = None
                        if demo_client_id:
                            print(f"[Webhook] Sesión Demo activa, cargando cliente: {demo_client_id}"); sys.stdout.flush()
                            client_data = database.get_client_by_id(demo_client_id)
                            # Heredar token e ID del bot principal para poder responder por WhatsApp
                            if client_data and real_client:
                                client_data['whatsapp_token'] = real_client.get('whatsapp_token')
                                client_data['phone_number_id'] = real_client.get('phone_number_id')
                        
                        # Fallback a phone_number_id si no es demo o no se encontró
                        if not client_data:
                            client_data = real_client
                            
                        if not client_data:
                            print(f"❌ ERROR: No client found for phoneID {phone_number_id}"); sys.stdout.flush()
                            return {"status": "error", "message": "Client not found"}
                        
                        print(f"✅ Client Found: {client_data.get('name')} (ID: {client_data.get('id')})"); sys.stdout.flush()
                        
                        # 1. Detectar tipo de mensaje
                        texto_usuario = ""
                        texto_menu = "" # Default to avoid NameError
                        if message.get('type') == 'text':
                            texto_usuario = message.get('text', {}).get('body', "")
                        elif message.get('type') == 'interactive':
                            interactive = message.get('interactive', {})
                            if interactive.get('type') == 'button_reply':
                                texto_usuario = interactive.get('button_reply', {}).get('title', "")
                            elif interactive.get('type') == 'list_reply':
                                texto_usuario = interactive.get('list_reply', {}).get('title', "")
                        
                        print(f"DEBUG: Texto de usuario detectado: '{texto_usuario}'"); sys.stdout.flush()
                        
                        # --- INTERCEPCIÓN DE DEMOS (SANDBOX) ---
                        texto_lower = texto_usuario.lower().strip()
                        if "quiero probar la demo de" in texto_lower:
                            # Identificar el tipo de demo
                            tipo_demo = None
                            if "restaurante" in texto_lower: tipo_demo = "Restaurante"
                            elif "clínica" in texto_lower or "clinica" in texto_lower: tipo_demo = "Clínica"
                            elif "tienda" in texto_lower: tipo_demo = "Tienda"
                            
                            if tipo_demo:
                                print(f"[Demo] Iniciando sesión de demo para {numero_usuario} modo: {tipo_demo}"); sys.stdout.flush()
                                database.save_user_session(numero_usuario, {"demo_mode": tipo_demo})
                                
                                # Send welcome message with buttons for the demo
                                if tipo_demo == "Restaurante":
                                    texto_welcome = "¡Bienvenido a *La Trattoria*! 👋 Soy tu asistente virtual. ¿Qué te gustaría hacer hoy?"
                                    opciones = ["Ver Menú", "Hacer Reserva", "Horarios"]
                                elif tipo_demo == "Clínica":
                                    texto_welcome = "Bienvenido a la *Clínica San Juan*. 🏥 ¿En qué podemos ayudarte hoy?"
                                    opciones = ["Agendar Cita", "Especialidades", "Ubicación"]
                                else: # Tienda
                                    texto_welcome = "¡Hola! Bienvenido a *Moda Urbana*. 🛍️ ✨ ¿Cómo podemos ayudarte con tu estilo hoy?"
                                    opciones = ["Ver Catálogo", "Tallas", "Devoluciones"]

                                whatsapp_service.enviar_menu_botones(numero_usuario, texto_welcome, opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                return {"status": "demo_started"}

                        # Comprobar si desea salir de la demo
                        if texto_lower in ["salir", "terminar", "terminar demo", "salir demo"]:
                            session = database.get_user_session(numero_usuario)
                            if session and session.get("demo_mode"):
                                database.delete_user_session(numero_usuario)
                                print(f"[Demo] Terminando sesión de demo para {numero_usuario}"); sys.stdout.flush()
                                msg_salida = "Has salido del modo demo. Ahora vuelvo a ser el asistente general de Zotek Soluciones IA. ¿En qué más puedo ayudarte?"
                                whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, msg_salida, client_data['whatsapp_token'], client_data['phone_number_id'])
                                return {"status": "demo_ended"}
                        # --- FIN INTERCEPCIÓN DEMOS ---

                        if not client_data.get('is_active', True):
                            print(f"[Webhook] Bot is INACTIVE for '{client_data['name']}'. Skipping AI."); sys.stdout.flush()
                            return {"status": "bot_inactive"}

                        print(f"[Webhook] Bot is ACTIVE. WhatsApp token present: {bool(client_data.get('whatsapp_token'))}, token starts: {str(client_data.get('whatsapp_token', ''))[:15]}..."); sys.stdout.flush()

                        # Intercepción de Opciones del Menú Personalizado
                        menu_data = None
                        try:
                            # Reutilizamos la lógica del menú aquí para evitar funciones anidadas problemáticas
                            menu_doc = database.get_db().collection('clients').document(str(client_data['id'])).collection('config').document('menu').get()
                            if menu_doc.exists: menu_data = menu_doc.to_dict()
                        except Exception as e:
                            print(f"DEBUG: Error al cargar menú desde Firestore: {e}"); sys.stdout.flush()

                        if menu_data:
                            def buscar_opcion(opciones, texto):
                                for opt in opciones:
                                    is_dict = isinstance(opt, dict)
                                    title = opt.get('title') if is_dict else opt
                                    icon = opt.get('icon', '') if is_dict else ''
                                    full_title = f"{icon} {title}".strip()
                                    
                                    # Comparar con título completo (con icono) y con solo el título
                                    if str(full_title).lower().strip() == texto.lower().strip(): return opt
                                    if str(title).lower().strip() == texto.lower().strip(): return opt

                                    if is_dict and opt.get('submenu') and opt['submenu'].get('options'):
                                        found = buscar_opcion(opt['submenu']['options'], texto)
                                        if found: return found
                                    elif is_dict and 'opciones' in opt: # Soporte para estructura vieja
                                        found = buscar_opcion(opt['opciones'], texto)
                                        if found: return found
                                return None

                            match = buscar_opcion(menu_data.get('options', []), texto_usuario)
                            if not match and 'opciones' in menu_data: # Backup para estructura vieja
                                match = buscar_opcion(menu_data['opciones'], texto_usuario)

                            if match and isinstance(match, dict):
                                if match.get('submenu') and match['submenu'].get('options'):
                                    sub = match['submenu']
                                    titles = []
                                    for o in sub['options']:
                                        t = o.get('title', 'Opción') if isinstance(o, dict) else str(o)
                                        i = o.get('icon', '') if isinstance(o, dict) else ''
                                        titles.append(f"{i} {t}".strip())
                                        
                                    if len(titles) == 0:
                                        msg = sub.get('text', f"Opciones para {match['title']}:")
                                        whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, msg, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    elif len(titles) > 3:
                                        whatsapp_service.enviar_menu_lista(numero_usuario, sub.get('text', 'Opciones:'), "Ver", match['title'], titles, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    else:
                                        whatsapp_service.enviar_menu_botones(numero_usuario, sub.get('text', 'Opciones:'), titles, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, sub.get('text', 'Opciones:'))
                                    return {"status": "submenu_sent"}
                                elif match.get('response'):
                                    res_text = match['response']
                                    cal_url = client_data.get('calendly_url')
                                    if cal_url:
                                        res_text = res_text.replace("{{calendly_url}}", cal_url)
                                        if "agendar cita" in str(match.get('title')).lower():
                                            if cal_url not in res_text: res_text += f"\n\nLink: {cal_url}"
                                    
                                    print(f"DEBUG: Enviando respuesta predefinida para '{match.get('title')}'"); sys.stdout.flush()
                                    database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, res_text)
                                    
                                    # Inline de enviar_respuesta_con_opciones
                                    texto_para_enviar = res_text
                                    opciones_dinamicas = []
                                    if "[OPCIONES]:" in res_text:
                                        partes = res_text.split("[OPCIONES]:")
                                        texto_para_enviar = partes[0].strip()
                                        dict_opciones = partes[1].split("|")
                                        opciones_dinamicas = [o.strip() for o in dict_opciones if o.strip()]

                                    whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, texto_para_enviar, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    if opciones_dinamicas:
                                        if len(opciones_dinamicas) > 3:
                                            whatsapp_service.enviar_menu_lista(numero_usuario, "Selecciona:", "Opciones", "Menú", opciones_dinamicas, client_data['whatsapp_token'], client_data['phone_number_id'])
                                        elif len(opciones_dinamicas) > 0:
                                            whatsapp_service.enviar_menu_botones(numero_usuario, "Selecciona:", opciones_dinamicas, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    return {"status": "predefined_sent"}

                            if not match and menu_data.get('fallback_text'):
                                print(f"DEBUG: No menu match found. Sending fallback_text for {client_data['name']}"); sys.stdout.flush()
                                fallback_msg = menu_data['fallback_text']
                                opciones_raw = menu_data.get('options', menu_data.get('opciones', []))
                                opciones = []
                                for opt in opciones_raw:
                                    t = opt.get('title', 'Opción') if isinstance(opt, dict) else str(opt)
                                    i = opt.get('icon', '') if isinstance(opt, dict) else ''
                                    opciones.append(f"{i} {t}".strip())
                                
                                if len(opciones) > 0:
                                    if len(opciones) > 3:
                                        whatsapp_service.enviar_menu_lista(numero_usuario, fallback_msg, "Ver Opciones", "Menú", opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    else:
                                        whatsapp_service.enviar_menu_botones(numero_usuario, fallback_msg, opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, f"[Fallback enviado: {fallback_msg}]")
                                    return {"status": "fallback_sent"}

                        # Keywords de menú (hola, menu, etc.)
                        if texto_usuario.lower().strip() in ["hola", "menu", "menú", "inicio", "opciones"]:
                            print(f"[Webhook] ✅ Keyword match: '{texto_usuario}' -> checking for explicit menu options"); sys.stdout.flush()
                            
                            opciones_raw = []
                            texto_menu_local = ""
                            if menu_data:
                                opciones_raw = menu_data.get('options', menu_data.get('opciones', []))
                                texto_menu_local = menu_data.get('text', f"¡Hola! Bienvendu@ a {client_data['name']}. 👋\n\n¿En qué puedo ayudarte?")
                            
                            if len(opciones_raw) > 0:
                                print(f"[send_menu_followup_inline] Starting for client {client_data.get('name')}"); sys.stdout.flush()
                                opciones = []
                                for opt in opciones_raw:
                                    t = opt.get('title', 'Opción') if isinstance(opt, dict) else str(opt)
                                    i = opt.get('icon', '') if isinstance(opt, dict) else ''
                                    opciones.append(f"{i} {t}".strip())
                                
                                print(f"[send_menu_followup_inline] Sending menu with {len(opciones)} options to {numero_usuario}"); sys.stdout.flush()
                                try:
                                    if len(opciones) > 3:
                                        send_result = whatsapp_service.enviar_menu_lista(numero_usuario, texto_menu_local, "Ver Opciones", "Menú", opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    else:
                                        send_result = whatsapp_service.enviar_menu_botones(numero_usuario, texto_menu_local, opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    
                                    database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, f"[Menu enviado: {send_result}]")
                                    print(f"[Webhook] ✅ Menu flow complete. send_result={send_result}"); sys.stdout.flush()
                                    return {"status": "menu_sent"}
                                except Exception as e:
                                    print(f"❌ ERROR enviando menú: {e}\n{traceback.format_exc()}"); sys.stdout.flush()
                                    return {"status": "error_sending_menu"}
                            else:
                                print(f"[Webhook] Menu has 0 options. Allowing Gemini to handle the greeting."); sys.stdout.flush()
                                # Do not return here. Let it fall through to Gemini.

                        # Proceso con Gemini
                        if gemini is None: return {"status": "no_gemini"}
                        
                        # --- INYECCIÓN DE CONTEXTO DEMO ---
                        session = database.get_user_session(numero_usuario)
                        if session and session.get('demo_mode'):
                            demo_mode = session['demo_mode']
                            if demo_mode == "Restaurante":
                                if not client_data.get('name'): client_data['name'] = "La Trattoria"
                                if not client_data.get('system_instruction'): client_data['system_instruction'] = "Eres el asistente inteligente del restaurante 'La Trattoria'. Tu objetivo es ayudar a los clientes a hacer reservas, ver el menú (ofreces pizzas, pastas y ensaladas) y responder dudas sobre los horarios (abierto 12pm a 11pm). Sé amigable, breve y apetitoso."
                            elif demo_mode == "Clínica":
                                if not client_data.get('name'): client_data['name'] = "Clínica San Juan"
                                if not client_data.get('system_instruction'): client_data['system_instruction'] = "Eres el asistente de la 'Clínica San Juan'. Ayudas a pacientes a agendar citas médicas (Medicina general, Odontología, Pediatría) y das información de ubicación. Sé empático, breve, profesional y tranquilizador."
                            elif demo_mode == "Tienda":
                                if not client_data.get('name'): client_data['name'] = "Moda Urbana Tienda"
                                if not client_data.get('system_instruction'): client_data['system_instruction'] = "Eres el asistente de la tienda de ropa 'Moda Urbana'. Ayudas a encontrar prendas (camisetas, jeans, tenis), verificar disponibilidad de tallas y hacer devoluciones. Usa emojis, sé casual, vendedor, dinámico y muy breve."
                            print(f"[Demo] Inyectando contexto de {demo_mode} para Gemini."); sys.stdout.flush()
                        
                        prompt = texto_usuario
                        if message.get('type') == 'interactive':
                            prompt = f"[Menú]: {texto_usuario}"
                        
                        if menu_data:
                            client_data['menu_data'] = menu_data
                        
                        print(f"[Webhook] Calling Gemini for: '{prompt[:50]}...'")
                        res_ai = gemini.generar_respuesta(prompt, client_data, numero_usuario)
                        print(f"[Webhook] Gemini response preview: {res_ai[:80]}")
                        
                        # Parse dynamic [OPCIONES]: generated by Gemini
                        texto_para_enviar = res_ai
                        opciones_dinamicas = []
                        if "[OPCIONES]:" in res_ai:
                            partes = res_ai.split("[OPCIONES]:")
                            texto_para_enviar = partes[0].strip()
                            dict_opciones = partes[1].split("|")
                            opciones_dinamicas = [o.strip() for o in dict_opciones if o.strip()][:10] # WhatsApp list limit 10
                        
                        success = whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, texto_para_enviar, client_data['whatsapp_token'], client_data['phone_number_id'])
                        
                        if success and opciones_dinamicas:
                            if len(opciones_dinamicas) > 3:
                                whatsapp_service.enviar_menu_lista(numero_usuario, "Por favor, selecciona una opción:", "Ver opciones", "Menú", opciones_dinamicas, client_data['whatsapp_token'], client_data['phone_number_id'])
                            elif len(opciones_dinamicas) > 0:
                                whatsapp_service.enviar_menu_botones(numero_usuario, "Selecciona una opción:", opciones_dinamicas, client_data['whatsapp_token'], client_data['phone_number_id'])

                        print(f"[Webhook] WhatsApp send result: {success}")
                        if success:
                            database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, res_ai)

    except Exception as e:
        import traceback
        print(f"❌ WEBHOOK CRITICAL ERROR: {e}\n{traceback.format_exc()}")

    return {"status": "ok"}


# === Security Helpers ===

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


def send_security_code(email: str, code: str):
    if not EMAIL_PASSWORD:
        print("ERROR: EMAIL_APP_PASSWORD no configurada en .env")
        return False

    print(f"Intentando enviar email a {email}...")

    try:
        msg = MIMEText(f"Tu codigo de acceso para el panel administrativo es: {code}\nExpira en 10 minutos.")
        msg['Subject'] = f"{code} es tu código de verificación"
        msg['From'] = ADMIN_EMAIL
        msg['To'] = email

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(ADMIN_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        import traceback
        print(f"Error enviando email: {e}")
        traceback.print_exc()
        return False


# === Routes ===

@app.get("/debug-paths")
async def debug_paths():
    return {
        "BASE_DIR": BASE_DIR,
        "status": "Firebase Hosting handles static files",
    }


# === Auth API ===

@app.post("/api/auth/request-code")
async def request_code(request: Request):
    data = await request.json()
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")
    
    # SaaS Phase 3: Permitir admin O email de cliente registrado
    normalized_email = email.lower().strip()
    is_admin = normalized_email in [e.lower().strip() for e in ADMIN_EMAILS]
    
    client = None
    if not is_admin:
        client = database.get_client_by_email(normalized_email)
        if not client:
            return JSONResponse(status_code=403, content={"detail": f"Acceso restringido: Email {email} no registrado"})

    code = f"{random.randint(100000, 999999)}"
    verification_codes[email] = {
        "code": code,
        "expiry": datetime.utcnow() + timedelta(minutes=10)
    }

    if send_security_code(email, code):
        return {"status": "code_sent"}
    else:
        raise HTTPException(status_code=500, detail="Error enviando el codigo")


@app.post("/api/auth/verify-code")
async def verify_code(request: Request):
    data = await request.json()
    email = data.get("email")
    code = data.get("code")

    stored = verification_codes.get(email)
    if not stored or stored["code"] != code or datetime.utcnow() > stored["expiry"]:
        raise HTTPException(status_code=401, detail="Codigo invalido o expirado")

    del verification_codes[email]

    # SaaS Phase 3: Determinar rol y client_id
    normalized_email = email.lower().strip()
    is_admin = normalized_email in [e.lower().strip() for e in ADMIN_EMAILS]
    role = "admin" if is_admin else "client"
    client_id = None
    if role == "client":
        client = database.get_client_by_email(normalized_email)
        client_id = str(client['id']) if client else None

    access_token = create_access_token(data={"sub": email, "role": role, "client_id": client_id})
    return {"access_token": access_token, "token_type": "bearer", "role": role}

@app.get("/api/me")
async def get_me(token: str = Depends(oauth2_scheme)):
    """Retorna el perfil del usuario actual basado en el JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub", "").lower().strip()
        
        # Calcular el rol dinámicamente para que los cambios en ADMIN_EMAILS 
        # surtan efecto incluso si el token tiene un rol viejo.
        is_admin = email in [e.lower().strip() for e in ADMIN_EMAILS]
        role = "admin" if is_admin else "client"
        
        client_id = payload.get("client_id")
        if role == "client" and not client_id:
            # Re-vincular si es necesario
            client = database.get_client_by_email(email)
            client_id = str(client['id']) if client else None
        
        return {
            "email": email,
            "role": role,
            "client_id": client_id
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# === Dynamic Redirections ===

@app.get("/api/redirect/whatsapp")
async def whatsapp_redirect(text: str = "Hola, quisiera mas informacion"):
    """Redirige dinamicamente al WhatsApp del cliente principal configurado."""
    clients = database.list_clients()
    
    def sanitize_mx_number(raw_number):
        """Normaliza números mexicanos: quita el viejo prefijo '1' después del '52'."""
        digits = "".join(filter(str.isdigit, str(raw_number)))
        # Si es un número mexicano con 13 dígitos (52 + 1 + 10), quitar el '1'
        if digits.startswith("521") and len(digits) == 13:
            digits = "52" + digits[3:]
        return digits

    # Intentar encontrar un cliente que tenga número configurado
    target_number = None
    for client in clients:
        num = client.get('whatsapp_number')
        if num:
            target_number = sanitize_mx_number(num)
            break
            
    import urllib.parse
    encoded_text = urllib.parse.quote(text)

    if target_number:
        print(f"[Redirect] Redirecting to client number: {target_number}")
        return RedirectResponse(url=f"https://wa.me/{target_number}?text={encoded_text}")

    # Fallback de seguridad (Bot Zotek: 3123775877)
    fallback_url = f"https://wa.me/523123775877?text={encoded_text}"
    print(f"[Redirect] No numbers found in DB, using fallback: 523123775877")
    return RedirectResponse(url=fallback_url)


# === Protected Admin API ===

@app.get("/api/clients")
async def list_clients(current_user: str = Depends(get_current_user)):
    return database.list_clients()


@app.post("/api/clients")
async def create_client(request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()
    if database.add_client(data):
        return {"status": "created"}
    raise HTTPException(status_code=400, detail="Error creating client")


@app.put("/api/clients/{client_id}")
async def update_client(client_id: str, request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()
    
    # Separar el menú si viene incluido para guardarlo en su propia ruta
    menu_data = data.pop('menu', None)
    
    if database.update_client(client_id, data):
        if menu_data:
            # Guardar el menú en la subcolección config/menu
            database.get_db().collection('clients').document(client_id).collection('config').document('menu').set(menu_data)
        return {"status": "updated"}
    raise HTTPException(status_code=400, detail="Error updating client")


@app.get("/api/clients/{client_id}")
async def get_client(client_id: str, current_user: str = Depends(get_current_user)):
    client = database.get_client_by_id(client_id)
    if client:
        return client
    raise HTTPException(status_code=404, detail="Client not found")


@app.get("/api/clients/{client_id}/documents")
async def list_documents(client_id: str, current_user: str = Depends(get_current_user)):
    return database.list_client_documents(client_id)


@app.delete("/api/clients/{client_id}/documents/{doc_id}")
async def delete_document(client_id: str, doc_id: str, current_user: str = Depends(get_current_user)):
    """Elimina un documento (entrada de conocimiento) de un cliente."""
    if database.delete_knowledge_entry(client_id, doc_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Documento no encontrado o no se pudo eliminar")


@app.get("/api/clients/{client_id}/menu")
async def get_client_menu(client_id: str, current_user: str = Depends(get_current_user)):
    """Obtiene la configuración del menú de un cliente."""
    doc = database.get_db().collection('clients').document(client_id).collection('config').document('menu').get()
    if doc.exists:
        return doc.to_dict()
    return {"text": "", "options": ["Servicios", "Agendar Cita", "Contacto"]}

@app.post("/api/clients/{client_id}/menu")
async def update_client_menu(client_id: str, request: Request, current_user: str = Depends(get_current_user)):
    """Actualiza la configuración del menú de un cliente."""
    data = await request.json()
    database.get_db().collection('clients').document(client_id).collection('config').document('menu').set(data)
    return {"status": "updated"}

@app.post("/api/clients/{client_id}/reset")
async def reset_demo_client(client_id: str, current_user: str = Depends(get_current_user)):
    """Restablece la configuración de un cliente de demostración a su estado original."""
    
    # Verificar que sea un cliente demo (ID debe comenzar con 'demo_')
    if not str(client_id).startswith('demo_'):
        raise HTTPException(status_code=400, detail="Solo se pueden restablecer los clientes de ejemplo (ID debe comenzar con 'demo_').")
    
    # Plantillas de configuración original por tipo de demo
    demo_templates = {
        "restaurante": {
            "name": "Restaurante La Trattoria",
            "email": "restaurante@ejemplo.com",
            "is_active": True,
            "menu": {
                "text": "¡Bienvenido a *La Trattoria*! 👋 Soy tu asistente virtual. ¿Qué te gustaría hacer hoy?",
                "options": [
                    {"title": "Ver Menú", "icon": "🍕", "response": "Nuestro menú incluye pizzas a la leña, pastas frescas y postres italianos."},
                    {"title": "Hacer Reserva", "icon": "📅", "response": "Indícanos la fecha y hora para verificar disponibilidad."},
                    {"title": "Horarios", "icon": "⏰", "response": "Estamos abiertos todos los días de 12:00 PM a 11:00 PM."}
                ],
                "fallback_text": "Lo siento, no entendí eso. Aquí tienes las opciones principales de La Trattoria:"
            }
        },
        "clinica": {
            "name": "Clínica San Juan",
            "email": "clinica@ejemplo.com",
            "is_active": True,
            "menu": {
                "text": "Bienvenido a la *Clínica San Juan*. 🏥 ¿En qué podemos ayudarte hoy?",
                "options": [
                    {"title": "Agendar Cita", "icon": "📅", "response": "Por favor, dinos para qué especialidad buscas cita."},
                    {"title": "Especialidades", "icon": "👨‍⚕️", "response": "Contamos con Medicina General, Odontología y Pediatría."},
                    {"title": "Ubicación", "icon": "📍", "response": "Estamos en Av. Central #123. Haz clic aquí para ver en el mapa: https://maps.google.com"}
                ],
                "fallback_text": "No comprendo tu solicitud. Selecciona una de estas opciones de la clínica:"
            }
        },
        "tienda": {
            "name": "Moda Urbana",
            "email": "tienda@ejemplo.com",
            "is_active": True,
            "menu": {
                "text": "¡Hola! Bienvenido a *Moda Urbana*. 🛍️ ✨ ¿Cómo podemos ayudarte con tu estilo hoy?",
                "options": [
                    {"title": "Ver Catálogo", "icon": "👕", "response": "Nuestra nueva colección de otoño ya está disponible."},
                    {"title": "Tallas", "icon": "📏", "response": "Manejamos tallas desde XS hasta XL en la mayoría de nuestras prendas."},
                    {"title": "Devoluciones", "icon": "🔄", "response": "Tienes 30 días para realizar cambios o devoluciones con tu ticket."}
                ],
                "fallback_text": "Ups, no reconozco eso. Aquí tienes lo que puedo hacer por ti en Moda Urbana:"
            }
        }
    }
    db = database.get_db()
    
    # 1. Obtener el cliente actual para saber su phone_number_id y determinar el tipo de demo
    client_ref = db.collection('clients').document(client_id)
    client_doc = client_ref.get()
    if not client_doc.exists:
        raise HTTPException(status_code=404, detail=f"Cliente '{client_id}' no encontrado en la base de datos.")
    
    current_data = client_doc.to_dict()
    phone_id = str(current_data.get('phone_number_id', '')).lower()
    
    # Determinar el tipo de demo por phone_number_id o por el ID del cliente
    template_key = None
    if 'restaurante' in phone_id or 'restaurante' in client_id.lower() or phone_id == 'demo_123':
        template_key = 'restaurante'
    elif 'clinica' in phone_id or 'clinica' in client_id.lower() or phone_id == 'demo_456':
        template_key = 'clinica'
    elif 'tienda' in phone_id or 'tienda' in client_id.lower() or phone_id == 'demo_789':
        template_key = 'tienda'
    
    # Si no se pudo determinar, intentar por el nombre del cliente
    if not template_key:
        client_name = str(current_data.get('name', '')).lower()
        if 'restaurante' in client_name or 'trattoria' in client_name:
            template_key = 'restaurante'
        elif 'clínica' in client_name or 'clinica' in client_name or 'san juan' in client_name:
            template_key = 'clinica'
        elif 'tienda' in client_name or 'moda' in client_name or 'urbana' in client_name or 'ecommerce' in client_name or 'e-commerce' in client_name:
            template_key = 'tienda'
    
    if not template_key:
        raise HTTPException(status_code=400, detail=f"No se pudo determinar el tipo de demo para '{client_id}'. Verifica que el phone_number_id o nombre del cliente indique el tipo (restaurante, clinica, tienda).")
    
    template = demo_templates[template_key]
    
    # 2. Actualizar información básica (preservar phone_number_id y campos técnicos)
    client_info = template.copy()
    menu_data = client_info.pop("menu")
    client_info["id"] = client_id
    # Preservar el phone_number_id original para no romper la integración de WhatsApp
    client_info["phone_number_id"] = current_data.get('phone_number_id', phone_id)
    
    client_ref.set(client_info, merge=True)
    
    # 3. Sobrescribir el menú completo con la configuración original
    client_ref.collection('config').document('menu').set(menu_data)
    
    # 4. Limpiar chats para un estado limpio
    chats = client_ref.collection('chats').stream()
    batch = db.batch()
    for doc in chats:
        batch.delete(doc.reference)
    batch.commit()

    return {"status": "success", "message": f"Cliente {client_id} restablecido correctamente como demo de '{template_key}'"}


@app.get("/api/clients/{client_id}/chats")
async def list_chats(client_id: str, limit: int = 50, current_user: str = Depends(get_current_user)):
    """Obtiene el historial de chats de un cliente."""
    return database.get_client_chats(client_id, limit=limit)

@app.post("/api/migrate")
async def migrate_sqlite_to_firestore(current_user: str = Depends(get_current_user)):
    """Migra los datos de SQLite local (en el servidor) a Firestore."""
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "consultorio.db")
    if not os.path.exists(db_path):
        return {"status": "error", "message": f"SQLite DB not found at {db_path}"}
    
    try:
        print(f"[Migration] SQLite DB found at {db_path}. Opening connection...")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Migrar Clientes
        print("[Migration] Extracting clients from SQLite...")
        cursor.execute("SELECT * FROM clients")
        clients = cursor.fetchall()
        print(f"[Migration] Found {len(clients)} clients to migrate.")
        migrated_clients = 0
        for client in clients:
            client_dict = dict(client)
            old_id = client_dict.pop('id')
            
            print(f"[Migration] Migrating client {old_id} ({client_dict.get('name')})...")
            # Subir a Firestore usando el ID anterior como nombre de doc para mantener refs
            doc_ref = database.get_db().collection('clients').document(str(old_id))
            doc_ref.set(client_dict)
            
            # Migrar Conocimiento
            print(f"[Migration]   Extracting knowledge for client {old_id}...")
            cursor.execute("SELECT * FROM knowledge_base WHERE client_id = ?", (old_id,))
            knowledge = cursor.fetchall()
            print(f"[Migration]   Found {len(knowledge)} entries.")
            for k in knowledge:
                k_dict = dict(k)
                k_id = k_dict.pop('id')
                k_dict.pop('client_id', None) # Avoid error if column name is actually client_id
                doc_ref.collection('knowledge').document(str(k_id)).set(k_dict)
            
            migrated_clients += 1
            print(f"[Migration]   Client {old_id} migrated successfully.")
        
        conn.close()
        print(f"[Migration] Success! Total migrated: {migrated_clients}")
        return {"status": "success", "migrated_clients": migrated_clients}
    except Exception as e:
        import traceback
        error_msg = f"Error en migración: {str(e)}\n{traceback.format_exc()}"
        print(f"[Migration] FATAL ERROR: {error_msg}")
        return {"status": "error", "message": str(e)}


@app.get("/api/settings")
async def get_settings(request: Request, current_user: str = Depends(get_current_user)):
    """Returns public system configuration for the Settings panel."""
    is_production = bool(os.environ.get('K_SERVICE') or os.environ.get('FIREBASE_CONFIG'))
    base_url = str(request.base_url).rstrip('/')

    return {
        "environment": "production" if is_production else "development",
        "webhook_url": f"{base_url}/webhook",
        "gemini_api_key_set": bool(GEMINI_API_KEY),
        "admin_email": ADMIN_EMAIL,
        "twofa_enabled": True,
        "api_version": "1.0.0",
        "total_clients": len(database.list_clients()),
    }


# Static file mounting is handled by Firebase Hosting rewrites, 
# so we don't need to mount it here if we are only an API.
@app.post("/api/clients/{client_id}/upload-pdf")
async def upload_pdf(client_id: str, request: Request, current_user: str = Depends(get_current_user)):
    """Endpoint para subir un PDF, extraer su texto y guardarlo en la base de conocimientos."""
    global PdfReader
    if not PdfReader:
        # Intentar re-importar por si se instaló después del inicio
        try:
            from pypdf import PdfReader as PR
            PdfReader = PR
        except ImportError:
            raise HTTPException(status_code=500, detail="Biblioteca pypdf no instalada en el servidor.")
    
    try:
        form = await request.form()
        file = form.get("file")
        
        if not file or not hasattr(file, 'filename'):
            raise HTTPException(status_code=400, detail="No se recibió ningún archivo.")

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")

        # Read the file into memory
        contents = await file.read()
        f = io.BytesIO(contents)
        
        reader = PdfReader(f)
        text_content = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_content += extracted + "\n"
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF (podría ser una imagen).")

        # Save to database
        database.add_knowledge_entry(client_id, text_content, source_file=file.filename)
        
        return {
            "status": "success",
            "message": f"Contenido de '{file.filename}' procesado y guardado correctamente.",
            "extracted_length": len(text_content)
        }
    except Exception as e:
        import traceback
        print(f"Error procesando PDF: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
