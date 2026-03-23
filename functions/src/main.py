import os
# Triggering redeploy for dynamic prompt fix
import random
import threading
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from collections import deque
import sys # Added for sys.stdout.flush()
import json # Added for json.loads()

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
import re

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

# --- PROCESAMIENTO DE AGENTES ---
def ejecutar_herramientas_agente(tool_calls, numero_usuario, client_data, phone_number_id, whatsapp_token):
    """
    Ejecuta las acciones autónomas solicitadas por el Agente Gemini.
    """
    for tool in tool_calls:
        name = tool.get('name')
        args_raw = tool.get('args')
        try:
            args = dict(args_raw) if args_raw is not None else {}
        except Exception:
            args = {}

        print(f"🤖 AGENTE EJECUTANDO HERRAMIENTA: {name} con {args}"); sys.stdout.flush()
        
        if name == "activar_demo":
            tipo = args.get('tipo', 'restaurante')
            # ID de cliente de la demo en la DB
            demo_id_db = {
                "restaurante": "demo_restaurant",
                "clinica": "demo_dental",
                "tienda": "demo_retail",
                "dental": "demo_dental",
                "psicologo": "demo_psychology",
                "salon": "demo_salon"
            }.get(tipo, "demo_restaurant")
            
            # Guardar en sandbox_sessions
            session_data = {"demo_mode": demo_id_db, "last_interaction": str(datetime.now())}
            database.save_user_session(numero_usuario, phone_number_id, session_data)
            
            # Avisar al usuario que cargamos la demo
            whatsapp_service.enviar_mensaje_whatsapp(
                numero_usuario, 
                f"🔧 Activando modo demostración: {tipo.capitalize()}...", 
                whatsapp_token, 
                phone_number_id
            )
            
            # Obtener datos de la demo para enviar su menú inicial
            demo_client = database.get_client_by_id(demo_id_db)
            if demo_client and demo_client.get('menu_json'):
                try:
                    menu = json.loads(demo_client['menu_json'])
                    whatsapp_service.enviar_menu_lista(
                        numero_usuario,
                        menu.get('text', 'Bienvenido a la demo.'),
                        "Ver Opciones",
                        "Menú de Demo",
                        [opt.get('title') for opt in menu.get('options', [])],
                        whatsapp_token,
                        phone_number_id
                    )
                except:
                    pass

        elif name == "enviar_menu_interactivo":
            mensaje = args.get('mensaje', 'Elige una opción:')
            opciones = args.get('opciones', [])
            if not opciones: continue
            
            if len(opciones) <= 3:
                whatsapp_service.enviar_menu_botones(numero_usuario, mensaje, opciones, whatsapp_token, phone_number_id)
            else:
                whatsapp_service.enviar_menu_lista(numero_usuario, mensaje, "Ver Opciones", "Opciones", opciones, whatsapp_token, phone_number_id)

        elif name == "capturar_lead":
            interes = args.get('interes', 'Interés general en Zotek')
            nombre = args.get('nombre', 'Desconocido')
            print(f"💰 NUEVO LEAD DETECTADO: {nombre} ({numero_usuario}) - Interés: {interes}")
            # Guardar lead en historial o enviar email a admin
            try:
                msg_lead = f"NUEVO LEAD DE ZOTEK\n\nNombre: {nombre}\nTel: {numero_usuario}\nInterés: {interes}"
                # Aquí podrías llamar a una función de envío de email
            except:
                pass

        elif name == "ejecutar_automatizacion_n8n":
            datos_brutos = args.get('datos', {})
            datos = {}
            try:
                datos.update(dict(datos_brutos))
            except:
                pass
            
            workflow_id = args.get('workflow_id', 'general')
            webhook_url = os.getenv("N8N_WEBHOOK_URL")
            
            if not webhook_url:
                print("❌ ERROR: N8N_WEBHOOK_URL no configurada en .env")
                continue
                
            print(f"🔗 DISPARANDO n8n WEBHOOK: {webhook_url}")
            try:
                # Incluir metadatos del usuario
                datos['phone_number'] = numero_usuario
                datos['client_id'] = client_data.get('id')
                datos['timestamp'] = str(datetime.now())
                
                # Llamada asíncrona (fire and forget o esperar)
                import requests
                response = requests.post(webhook_url, json=datos, timeout=10)
                print(f"✅ RESPUESTA n8n ({response.status_code}): {response.text[:50]}")
            except Exception as e:
                print(f"🔥 ERROR AL LLAMAR n8n: {e}")

        elif name == "finalizar_demo":
            database.delete_user_session(numero_usuario, phone_number_id)
            whatsapp_service.enviar_mensaje_whatsapp(
                numero_usuario,
                "✅ Has salido del modo demo. Ahora vuelves a hablar con el asistente principal de Zotek.",
                whatsapp_token,
                phone_number_id
            )



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
            return {"error": "No clients in PostgreSQL database", "steps": results["steps"]}
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

# === SECURITY HELPERS ===

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(hours=8))
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

# === AUTH API ===

