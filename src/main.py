# Deploy Trigger: Force redeploy to fix persistent NameError in production.
import os
import json
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from collections import deque
from dotenv import load_dotenv

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
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD") # The 16 character app password

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/verify-code")

# In-memory storage for 2FA codes (In production use Redis)
verification_codes = {} # {email: {"code": str, "expiry": datetime}}

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW_DIR = os.path.join(BASE_DIR, "www")
ADMIN_DIR = os.path.join(WWW_DIR, "admin")

print(f"--- SERVER STARTUP DIAGNOSTICS ---")
print(f"📁 BASE_DIR: {BASE_DIR}")
print(f"📁 WWW_DIR: {WWW_DIR}")
print(f"📁 ADMIN_DIR: {ADMIN_DIR}")
print(f"----------------------------------")

app = FastAPI()

# Initialize Database Schema
database.init_db()

@app.exception_handler(404)
async def custom_404_handler(request: Request, __):
    print(f"🛑 404 Error: {request.url.path}")
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

# Lazy initialization using app events or on first request to ensure DB is ready
@app.on_event("startup")
async def startup_event():
    if not os.environ.get('K_SERVICE'):
        database.init_db()
    
    global gemini
    gemini = GeminiEngine(api_key=GEMINI_API_KEY)

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
            texto_menu = "" # Default to empty string to avoid NameError
            phone_number_id = value['metadata']['phone_number_id']
            
            # Mexico normalization
            if numero_usuario.startswith("521"):
                numero_usuario = numero_usuario.replace("521", "52", 1)
            
            print(f"📩 Mensaje de {numero_usuario} para {phone_number_id}: {texto_usuario}")
            
            # 2. Get client data from DB
            client_data = database.get_client_by_phone_id(phone_number_id)
            
            if not client_data:
                print(f"⚠️ Negocio no registrado: {phone_number_id}")
                return {"status": "unrecognized_client"}

            # 3. Process with Gemini
            respuesta_ai = gemini.generar_respuesta(texto_usuario, client_data, numero_usuario)
            
            # 4. Send via WhatsApp
            whatsapp_service.enviar_mensaje_whatsapp(
                numero=numero_usuario,
                texto=respuesta_ai,
                whatsapp_token=client_data['whatsapp_token'],
                phone_number_id=client_data['phone_number_id']
            )
            print(f"✅ Respuesta enviada con éxito a {numero_usuario}")
            
    except Exception as e:
        print(f"🔥 Error en Webhook: {e}")

    return {"status": "ok"}


# --- Security Helpers ---

def create_access_token(data: dict, expires_delta: timedelta = None):
    print(f"🔑 Generating access token for: {data.get('sub')}")
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"DEBUG: Token generated. Secret Key length: {len(SECRET_KEY)}")
    return token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"🕵️ Validating token: {token[:10]}...{token[-10:] if len(token) > 20 else ''}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        print(f"✅ Token decoded successfully for: {email}")
        if email is None:
            print("❌ Token payload missing 'sub'")
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def send_security_code(email: str, code: str):
    if not EMAIL_PASSWORD:
        print("❌ ERROR: EMAIL_APP_PASSWORD no configurada en .env")
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
        print(f"❌ Error enviando email: {e}")
        traceback.print_exc()
        return False

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

@app.post("/api/auth/request-code")
async def request_code(request: Request):
    data = await request.json()
    email = data.get("email")
    if email != ADMIN_EMAIL:
        return JSONResponse(status_code=403, content={"detail": "Acceso restringido"})
    
    code = f"{random.randint(100000, 999999)}"
    verification_codes[email] = {
        "code": code,
        "expiry": datetime.utcnow() + timedelta(minutes=10)
    }
    
    if send_security_code(email, code):
        return {"status": "code_sent"}
    else:
        raise HTTPException(status_code=500, detail="Error enviando el código")

@app.post("/api/auth/verify-code")
async def verify_code(request: Request):
    data = await request.json()
    email = data.get("email")
    code = data.get("code")
    print(f"📩 Login attempt: Email={email}, Code={code}")
    
    stored = verification_codes.get(email)
    if not stored:
        print(f"❌ No code found in memory for {email}")
        raise HTTPException(status_code=401, detail="Código inválido o expirado")
        
    if stored["code"] != code:
        print(f"❌ Code mismatch: expected {stored['code']}, got {code}")
        raise HTTPException(status_code=401, detail="Código inválido o expirado")
        
    if datetime.utcnow() > stored["expiry"]:
        print(f"❌ Code expired for {email}")
        raise HTTPException(status_code=401, detail="Código inválido o expirado")
    
    print(f"✅ Code verified for {email}")
    # Clean up code
    del verification_codes[email]
    
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

@app.put("/api/clients/{client_id}")
async def update_client(client_id: int, request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()
    # Map 'menu' from frontend to 'menu_json' in DB
    if 'menu' in data:
        data['menu_json'] = json.dumps(data.pop('menu'))
        
    if database.update_client(client_id, data):
        return {"status": "updated"}
    raise HTTPException(status_code=400, detail="Error updating client")

@app.get("/api/clients/{client_id}/menu")
async def get_client_menu(client_id: int, current_user: str = Depends(get_current_user)):
    client = database.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    menu_data = client.get("menu_json")
    if menu_data:
        try:
            return json.loads(menu_data)
        except:
            return {"options": []}
    return {"options": []}

@app.post("/api/clients/{client_id}/reset")
async def reset_client(client_id: int, current_user: str = Depends(get_current_user)):
    """Resetea un cliente, eliminando sus personalizaciones en BD (especial para demos)."""
    if database.delete_client_db_entry(client_id):
        return {"status": "reset_successful"}
    raise HTTPException(status_code=400, detail="Error resetting client")

@app.get("/api/clients/{client_id}")
async def get_client(client_id: int, current_user: str = Depends(get_current_user)):
    client = database.get_client_by_id(client_id)
    if client:
        return client
    raise HTTPException(status_code=404, detail="Client not found")

@app.get("/api/clients/{client_id}/documents")
async def list_documents(client_id: int, current_user: str = Depends(get_current_user)):
    return database.list_client_documents(client_id)

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

# Static Files Mounts (After all specific routes)
if os.path.exists(WWW_DIR):
    print(f"✅ Mounting static files from {WWW_DIR}")
    app.mount("/", StaticFiles(directory=WWW_DIR, html=True), name="root")
else:
    print(f"ℹ️ Skipping static files mount (Directory not found: {WWW_DIR})")

# Production entry point handled by Firebase or Uvicorn from shell
