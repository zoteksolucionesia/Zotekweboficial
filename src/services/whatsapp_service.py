import requests

def enviar_mensaje_whatsapp(numero, texto, whatsapp_token, phone_number_id):
    """Envía un mensaje de texto plano a través de la API de WhatsApp Cloud."""
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"✅ WHATSAPP [{numero}]: {texto[:50]}...")
            return True
        else:
            print(f"❌ ERROR WHATSAPP ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"🔥 EXCEPCIÓN WHATSAPP: {e}")
        return False
