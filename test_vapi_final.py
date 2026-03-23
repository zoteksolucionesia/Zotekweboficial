import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración desde .env
API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
PHONE_ID = os.getenv("VAPI_PHONE_NUMBER_ID")

# NÚMERO DEL USUARIO
# Ajustado para México (Código +52)
TU_NUMERO = "+523123173431" 

print(f"🚀 Iniciando llamada de prueba a {TU_NUMERO}...")
print(f"🔹 Assistant ID: {ASSISTANT_ID}")
print(f"🔹 Phone ID: {PHONE_ID}")

url = "https://api.vapi.ai/call/phone"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "assistantId": ASSISTANT_ID,
    "phoneNumberId": PHONE_ID,
    "customer": {
        "number": TU_NUMERO,
        "name": "Morentinomar"
    },
    "assistantOverrides": {
        "variableValues": {
            "nombre_paciente": "Omar",
            "fecha_cita": "en 15 minutos",
            "nombre_profesional": "la Dra. Psicóloga",
            "nombre_consultorio": "Zotek Soluciones IA"
        }
    }
}

try:
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print("\n✅ ¡ÉXITO TOTAL!")
        print(f"📞 La llamada ha sido enviada al sistema de VAPI.")
        print(f"🆔 Call ID: {response.json().get('id')}")
        print("\n⏳ Deberías recibir la llamada en tu celular en los próximos segundos...")
    else:
        print(f"\n❌ ERROR de VAPI ({response.status_code})")
        print(f"Detalle: {response.text}")
except Exception as e:
    print(f"\n🔥 ERROR INESPERADO al ejecutar el script: {e}")