@app.post("/api/auth/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    # Simple hardcoded check for admin
    if email == ADMIN_EMAIL and password == os.getenv("ADMIN_PASSWORD", "Zotek!SecureAdmin9X$2026"):
        access_token = create_access_token(data={"sub": email})
        return {"access_token": access_token, "token_type": "bearer"}
    
    # Check other admins
    if email in ADMIN_EMAILS and password == os.getenv("ADMIN_PASSWORD"):
        access_token = create_access_token(data={"sub": email})
        return {"access_token": access_token, "token_type": "bearer"}
        
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")

@app.get("/api/me")
async def get_me(current_user: str = Depends(get_current_user)):
    return {
        "email": current_user,
        "role": "admin" if current_user == ADMIN_EMAIL else "client"
    }

# === CLIENTS API ===

@app.get("/api/recent_logs")
async def get_recent_logs():
    return {"logs": list(RECENT_LOGS)}

@app.get("/api/clients")
async def list_clients(current_user: str = Depends(get_current_user)):
    return database.list_clients()

@app.get("/api/clients/{client_id}")
async def get_client(client_id: str, current_user: str = Depends(get_current_user)):
    client = database.get_client_by_id(client_id)
    if client: return client
    raise HTTPException(status_code=404, detail="Client not found")

@app.post("/api/clients")
async def create_client(request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()
    import json
    if 'menu' in data:
        data['menu_json'] = json.dumps(data.pop('menu'))
    if database.add_client(data):
        return {"status": "created"}
    raise HTTPException(status_code=400, detail="Error creating client")

@app.put("/api/clients/{client_id}")
async def update_client(client_id: str, request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()
    import json
    if 'menu' in data:
        data['menu_json'] = json.dumps(data.pop('menu'))
    if database.update_client(client_id, data):
        return {"status": "updated"}
    raise HTTPException(status_code=400, detail="Error updating client")

@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: str, current_user: str = Depends(get_current_user)):
    # Prevent deletion of demos
    if str(client_id) in ["demo_dental", "demo_psychology", "demo_restaurant", "demo_salon", "demo_retail"]:
        raise HTTPException(status_code=403, detail="No se pueden eliminar demos")
    if database.delete_client_db_entry(client_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=400, detail="Error deleting client")

@app.post("/api/clients/{client_id}/duplicate")
async def duplicate_client(client_id: str, current_user: str = Depends(get_current_user)):
    new_client = database.duplicate_client(client_id)
    if new_client:
        return {"status": "duplicated", "new_client_id": new_client["id"]}
    raise HTTPException(status_code=400, detail="Error duplicating client")

@app.get("/api/clients/{client_id}/documents")
async def list_documents(client_id: str, current_user: str = Depends(get_current_user)):
    return database.list_client_documents(client_id)



# === GLOBAL STATE & INIT ===

# Cache for WhatsApp retries
PROCESSED_MESSAGES = deque(maxlen=100)

# Memory log for debugging
RECENT_LOGS = deque(maxlen=50)

# Initialize DB at module level
database.init_db()

# Initialize Gemini at module level
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
        
        # Guardar en logs recientes
        timestamp_str = datetime.now().isoformat()
        RECENT_LOGS.append({"time": timestamp_str, "payload": data})
        
        if data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    if 'messages' in value:
                        message = value['messages'][0]
                        message_id = message.get('id')
                        
                        # Inicializar variables locales críticas
                        menu_data = None
                        match = None
                        texto_usuario = ""
                        
                        if message_id in PROCESSED_MESSAGES:
                            print(f"DEBUG: Message {message_id} already processed."); sys.stdout.flush()
                            return {"status": "already_processed"}
                        
                        PROCESSED_MESSAGES.append(message_id)
                        if len(PROCESSED_MESSAGES) > 100: PROCESSED_MESSAGES.pop(0)

                        numero_usuario = message['from']
                        phone_number_id = value['metadata']['phone_number_id']

                        print(f"[Webhook] Message from {numero_usuario}, phoneID={phone_number_id}"); sys.stdout.flush()
                        print(f"[DEBUG] texto_usuario inicial: '{texto_usuario}'"); sys.stdout.flush()

                        # --- VERIFICAR SESIÓN DEMO PRIMERO ---
                        session = database.get_user_session(numero_usuario, phone_number_id)
                        demo_client_id = None
                        if session and session.get('demo_mode'):
                            demo_mode = session['demo_mode']
                            # IDs deben coincidir con los de database.py
                            if demo_mode == "Restaurante": demo_client_id = "demo_restaurant"
                            elif demo_mode == "Dental": demo_client_id = "demo_dental"
                            elif demo_mode == "Psicólogo" or demo_mode == "Psicología": demo_client_id = "demo_psychology"
                            elif demo_mode == "Salon" or demo_mode == "Salón": demo_client_id = "demo_salon"
                            elif demo_mode == "Retail" or demo_mode == "Tienda": demo_client_id = "demo_retail"
                        
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

                        # ============================================
                        # DETECCIÓN DE INICIO DE DEMO (NUEVO - MOVIDO ARRIBA)
                        # ============================================
                        # 1. Detectar tipo de mensaje
                        message_type = message.get('type')
                        print(f"[DEBUG] message_type RAW: {message_type}"); sys.stdout.flush()
                        print(f"[DEBUG] message RAW: {message}"); sys.stdout.flush()

                        if message_type == 'text':
                            texto_usuario = message.get('text', {}).get('body', "")
                        elif message_type == 'interactive':
                            interactive = message.get('interactive', {})
                            print(f"[DEBUG] interactive type: {interactive.get('type')}"); sys.stdout.flush()
                            print(f"[DEBUG] interactive content: {interactive}"); sys.stdout.flush()

                            if interactive.get('type') == 'button_reply':
                                texto_usuario = interactive.get('button_reply', {}).get('title', "")
                            elif interactive.get('type') == 'list_reply':
                                texto_usuario = interactive.get('list_reply', {}).get('title', "")
                            else:
                                print(f"[DEBUG] interactive type desconocido: {interactive.get('type')}"); sys.stdout.flush()
                                texto_usuario = ""
                        else:
                            print(f"Unhandled message type '{message_type}': {message}"); sys.stdout.flush()
                            texto_usuario = ""

                        print(f"[DEBUG] texto_usuario DESPUES de extraer: '{texto_usuario}'"); sys.stdout.flush()
                        print(f"[DEBUG] message_type: {message_type}"); sys.stdout.flush()

                        # Verificar si el usuario quiere iniciar UNA NUEVA demo (no viene de sesión)
                        if not demo_client_id:
                            texto_lower = texto_usuario.lower().strip()

                            demo_keyword_map = {
                                "restaurante": "demo_restaurant",
                                "tienda": "demo_retail",
                                "dental": "demo_dental",
                                "psicologo": "demo_psychology",
                                "psicólogo": "demo_psychology",
                                "salon": "demo_salon",
                                "belleza": "demo_salon"
                            }

                            demo_phone_id = None
                            for keyword, phone_id in demo_keyword_map.items():
                                if keyword in texto_lower:
                                    demo_phone_id = phone_id
                                    break

                            if demo_phone_id:
                                # Usuario quiere iniciar una demo nueva
                                demo_client = database.get_client_by_phone_id(demo_phone_id)

                                if demo_client:
                                    tipo_demo = demo_phone_id.replace("demo_", "")
                                    print(f"[Demo] Iniciando sesión de demo para {numero_usuario} modo: {tipo_demo}"); sys.stdout.flush()
                                    database.save_user_session(numero_usuario, phone_number_id, {"demo_mode": tipo_demo, "demo_phone_id": demo_phone_id})

                                    # Cargar menú del demo
                                    menu_data_demo = None
                                    print(f"[DEBUG] demo_client menu_json exists: {bool(demo_client.get('menu_json'))}"); sys.stdout.flush()
                                    print(f"[DEBUG] demo_client keys: {demo_client.keys() if demo_client else 'NONE'}"); sys.stdout.flush()
                                    try:
                                        if demo_client.get('menu_json'):
                                            menu_json_str = demo_client.get('menu_json')
                                            print(f"[DEBUG] menu_json_str type: {type(menu_json_str)}"); sys.stdout.flush()
                                            if isinstance(menu_json_str, str):
                                                menu_data_demo = json.loads(menu_json_str)
                                                print(f"[DEBUG] menu_data loaded from string"); sys.stdout.flush()
                                            elif isinstance(menu_json_str, dict):
                                                menu_data_demo = menu_json_str
                                                print(f"[DEBUG] menu_data loaded from dict"); sys.stdout.flush()
                                    except Exception as e:
                                        print(f"DEBUG: Error al cargar menú del demo: {e}"); sys.stdout.flush()

                                    print(f"[DEBUG] menu_data_demo final: {bool(menu_data_demo)}"); sys.stdout.flush()

                                    if menu_data_demo:
                                        texto_welcome = menu_data_demo.get('text', f"Hola! Bienvenido a {demo_client.get('name', 'la demo')}.")
                                        opciones = [opt.get('title') for opt in menu_data_demo.get('options', [])]

                                        print(f"[Demo] Menu cargado: {len(opciones)} opciones")
                                        print(f"[DEBUG] real_client exists: {bool(real_client)}")
                                        print(f"[DEBUG] phone_number_id value: {phone_number_id}")

                                        # FORZAR token de Zotek directamente
                                        FORCE_TOKEN = real_client.get('whatsapp_token') if real_client else None

                                        print(f"[DEBUG] FORCE_TOKEN: {str(FORCE_TOKEN)[:20] if FORCE_TOKEN else 'NONE'}... (len={len(FORCE_TOKEN) if FORCE_TOKEN else 0})")
                                        print(f"[DEBUG] phone_number_id: {phone_number_id}")

                                        if FORCE_TOKEN and len(str(FORCE_TOKEN)) > 50:
                                            print(f"[Demo] PREPARANDO ENVIO de WhatsApp..."); sys.stdout.flush()
                                            print(f"[Demo]   numero_usuario: {numero_usuario}")
                                            print(f"[Demo]   telefono_token: {str(FORCE_TOKEN)[:20]}...")
                                            print(f"[Demo]   phone_number_id: {phone_number_id}")
                                            print(f"[Demo]   opciones: {opciones}")
                                            try:
                                                print(f"[Demo] LLAMANDO a enviar_menu_botones..."); sys.stdout.flush()
                                                result = whatsapp_service.enviar_menu_botones(numero_usuario, texto_welcome, opciones, FORCE_TOKEN, phone_number_id)
                                                print(f"[Demo] RESULTADO: {result}"); sys.stdout.flush()
                                            except Exception as e:
                                                print(f"[Demo] EXCEPCION: {e}"); sys.stdout.flush()
                                                import traceback
                                                traceback.print_exc()
                                            print(f"[Demo] ENVIO completado"); sys.stdout.flush()
                                        else:
                                            print(f"[Demo] ERROR: Token no válido (len={len(FORCE_TOKEN) if FORCE_TOKEN else 0})"); sys.stdout.flush()
                                    else:
                                        print(f"[Demo] ERROR: No hay menú para {demo_phone_id}")

                                    return {"status": "demo_started"}
                                else:
                                    print(f"[Demo] Bot demo '{demo_phone_id}' no encontrado"); sys.stdout.flush()

                            # Si es mensaje de salir de demo
                            if texto_lower in ["salir", "terminar", "terminar demo", "salir demo"]:
                                if session and session.get("demo_mode"):
                                    database.delete_user_session(numero_usuario, phone_number_id)
                                    print(f"[Demo] Terminando sesión de demo para {numero_usuario}"); sys.stdout.flush()
                                    msg_salida = "Has salido del modo demo. Ahora vuelvo a ser el asistente general de Zotek Soluciones IA. En que mas puedo ayudarte?"
                                    whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, msg_salida, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    return {"status": "demo_ended"}

                        # ============================================
                        # FLUJO DE RESERVA INTERACTIVA (Restaurante)
                        # ============================================
                        # Verificar si el usuario está en medio de un flujo de reserva (dentro de session_data)
                        reservation_session = database.get_user_session(numero_usuario, phone_number_id)
                        if reservation_session and reservation_session.get('session_data', {}).get('reservation_flow'):
                            flow_state = reservation_session['session_data']['reservation_flow']
                            current_step = flow_state.get('step', 1)

                            print(f"[Reserva] Usuario en paso {current_step} del flujo de reserva"); sys.stdout.flush()

                            # Manejar cada paso del flujo
                            if current_step == 1:  # Fecha
                                # Guardar fecha seleccionada - preservar session_data
                                from copy import deepcopy
                                new_session_data = deepcopy(session.get('session_data', {}))
                                new_session_data['reservation_flow'] = {
                                    'step': 2,
                                    'fecha': texto_usuario,
                                    'inicio': flow_state.get('inicio')
                                }
                                database.save_user_session(numero_usuario, phone_number_id, new_session_data)

                                # Enviar siguiente pregunta con botones
                                fecha_msg = f"¡Perfecto! Reserva para: *{texto_usuario}* 📅\n\n"
                                fecha_msg += "¿Para *cuántas personas* es la reserva?\n\n"
                                whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, fecha_msg, client_data['whatsapp_token'], client_data['phone_number_id'])

                                # Enviar botones con opciones de personas
                                personas_opciones = ["1-2 personas", "3-4 personas", "5+ personas"]
                                whatsapp_service.enviar_menu_botones(numero_usuario, "Selecciona el número de personas:", personas_opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                return {"status": "reservation_step_1"}

                            elif current_step == 2:  # Personas
                                # Guardar número de personas
                                database.save_user_session(numero_usuario, phone_number_id, {
                                    'reservation_flow': {
                                        'step': 3,
                                        'fecha': flow_state.get('fecha'),
                                        'personas': texto_usuario,
                                        'inicio': flow_state.get('inicio')
                                    }
                                })

                                # Enviar siguiente pregunta con botones de horario
                                personas_msg = f"¡Excelente! Para *{texto_usuario}* 👥\n\n"
                                personas_msg += "¿Qué *horario* prefieres?\n\n"
                                whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, personas_msg, client_data['whatsapp_token'], client_data['phone_number_id'])

                                horario_opciones = ["Comida (1-5pm)", "Cena (6-10pm)"]
                                whatsapp_service.enviar_menu_botones(numero_usuario, "Selecciona el horario:", horario_opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                return {"status": "reservation_step_2"}

                            elif current_step == 3:  # Horario
                                # Guardar horario - preservar session_data
                                from copy import deepcopy
                                new_session_data = deepcopy(session.get('session_data', {}))
                                new_session_data['reservation_flow'] = {
                                    'step': 4,
                                    'fecha': flow_state.get('fecha'),
                                    'personas': flow_state.get('personas'),
                                    'horario': texto_usuario,
                                    'inicio': flow_state.get('inicio')
                                }
                                database.save_user_session(numero_usuario, phone_number_id, new_session_data)

                                # Pedir nombre
                                horario_msg = f"¡Genial! Horario: *{texto_usuario}* ⏰\n\n"
                                horario_msg += "Solo falta tu *nombre* para la reserva.\n\n"
                                horario_msg += "¿Cómo te llamas?"
                                whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, horario_msg, client_data['whatsapp_token'], client_data['phone_number_id'])
                                return {"status": "reservation_step_3"}

                            elif current_step == 4:  # Nombre - Confirmar
                                # Obtener todos los datos
                                fecha = flow_state.get('fecha', 'N/A')
                                personas = flow_state.get('personas', 'N/A')
                                horario = flow_state.get('horario', 'N/A')
                                nombre = texto_usuario

                                # Mensaje de confirmación
                                confirmacion_msg = f"¡Reserva confirmada! ✅\n\n"
                                confirmacion_msg += f"*Detalles:*\n"
                                confirmacion_msg += f"📅 Fecha: {fecha}\n"
                                confirmacion_msg += f"👥 Personas: {personas}\n"
                                confirmacion_msg += f"⏰ Horario: {horario}\n"
                                confirmacion_msg += f"👤 Nombre: {nombre}\n\n"
                                confirmacion_msg += f"*¡Te esperamos en La Mesa Elegante!*\n\n"
                                confirmacion_msg += f"📍 Av. Principal #123, Centro\n"
                                confirmacion_msg += f"📞 Tel: 55-1234-5678\n\n"
                                confirmacion_msg += f"¿Necesitas algo más?"

                                whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, confirmacion_msg, client_data['whatsapp_token'], client_data['phone_number_id'])

                                # Limpiar sesión de reserva
                                database.delete_user_session(numero_usuario, phone_number_id)
                                return {"status": "reservation_completed"}

                        # ============================================
                        # FIN DEL FLUJO DE RESERVA
                        # ============================================

                        if not client_data.get('is_active', True):
                            print(f"[Webhook] Bot is INACTIVE for '{client_data['name']}'. Skipping AI."); sys.stdout.flush()
                            # Still send a polite message to the user
                            try:
                                whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, "Gracias por contactarnos. En este momento el bot está temporalmente no disponible. Por favor intenta más tarde.", client_data.get('whatsapp_token', ''), client_data.get('phone_number_id', ''))
                            except:
                                pass
                            return {"status": "bot_inactive"}

                        # Validar token de WhatsApp
                        if not client_data.get('whatsapp_token'):
                            print(f"❌ ERROR: No WhatsApp token configured for '{client_data['name']}'"); sys.stdout.flush()
                            # No podemos enviar mensaje sin token, pero continuamos con Gemini para logging
                            # Marcar para no intentar enviar WhatsApp
                            skip_whatsapp = True
                        else:
                            skip_whatsapp = False
                            print(f"[Webhook] Bot is ACTIVE. WhatsApp token present: {bool(client_data.get('whatsapp_token'))}, token starts: {str(client_data.get('whatsapp_token', ''))[:15]}..."); sys.stdout.flush()

                        # Intercepción de Opciones del Menú Personalizado
                        # En PostgreSQL, el menú está en client_data['menu_json']
                        # Si el usuario está en una demo, cargar el menú del demo, no el de Zotek
                        session_is_demo = session and session.get('demo_mode')
                        # session_data está dentro de session['session_data']
                        session_data_dict = session.get('session_data', {}) if session else {}
                        demo_phone_id_from_session = session_data_dict.get('demo_phone_id') if session_is_demo else None

                        print(f"[DEBUG] session_is_demo: {session_is_demo}"); sys.stdout.flush()
                        print(f"[DEBUG] demo_phone_id_from_session: {demo_phone_id_from_session}"); sys.stdout.flush()

                        menu_data = None
                        try:
                            # Si es demo, cargar el menú del demo
                            if session_is_demo and demo_phone_id_from_session:
                                print(f"[DEBUG] Loading demo menu for: {demo_phone_id_from_session}"); sys.stdout.flush()
                                demo_client_for_menu = database.get_client_by_phone_id(demo_phone_id_from_session)
                                print(f"[DEBUG] demo_client_for_menu: {bool(demo_client_for_menu)}"); sys.stdout.flush()
                                if demo_client_for_menu and demo_client_for_menu.get('menu_json'):
                                    menu_json_str = demo_client_for_menu.get('menu_json')
                                    if isinstance(menu_json_str, str):
                                        menu_data = json.loads(menu_json_str)
                                        print(f"[DEBUG] menu_data loaded from DEMO string"); sys.stdout.flush()
                                    elif isinstance(menu_json_str, dict):
                                        menu_data = menu_json_str
                                        print(f"[DEBUG] menu_data loaded from DEMO dict"); sys.stdout.flush()
                            # Si no es demo, cargar el menú del cliente normal
                            elif client_data and client_data.get('menu_json'):
                                menu_json_str = client_data.get('menu_json')
                                if isinstance(menu_json_str, str):
                                    menu_data = json.loads(menu_json_str)
                                elif isinstance(menu_json_str, dict):
                                    menu_data = menu_json_str
                        except Exception as e:
                            print(f"DEBUG: Error al cargar menú desde JSON: {e}"); sys.stdout.flush()
                            import traceback
                            traceback.print_exc()

                        if menu_data:
                            print(f"[DEBUG] menu_data loaded, options count: {len(menu_data.get('options', []))}"); sys.stdout.flush()

                            def clean_string(s):
                                if not s: return ""
                                # Eliminar emojis, caracteres especiales y acentos
                                s = re.sub(r'[^\w\s]', '', s)
                                # Normalizar: eliminar acentos y convertir a lowercase
                                s = s.lower().strip()
                                # Eliminar espacios multiples
                                s = re.sub(r'\s+', ' ', s)
                                return s

                            def buscar_opcion(opciones, texto):
                                """Busca una opción en el menú de forma resiliente."""
                                cleaned_text = clean_string(texto)
                                print(f"[DEBUG] buscar_opcion: texto='{texto}', cleaned='{cleaned_text}'"); sys.stdout.flush()
                                if not cleaned_text: return None

                                for opt in opciones:
                                    is_dict = isinstance(opt, dict)
                                    title = opt.get('title') if is_dict else str(opt)
                                    icon = opt.get('icon', '') if is_dict else ''
                                    cleaned_title = clean_string(title)

                                    print(f"[DEBUG]   checking option: title='{title}', cleaned='{cleaned_title}'"); sys.stdout.flush()

                                    # 1. Emparejamiento exacto o por título limpio
                                    if cleaned_title == cleaned_text:
                                        print(f"[DEBUG]   MATCH 1: exact clean"); sys.stdout.flush()
                                        return opt

                                    # 2. Emparejamiento parcial (contiene el texto)
                                    if cleaned_text in cleaned_title:
                                        print(f"[DEBUG]   MATCH 2: partial"); sys.stdout.flush()
                                        return opt

                                    # 3. Emparejamiento con icono si viene en el texto
                                    full_title = f"{icon} {title}".strip()
                                    if clean_string(full_title) == cleaned_text:
                                        print(f"[DEBUG]   MATCH 3: with icon exact"); sys.stdout.flush()
                                        return opt
                                    if cleaned_text in clean_string(full_title):
                                        print(f"[DEBUG]   MATCH 4: with icon partial"); sys.stdout.flush()
                                        return opt

                                    # 4. Emparejamiento sin icono (por si el usuario no incluye el emoji)
                                    if icon and cleaned_title == cleaned_text:
                                        print(f"[DEBUG]   MATCH 5: no emoji"); sys.stdout.flush()
                                        return opt

                                    # 5. Recursión para submenús
                                    if is_dict and opt.get('submenu') and opt['submenu'].get('options'):
                                        found = buscar_opcion(opt['submenu']['options'], texto)
                                        if found: return found
                                    elif is_dict and 'opciones' in opt:
                                        found = buscar_opcion(opt['opciones'], texto)
                                        if found: return found
                                return None

                            match = buscar_opcion(menu_data.get('options', []), texto_usuario)
                            if not match and 'opciones' in menu_data:
                                match = buscar_opcion(menu_data['opciones'], texto_usuario)

                            if match and isinstance(match, dict):
                                # ============================================
                                # INICIAR FLUJO DE RESERVA (Restaurante)
                                # ============================================
                                titulo_match = str(match.get('title', '')).lower()
                                if 'reserva' in titulo_match and 'hacer' in titulo_match:
                                    print(f"[Reserva] Iniciando flujo de reserva para {numero_usuario}"); sys.stdout.flush()

                                    # Guardar estado inicial del flujo
                                    database.save_user_session(numero_usuario, phone_number_id, {
                                        'reservation_flow': {
                                            'step': 1,
                                            'inicio': datetime.now().isoformat()
                                        }
                                    })

                                    # Enviar primer mensaje del flujo
                                    reserva_msg = "¡Excelente elección! 🎉\n\n"
                                    reserva_msg += "*Vamos a agendar tu reserva*\n\n"
                                    reserva_msg += "Primero, ¿para qué *fecha* te gustaría reservar?\n\n"
                                    reserva_msg += "*Opciones:*\n"
                                    reserva_msg += "• Hoy\n"
                                    reserva_msg += "• Mañana\n"
                                    reserva_msg += "• Otra fecha (escribe la fecha)\n\n"
                                    reserva_msg += "¿Cuál prefieres?"

                                    whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, reserva_msg, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    return {"status": "reservation_started"}

                                # ============================================
                                # FIN FLUJO DE RESERVA
                                # ============================================

                                if match.get('submenu') and match['submenu'].get('options'):
                                    sub = match['submenu']
                                    titles = []
                                    for o in sub['options']:
                                        t = o.get('title', 'Opción') if isinstance(o, dict) else str(o)
                                        i = o.get('icon', '') if isinstance(o, dict) else ''
                                        if i and t.startswith(i):
                                            titles.append(t.strip())
                                        else:
                                            titles.append(f"{i} {t}".strip())

                                    if not skip_whatsapp:
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

                                    # Inline de enviar_respuesta_con_opciones
                                    texto_para_enviar = res_text
                                    opciones_dinamicas = []
                                    if "[OPCIONES]:" in res_text:
                                        partes = res_text.split("[OPCIONES]:")
                                        texto_para_enviar = partes[0].strip()
                                        dict_opciones = partes[1].split("|")
                                        opciones_dinamicas = [o.strip() for o in dict_opciones if o.strip()]

                                    if not skip_whatsapp:
                                        database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, res_text)
                                        whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, texto_para_enviar, client_data['whatsapp_token'], client_data['phone_number_id'])
                                        if opciones_dinamicas:
                                            if len(opciones_dinamicas) > 3:
                                                whatsapp_service.enviar_menu_lista(numero_usuario, "Selecciona:", "Opciones", "Menú", opciones_dinamicas, client_data['whatsapp_token'], client_data['phone_number_id'])
                                            elif len(opciones_dinamicas) > 0:
                                                whatsapp_service.enviar_menu_botones(numero_usuario, "Selecciona:", opciones_dinamicas, client_data['whatsapp_token'], client_data['phone_number_id'])
                                    return {"status": "predefined_sent"}

                                # Caso: opción de menú sin response ni submenu - usar fallback
                                elif menu_data and menu_data.get('fallback_text'):
                                    print(f"DEBUG: Opción '{match.get('title')}' sin response. Usando fallback_text."); sys.stdout.flush()
                                    if not skip_whatsapp:
                                        whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, menu_data['fallback_text'], client_data['whatsapp_token'], client_data['phone_number_id'])
                                        database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, menu_data['fallback_text'])
                                    return {"status": "fallback_sent"}

                                # Caso: opción de menú sin response - dejar que Gemini responda
                                else:
                                    print(f"DEBUG: Opción '{match.get('title')}' sin response. Gemini responderá."); sys.stdout.flush()
                                    # Continuar a Gemini, no retornar aquí

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
                                    if i and t.startswith(i):
                                        opciones.append(t.strip())
                                    else:
                                        opciones.append(f"{i} {t}".strip())

                                print(f"[send_menu_followup_inline] Sending menu with {len(opciones)} options to {numero_usuario}"); sys.stdout.flush()
                                if not skip_whatsapp:
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
                                    print(f"[Webhook] Would send menu but skip_whatsapp=True"); sys.stdout.flush()
                                    return {"status": "menu_skipped"}
                            else:
                                print(f"[Webhook] Menu has 0 options. Allowing Gemini to handle the greeting."); sys.stdout.flush()
                                # Do not return here. Let it fall through to Gemini.

                        # Obtenemos si es el maestro Zotek para decidir si saltamos el fallback del menú
                        es_zotek_maestro = str(client_data.get('id', '')) == '10'

                        # Fallback text - only if menu_data exists and no match was found (Y NO ES ZOTEK MAESTRO)
                        if menu_data and not match and menu_data.get('fallback_text') and not es_zotek_maestro:
                            print(f"DEBUG: No menu match found. Sending fallback_text for {client_data['name']}"); sys.stdout.flush()
                            fallback_msg = menu_data['fallback_text']
                            opciones_raw = menu_data.get('options', menu_data.get('opciones', []))
                            opciones = []
                            for opt in opciones_raw:
                                t = opt.get('title', 'Opción') if isinstance(opt, dict) else str(opt)
                                i = opt.get('icon', '') if isinstance(opt, dict) else ''
                                if i and t.startswith(i):
                                    opciones.append(t.strip())
                                else:
                                    opciones.append(f"{i} {t}".strip())

                            if not skip_whatsapp and len(opciones) > 0:
                                if len(opciones) > 3:
                                    whatsapp_service.enviar_menu_lista(numero_usuario, fallback_msg, "Ver Opciones", "Menú", opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                else:
                                    whatsapp_service.enviar_menu_botones(numero_usuario, fallback_msg, opciones, client_data['whatsapp_token'], client_data['phone_number_id'])
                                database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, f"[Fallback enviado: {fallback_msg}]")
                                return {"status": "fallback_sent"}
                            elif len(opciones) == 0:
                                print(f"[Webhook] Fallback has 0 options. Allowing Gemini to handle."); sys.stdout.flush()
                                # Let Gemini handle it

                        # --- INYECCIÓN DE CONTEXTO DEMO ---
                        session = database.get_user_session(numero_usuario, phone_number_id)
                        if session and session.get('demo_mode'):
                            demo_mode = session['demo_mode']
                            demo_phone_id = session.get('demo_phone_id')

                            # Cargar el bot demo desde la base de datos si tenemos el phone_id
                            if demo_phone_id:
                                demo_client = database.get_client_by_phone_id(demo_phone_id)
                                if demo_client:
                                    # Reemplazar client_data con el bot demo completo
                                    client_data = demo_client
                                    print(f"[Demo] Usando bot '{client_data.get('name')}' desde la base de datos."); sys.stdout.flush()
                            else:
                                # Fallback: intentar encontrar el demo por modo (solo si no hay phone_id)
                                demo_phone_ids = {
                                    "restaurante": "demo_restaurant",
                                    "tienda": "demo_retail",
                                    "dental": "demo_dental",
                                    "psicologo": "demo_psychology",
                                    "salon": "demo_salon"
                                }
                                if demo_mode in demo_phone_ids:
                                    demo_client = database.get_client_by_phone_id(demo_phone_ids[demo_mode])
                                    if demo_client:
                                        client_data = demo_client
                                        print(f"[Demo] Usando bot '{client_data.get('name')}' desde la base de datos."); sys.stdout.flush()
                        
                        prompt = texto_usuario
                        if message.get('type') == 'interactive':
                            prompt = f"[Menú]: {texto_usuario}"

                        if menu_data:
                            client_data['menu_data'] = menu_data

                        # ============================================
                        # RAG: Inyectar conocimiento de PDFs en el contexto
                        # ============================================
                        knowledge = database.get_client_knowledge(client_data['id'])
                        contexto_pdf = ""

                        if knowledge and len(knowledge) > 0:
                            # el conocimiento ya viene como un string concatenado desde database.py
                            contexto_pdf = knowledge

                            # Inyectar en system_instruction temporalmente
                            original_instruction = client_data.get('system_instruction', '')
                            client_data['system_instruction'] = f"""{original_instruction}

📚 CONOCIMIENTO DE DOCUMENTOS ADJUNTOS:
El cliente ha subido los siguientes documentos que contienen información importante. Usa esta información para responder preguntas específicas:

{contexto_pdf[:15000]}  # Limitar para no exceder token limit

INSTRUCCIONES:
- Si el usuario pregunta algo relacionado con los documentos, usa la información de arriba para responder.
- Si no encuentras la respuesta en los documentos, responde honestamente que no tienes esa información.
- Cita la fuente cuando sea posible (nombre del archivo).
- Sé preciso y específico con la información de los documentos.
"""
                            print(f"[RAG] Injected {len(contexto_pdf)} chars of knowledge context"); sys.stdout.flush()
                        else:
                            print(f"[RAG] No knowledge base found for client {client_data['id']}"); sys.stdout.flush()
                               # ============================================
                        # LLAMADA AL MOTOR DE IA (AGENTE O LEGACY)
                        # ============================================
                        print(f"[Webhook] Calling AI Engine for: '{prompt[:50]}...'"); sys.stdout.flush()

                        if gemini is None:
                            print(f"❌ ERROR: Gemini not initialized."); sys.stdout.flush()
                            return {"status": "no_gemini"}

                        # Si es el Bot Maestro de Zotek (ID 10), usar flujo de Agente Inteligente
                        es_zotek_maestro = str(client_data.get('id', '')) == '10'
                        
                        if es_zotek_maestro:
                            print(f"🚀 INICIANDO FLUJO DE AGENTE PARA ZOTEK (ID 10)"); sys.stdout.flush()
                            agent_output = gemini.generar_respuesta_agente(prompt, client_data, numero_usuario)
                            res_ai = agent_output.get('text', '')
                            tool_calls = agent_output.get('tool_calls', [])
                            
                            # Ejecutar acciones autónomas si el agente lo solicitó
                            if tool_calls:
                                ejecutar_herramientas_agente(
                                    tool_calls, 
                                    numero_usuario, 
                                    client_data, 
                                    phone_number_id, 
                                    client_data.get('whatsapp_token', '')
                                )
                        else:
                            # Flujo tradicional para otros clientes
                            res_ai = gemini.generar_respuesta(prompt, client_data, numero_usuario)

                        print(f"[Webhook] AI response: {res_ai[:80]}..."); sys.stdout.flush()

                        # Parse dynamic [OPCIONES]: generated by Gemini (Fallback legacy)
                        texto_para_enviar = res_ai
                        opciones_dinamicas = []
                        if "[OPCIONES]:" in res_ai:
                            partes = res_ai.split("[OPCIONES]:")
                            texto_para_enviar = partes[0].strip()
                            dict_opciones = partes[1].split("|")
                            opciones_dinamicas = [o.strip() for o in dict_opciones if o.strip()][:10] # WhatsApp list limit 10

                        # Enviar respuesta solo si tenemos token
                        success = False
                        if not skip_whatsapp:
                            success = whatsapp_service.enviar_mensaje_whatsapp(numero_usuario, texto_para_enviar, client_data['whatsapp_token'], client_data['phone_number_id'])

                            if success and opciones_dinamicas:
                                if len(opciones_dinamicas) > 3:
                                    whatsapp_service.enviar_menu_lista(numero_usuario, "Por favor, selecciona una opción:", "Ver opciones", "Menú", opciones_dinamicas, client_data['whatsapp_token'], client_data['phone_number_id'])
                                elif len(opciones_dinamicas) > 0:
                                    whatsapp_service.enviar_menu_botones(numero_usuario, "Selecciona una opción:", opciones_dinamicas, client_data['whatsapp_token'], client_data['phone_number_id'])

                            print(f"[Webhook] WhatsApp send result: {success}"); sys.stdout.flush()
                        else:
                            print(f"[Webhook] Skipping WhatsApp send (no token)"); sys.stdout.flush()
                            success = True  # Mark as success for logging purposes

                        if success:
                            database.save_chat_message(client_data['id'], numero_usuario, texto_usuario, res_ai)

    except Exception as e:
        import traceback
        error_msg = f"❌ WEBHOOK CRITICAL ERROR: {e}\n{traceback.format_exc()}"
        print(error_msg); sys.stdout.flush()

        # Intentar notificar al usuario sobre el error
        try:
            if 'numero_usuario' in locals() and 'client_data' in locals():
                if client_data.get('whatsapp_token'):
                    whatsapp_service.enviar_mensaje_whatsapp(
                        numero_usuario,
                        "Lo siento, ocurrió un error técnico al procesar tu mensaje. Por favor intenta de nuevo más tarde.",
                        client_data.get('whatsapp_token'),
                        client_data.get('phone_number_id', '')
                    )
        except:
            pass  # No hacer ruido si falla el envío del error

    return {"status": "ok"}


