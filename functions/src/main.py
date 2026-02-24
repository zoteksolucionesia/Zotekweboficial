import os
import random
import threading
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from collections import deque

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
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
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/verify-code")

# In-memory storage for 2FA codes (In production use Redis)
verification_codes = {}  # {email: {"code": str, "expiry": datetime}}

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW_DIR = os.path.join(BASE_DIR, "www")
ADMIN_DIR = os.path.join(WWW_DIR, "admin")

print("--- SERVER STARTUP DIAGNOSTICS ---")
print(f"BASE_DIR: {BASE_DIR}")
print(f"WWW_DIR: {WWW_DIR}")
print(f"ADMIN_DIR: {ADMIN_DIR}")
print("----------------------------------")

app = FastAPI()

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

# Initialize DB at module level (Firebase copies DB to /tmp, locally creates tables)
database.init_db()

# Initialize Gemini at module level (startup events don't fire in our custom ASGI bridge)
gemini = None
print(f"GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}, starts: {GEMINI_API_KEY[:10] if GEMINI_API_KEY else 'NONE'}")
try:
    gemini = GeminiEngine(api_key=GEMINI_API_KEY)
    print("GeminiEngine initialized OK")
except Exception as e:
    print(f"GeminiEngine INIT FAILED: {e}")
    gemini = None


# === WEBHOOK ===

@app.get("/webhook")
async def verify_webhook(request: Request):
    token = request.query_params.get("hub.verify_token")
    if token == VERIFY_TOKEN:
        challenge = request.query_params.get("hub.challenge")
        return int(challenge) if challenge else "Ok"
    return "Error auth", 403


@app.get("/api/debug-env")
async def debug_env():
    """Temporary diagnostic endpoint."""
    return {
        "GEMINI_API_KEY": f"{GEMINI_API_KEY[:10]}..." if GEMINI_API_KEY else "NOT SET",
        "VERIFY_TOKEN": f"{VERIFY_TOKEN[:5]}..." if VERIFY_TOKEN else "NOT SET",
        "SECRET_KEY": "SET" if SECRET_KEY and SECRET_KEY != "ZOTEK_SECRET_DEFAULT_CHANGE_ME" else "DEFAULT",
        "ADMIN_EMAIL": ADMIN_EMAIL,
        "EMAIL_PASSWORD_SET": bool(EMAIL_PASSWORD),
        "gemini_initialized": gemini is not None,
    }


@app.get("/api/test-bot")
async def test_bot():
    """Diagnostic endpoint: runs full Gemini+WhatsApp flow and returns the trace."""
    trace = {}
    try:
        phone_number_id = "980996958435648"
        numero_usuario = "5213351380285"
        texto_usuario = "Hola, esto es una prueba de funcionamiento del bot"

        # 1. Client lookup
        client_data = database.get_client_by_phone_id(phone_number_id)
        trace["client_found"] = client_data is not None
        trace["client_name"] = client_data.get("name") if client_data else None

        if not client_data:
            trace["error"] = "Client not found in DB"
            return trace

        # 2. Gemini
        trace["gemini_initialized"] = gemini is not None
        if gemini is None:
            trace["error"] = "Gemini not initialized"
            return trace

        try:
            respuesta_ai = gemini.generar_respuesta(texto_usuario, client_data, numero_usuario)
            trace["gemini_response"] = respuesta_ai[:200] if respuesta_ai else None
        except Exception as e:
            import traceback
            trace["gemini_error"] = str(e)
            trace["gemini_traceback"] = traceback.format_exc()
            return trace

        # 3. WhatsApp send
        try:
            token = client_data.get("whatsapp_token", "")
            pid = client_data.get("phone_number_id", "")
            trace["whatsapp_token_preview"] = token[:15] + "..." if token else "MISSING"
            trace["phone_number_id"] = pid

            import requests as rq
            url = f"https://graph.facebook.com/v22.0/{pid}/messages"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {
                "messaging_product": "whatsapp",
                "to": numero_usuario,
                "type": "text",
                "text": {"body": respuesta_ai}
            }
            resp = rq.post(url, json=payload, headers=headers, timeout=15)
            trace["whatsapp_status"] = resp.status_code
            trace["whatsapp_response"] = resp.json()
        except Exception as e:
            import traceback
            trace["whatsapp_error"] = str(e)
            trace["whatsapp_traceback"] = traceback.format_exc()

    except Exception as e:
        import traceback
        trace["fatal_error"] = str(e)
        trace["fatal_traceback"] = traceback.format_exc()

    return trace


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
            phone_number_id = value['metadata']['phone_number_id']

            # NOTE: Do NOT normalize Mexican numbers. Meta sends the wa_id in the
            # exact format needed to reply. Normalizing it breaks delivery.

            print(f"[Webhook] Msg from {numero_usuario}, phone_id={phone_number_id}: '{texto_usuario}'")

            client_data = database.get_client_by_phone_id(phone_number_id)
            print(f"[Webhook] Client lookup: {'FOUND' if client_data else 'NOT FOUND'}")

            if not client_data:
                return {"status": "unrecognized_client"}

            if gemini is None:
                print("[Webhook] Gemini not initialized")
                return {"status": "gemini_unavailable"}

            print(f"[Webhook] Calling Gemini for '{client_data['name']}'...")
            respuesta_ai = gemini.generar_respuesta(texto_usuario, client_data, numero_usuario)
            print(f"[Webhook] Gemini OK: '{respuesta_ai[:80] if respuesta_ai else None}'")

            print(f"[Webhook] Sending WhatsApp to {numero_usuario}...")
            success = whatsapp_service.enviar_mensaje_whatsapp(
                numero=numero_usuario,
                texto=respuesta_ai,
                whatsapp_token=client_data['whatsapp_token'],
                phone_number_id=client_data['phone_number_id']
            )
            print(f"[Webhook] Send result: {'OK' if success else 'FAILED'}")

    except Exception as e:
        import traceback
        print(f"[Webhook] Error: {e}\n{traceback.format_exc()}")

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
        msg = MIMEText(f"Tu codigo de acceso para Zotek Admin es: {code}\nExpira en 10 minutos.")
        msg['Subject'] = f"{code} es tu codigo de verificacion de Zotek"
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
        "WWW_DIR": WWW_DIR,
        "ADMIN_DIR": ADMIN_DIR,
        "index_exists": os.path.exists(os.path.join(WWW_DIR, "index.html")),
        "admin_index_exists": os.path.exists(os.path.join(ADMIN_DIR, "index.html")),
        "login_exists": os.path.exists(os.path.join(ADMIN_DIR, "login.html"))
    }


# === Auth API ===

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

    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}


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
async def update_client(client_id: int, request: Request, current_user: str = Depends(get_current_user)):
    data = await request.json()
    if database.update_client(client_id, data):
        return {"status": "updated"}
    raise HTTPException(status_code=400, detail="Error updating client")


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
    print(f"Mounting static files from {WWW_DIR}")
    app.mount("/", StaticFiles(directory=WWW_DIR, html=True), name="root")
else:
    print(f"Skipping static files mount (Directory not found: {WWW_DIR})")
