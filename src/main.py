import os
import uvicorn
from fastapi import FastAPI, Request
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

app = FastAPI()

# Cache for WhatsApp retries
PROCESSED_MESSAGES = deque(maxlen=100)

# Lazy initialization using app events or on first request to ensure DB is ready
@app.on_event("startup")
async def startup_event():
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
            
    except Exception as e:
        print(f"🔥 Error en Webhook: {e}")

    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Note: When running as a package, use `python -m src.main` or `uvicorn src.main:app`
    uvicorn.run(app, host="0.0.0.0", port=port)