# === Security Helpers ===

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(hours=8))
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
        "expiry": datetime.now() + timedelta(minutes=10)
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
    if not stored or stored["code"] != code or datetime.now() > stored["expiry"]:
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

    # Separar el menú si viene incluido para guardarlo en menu_json
    menu_data = data.pop('menu', None)

    if menu_data:
        data['menu_json'] = menu_data

    if database.update_client(client_id, data):
        return {"status": "updated"}
    raise HTTPException(status_code=400, detail="Error updating client")


@app.get("/api/clients/{client_id}")
async def get_client(client_id: str, current_user: str = Depends(get_current_user)):
    client = database.get_client_by_id(client_id)
    if client:
        return client
    raise HTTPException(status_code=404, detail="Client not found")


@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: str, current_user: str = Depends(get_current_user)):
    """Elimina permanentemente un cliente de la base de datos PostgreSQL."""
    print(f"📥 DELETE /api/clients/{client_id} called")

    # Prevenir eliminación de demos hardcodeados
    if str(client_id).startswith('demo_'):
        print(f"⚠️ Attempted to delete demo client {client_id}")
        raise HTTPException(status_code=403, detail="No se pueden eliminar clientes de demostración")

    try:
        # database.delete_client_db_entry ya maneja la eliminación en cascada
        if database.delete_client_db_entry(client_id):
            print(f"✅ Cliente {client_id} eliminado exitosamente")
            return {"status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error eliminando cliente: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")


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
    client = database.get_client_by_id(client_id)
    if client and client.get('menu_json'):
        menu_json = client.get('menu_json')
        if isinstance(menu_json, str):
            try:
                return json.loads(menu_json)
            except:
                pass
        return menu_json
    return {"text": "", "options": ["Servicios", "Agendar Cita", "Contacto"]}

@app.post("/api/clients/{client_id}/menu")
async def update_client_menu(client_id: str, request: Request, current_user: str = Depends(get_current_user)):
    """Actualiza la configuración del menú de un cliente."""
    data = await request.json()
    if database.update_client(client_id, {'menu_json': data}):
        return {"status": "updated"}
    raise HTTPException(status_code=400, detail="Error updating menu")

@app.post("/api/clients/{client_id}/reset")
async def reset_demo_client(client_id: str, current_user: str = Depends(get_current_user)):
    """Restablece la configuración de un cliente de demostración a su estado original."""
    
    # Verificar que sea un cliente demo (ID debe comenzar con 'demo_')
    if not str(client_id).startswith('demo_'):
        raise HTTPException(status_code=400, detail="Solo se pueden restablecer los clientes de ejemplo (ID debe comenzar con 'demo_').")
    
    # Plantillas de configuración original por tipo de demo
    demo_templates = {
        "restaurante": {
            "name": "🤖 Demo GourmetBot 2026",
            "email": "restaurante@ejemplo.com",
            "is_active": True,
            "menu": {
                "text": "¡Bienvenido a *GourmetBot 2026*! 👋 Soy tu asistente virtual del restaurante 'La Mesa Elegante'. ¿Qué te gustaría hacer hoy?",
                "options": [
                    {"title": "Ver Menú", "icon": "🍕", "response": "Nuestro menú incluye pizzas a la leña, pastas frescas y postres italianos."},
                    {"title": "Hacer Reserva", "icon": "📅", "response": "Indícanos la fecha y hora para verificar disponibilidad."},
                    {"title": "Horarios", "icon": "⏰", "response": "Estamos abiertos todos los días de 12:00 PM a 11:00 PM."}
                ],
                "fallback_text": "Lo siento, no entendí eso. Aquí tienes las opciones principales de GourmetBot 2026:"
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
                    {"title": "Ver Catálogo", "icon": "��", "response": "Nuestra nueva colección de otoño ya está disponible."},
                    {"title": "Tallas", "icon": "📏", "response": "Manejamos tallas desde XS hasta XL en la mayoría de nuestras prendas."},
                    {"title": "Devoluciones", "icon": "🔄", "response": "Tienes 30 días para realizar cambios o devoluciones con tu ticket."}
                ],
                "fallback_text": "Ups, no reconozco eso. Aquí tienes lo que puedo hacer por ti en Moda Urbana:"
            }
        },
        "dental": {
            "name": "SonrisaPerfecta IA (Dental)",
            "is_active": True,
            "menu": {
                "text": "¡Hola! Bienvenido a *SonrisaPerfecta IA*. 🦷 Especialistas en tu sonrisa. ¿Qué necesitas?",
                "options": [
                    {"title": "Agendar Cita", "icon": "📅", "response": "Contamos con horarios disponibles de Lunes a Viernes."},
                    {"title": "Precios", "icon": "💰", "response": "Limpieza: $500, Blanqueamiento: $2000, Consulta: $300."},
                    {"title": "Ubicación", "icon": "📍", "response": "Calle Odontología #456, Col. Dental."}
                ],
                "fallback_text": "No comprendo. Selecciona una opción para continuar:"
            }
        },
        "psychology": {
            "name": "MenteSana Bot (Psicólogo)",
            "is_active": True,
            "menu": {
                "text": "Hola, bienvenido al consultorio del *Dr. Alejandro Ruiz*. 🧠 ¿Cómo puedo apoyarte hoy?",
                "options": [
                    {"title": "Agendar Sesión", "icon": "📅", "response": "Me encantaría ayudarte a agendar. ¿Buscas sesión online o presencial?"},
                    {"title": "Información", "icon": "ℹ️", "response": "El Dr. Ruiz se especializa en Terapia Cognitivo-Conductual."},
                    {"title": "Costos", "icon": "💰", "response": "La sesión de 50 minutos tiene un costo de $900 MXN."}
                ],
                "fallback_text": "Por favor selecciona una de las opciones administrativas:"
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
    elif 'dental' in phone_id or 'dental' in client_id.lower():
        template_key = 'dental'
    elif 'psychology' in phone_id or 'psychology' in client_id.lower() or 'psicologo' in client_id.lower():
        template_key = 'psychology'
    
    # Si no se pudo determinar, intentar por el nombre del cliente
    if not template_key:
        client_name = str(current_data.get('name', '')).lower()
        if 'restaurante' in client_name or 'gourmet' in client_name or 'la mesa elegante' in client_name:
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

@app.delete("/api/clients/{client_id}/clear-chats")
async def clear_chats(client_id: str, current_user: str = Depends(get_current_user)):
    """Elimina todos los chats de un cliente."""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM client_chats WHERE client_id = %s', (client_id,))
        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "cleared", "deleted_count": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NOTA: La ruta /api/migrate fue eliminada porque la migración a PostgreSQL ya está completa.
# El sistema ahora usa exclusivamente PostgreSQL (InsForge) como base de datos.

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
    import sys

    if not PdfReader:
        try:
            from pypdf import PdfReader as PR
            PdfReader = PR
            print("[PDF] pypdf imported successfully"); sys.stdout.flush()
        except ImportError as e:
            print(f"[PDF] ImportError: {e}"); sys.stdout.flush()
            raise HTTPException(status_code=500, detail=f"Biblioteca pypdf no instalada. Error: {str(e)}")

    try:
        print(f"[PDF] === START UPLOAD ==="); sys.stdout.flush()
        print(f"[PDF] Client ID: {client_id}"); sys.stdout.flush()

        form = await request.form()
        file = form.get("file")
        print(f"[PDF] File received: {bool(file)}"); sys.stdout.flush()

        if not file or not hasattr(file, 'filename'):
            print(f"[PDF] No file in request"); sys.stdout.flush()
            raise HTTPException(status_code=400, detail="No se recibió ningún archivo.")

        print(f"[PDF] Filename: {file.filename}"); sys.stdout.flush()

        if not file.filename.lower().endswith(".pdf"):
            print(f"[PDF] Invalid extension: {file.filename}"); sys.stdout.flush()
            raise HTTPException(status_code=400, detail=f"Solo se permiten archivos PDF. Recibido: {file.filename}")

        print(f"[PDF] Reading file content..."); sys.stdout.flush()
        contents = await file.read()
        print(f"[PDF] File size: {len(contents)} bytes ({len(contents)/1024:.1f} KB)"); sys.stdout.flush()

        f = io.BytesIO(contents)

        print(f"[PDF] Initializing PdfReader..."); sys.stdout.flush()
        try:
            reader = PdfReader(f)
            print(f"[PDF] Pages count: {len(reader.pages)}"); sys.stdout.flush()
        except Exception as e:
            print(f"[PDF] PdfReader error: {e}"); sys.stdout.flush()
            raise HTTPException(status_code=400, detail=f"Error leyendo PDF: {str(e)}. El archivo podría estar corrupto o protegido con contraseña.")

        text_content = ""

        for i, page in enumerate(reader.pages):
            print(f"[PDF] Extracting page {i+1}/{len(reader.pages)}..."); sys.stdout.flush()
            try:
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
                    print(f"[PDF] Page {i+1}: {len(extracted)} chars"); sys.stdout.flush()
                else:
                    print(f"[PDF] Page {i+1}: NO TEXT (might be image)"); sys.stdout.flush()
            except Exception as page_error:
                print(f"[PDF] Page {i+1} error: {page_error}"); sys.stdout.flush()
                # Continue with next page

        print(f"[PDF] Total extracted: {len(text_content)} characters"); sys.stdout.flush()

        if not text_content.strip():
            print(f"[PDF] No text extracted - PDF is image-only"); sys.stdout.flush()
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF. El archivo parece contener solo imágenes. Usa un PDF con texto seleccionable.")

        # Save to database
        print(f"[PDF] Saving to knowledge_base..."); sys.stdout.flush()
        result = database.add_knowledge_entry(client_id, text_content, source_file=file.filename)

        if result:
            print(f"[PDF] SUCCESS!"); sys.stdout.flush()
            return {
                "status": "success",
                "message": f"PDF '{file.filename}' procesado correctamente.",
                "extracted_length": len(text_content),
                "pages": len(reader.pages)
            }
        else:
            print(f"[PDF] Database save returned False"); sys.stdout.flush()
            raise HTTPException(status_code=500, detail="Error guardando en la base de datos.")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"[PDF] CRITICAL ERROR: {e}\n{traceback.format_exc()}"
        print(error_msg); sys.stdout.flush()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================
# ENDPOINTS DE EMAIL CONFIGURATION
# ============================================

@app.get("/api/clients/{client_id}/email-config")
async def get_email_config(client_id: str, current_user: str = Depends(get_current_user)):
    """Obtiene la configuración de email de un cliente"""
    client = database.get_client_by_id(client_id) if client_id.isdigit() else database.get_client_by_phone_id(client_id)
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
async def update_email_config(client_id: str, request: Request, current_user: str = Depends(get_current_user)):
    """Actualiza la configuración de email de un cliente"""
    data = await request.json()

    # Actualizar configuración
    config = {
        'email_smtp_server': data.get('smtp_server', 'smtp.gmail.com'),
        'email_smtp_port': data.get('smtp_port', 587),
        'email_user': data.get('email_user', ''),
        'email_password': data.get('email_password', ''),  # Se guarda encriptado en producción
        'email_from_name': data.get('email_from_name', ''),
        'email_notifications_enabled': data.get('notifications_enabled', False)
    }

    client_id_value = int(client_id) if client_id.isdigit() else client_id
    if database.update_client(client_id_value, config):
        return {"status": "updated", "message": "Configuración de email guardada"}
    raise HTTPException(status_code=400, detail="Error al guardar configuración")

@app.post("/api/clients/{client_id}/email-test")
async def test_email_config(client_id: str, request: Request, current_user: str = Depends(get_current_user)):
    """Prueba la configuración de email enviando un email de prueba"""
    from src.services.email_service import EmailService

    data = await request.json()
    test_email = data.get('email', '')

    if not test_email:
        raise HTTPException(status_code=400, detail="Email de prueba requerido")

    client = database.get_client_by_id(client_id) if client_id.isdigit() else database.get_client_by_phone_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    email_service = EmailService(
        smtp_server=client.get('email_smtp_server', 'smtp.gmail.com'),
        smtp_port=client.get('email_smtp_port', 587),
        email_user=client.get('email_user', ''),
        email_password=client.get('email_password', ''),
        email_from_name=client.get('email_from_name', '')
    )

    success = email_service.send_email(
        to=test_email,
        subject="✅ Configuración de email exitosa - Zotek IA",
        body=f"¡Hola!\n\nTu configuración de email en Zotek IA está funcionando correctamente.\n\nEste es un email de prueba.\n\n{client.get('name', '')}"
    )

    if success:
        return {"status": "success", "message": "Email de prueba enviado correctamente"}
    raise HTTPException(status_code=500, detail="Error al enviar email de prueba")


# ============================================
# ENDPOINTS DE LEAD TRACKING
# ============================================

@app.get("/api/clients/{client_id}/leads")
async def get_client_leads(client_id: str, status: str = None, limit: int = 50,
                          current_user: str = Depends(get_current_user)):
    """Obtiene los leads de un cliente"""
    from src.services.lead_service import LeadService
    lead_service = LeadService()

    client_id_value = int(client_id) if client_id.isdigit() else client_id

    try:
        conn = lead_service.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT * FROM lead_tracking
            WHERE client_id = %s
        """
        params = [client_id_value]

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
async def get_cold_leads(client_id: str, hours: int = 24,
                         current_user: str = Depends(get_current_user)):
    """Obtiene leads fríos (no han respondido en X horas)"""
    from src.services.lead_service import LeadService
    lead_service = LeadService()

    client_id_value = int(client_id) if client_id.isdigit() else client_id
    cold_leads = lead_service.get_cold_leads(client_id_value, hours)

    return {"leads": cold_leads, "total": len(cold_leads), "hours": hours}

@app.post("/api/clients/{client_id}/leads/{lead_id}/followup")
async def send_lead_followup(client_id: str, lead_id: int, request: Request,
                            current_user: str = Depends(get_current_user)):
    """Envía follow-up manual a un lead"""
    from src.services.lead_service import LeadService
    from src.services.email_service import get_email_service_for_client

    data = await request.json()
    message = data.get('message', '')
    channel = data.get('channel', 'whatsapp')  # whatsapp o email

    lead_service = LeadService()
    client_id_value = int(client_id) if client_id.isdigit() else client_id

    # Obtener datos del lead
    lead = lead_service.get_lead_by_phone(client_id_value, '')  # Necesitamos el phone

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    # Enviar por WhatsApp (implementar después)
    if channel == 'whatsapp':
        # TODO: Implementar envío por WhatsApp
        return {"status": "pending", "message": "Follow-up por WhatsApp pendiente de implementación"}

    # Enviar por email
    client = database.get_client_by_id(client_id_value)
    email_service = get_email_service_for_client(client)

    if not email_service:
        raise HTTPException(status_code=400, detail="Cliente no tiene configuración de email")

    # TODO: Obtener email del lead (se necesita campo adicional)
    return {"status": "success", "message": "Follow-up enviado"}


# ============================================
# ENDPOINTS DE APPOINTMENTS
# ============================================

@app.get("/api/clients/{client_id}/appointments")
async def get_client_appointments(client_id: str, status: str = None,
                                  current_user: str = Depends(get_current_user)):
    """Obtiene las citas de un cliente"""
    from src.services.appointment_service import AppointmentService
    apt_service = AppointmentService()

    client_id_value = int(client_id) if client_id.isdigit() else client_id

    if status == 'tomorrow':
        appointments = apt_service.get_tomorrow_appointments(client_id_value)
    elif status:
        # Filtrar por status
        try:
            conn = apt_service.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM appointments
                WHERE client_id = %s AND status = %s
                ORDER BY appointment_date ASC
            """, (client_id_value, status))
            appointments = cursor.fetchall()
            cursor.close()
            conn.close()
            appointments = [dict(apt) for apt in appointments]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        appointments = apt_service.get_pending_appointments(client_id_value)

    return {"appointments": appointments, "total": len(appointments)}

@app.post("/api/clients/{client_id}/appointments")
async def create_appointment(client_id: str, request: Request,
                            current_user: str = Depends(get_current_user)):
    """Crea una nueva cita"""
    from src.services.appointment_service import AppointmentService
    apt_service = AppointmentService()

    data = await request.json()
    client_id_value = int(client_id) if client_id.isdigit() else client_id

    # Parsear fecha
    try:
        appointment_date = datetime.fromisoformat(data.get('appointment_date'))
    except:
        raise HTTPException(status_code=400, detail="Fecha inválida. Usa formato ISO")

    appointment_id = apt_service.create_appointment(
        client_id=client_id_value,
        phone_number=data.get('phone_number', ''),
        appointment_date=appointment_date,
        customer_name=data.get('customer_name', ''),
        notes=data.get('notes', '')
    )

    if appointment_id > 0:
        return {"status": "created", "appointment_id": appointment_id}
    raise HTTPException(status_code=400, detail="Error al crear cita")

@app.post("/api/clients/{client_id}/appointments/{appointment_id}/confirm")
async def confirm_appointment(client_id: str, appointment_id: int,
                             current_user: str = Depends(get_current_user)):
    """Confirma una cita"""
    from src.services.appointment_service import AppointmentService
    apt_service = AppointmentService()

    if apt_service.confirm_appointment(appointment_id):
        return {"status": "confirmed", "message": "Cita confirmada"}
    raise HTTPException(status_code=400, detail="Error al confirmar cita")

@app.post("/api/clients/{client_id}/appointments/{appointment_id}/cancel")
async def cancel_appointment(client_id: str, appointment_id: int,
                            current_user: str = Depends(get_current_user)):
    """Cancela una cita"""
    from src.services.appointment_service import AppointmentService
    apt_service = AppointmentService()

    if apt_service.cancel_appointment(appointment_id):
        return {"status": "cancelled", "message": "Cita cancelada"}
    raise HTTPException(status_code=400, detail="Error al cancelar cita")
