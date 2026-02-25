import requests
import json

def enviar_mensaje_whatsapp(numero, texto, whatsapp_token, phone_number_id):
    """Envía un mensaje de texto plano a través de la API de WhatsApp Cloud."""
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    try:
        # Usamos json.dumps con ensure_ascii=False para enviar tildes reales y no códigos \u00xx
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            print(f"✅ WHATSAPP [{numero}]: {texto[:50]}...")
            return True
        else:
            print(f"❌ ERROR WHATSAPP ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"🔥 EXCEPCIÓN WHATSAPP: {e}")
        return False

def enviar_menu_botones(numero, texto, opciones, whatsapp_token, phone_number_id):
    """Envía un mensaje con hasta 3 botones de respuesta rápida."""
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    buttons = []
    for i, opcion in enumerate(opciones[:3]):
        buttons.append({
            "type": "reply",
            "reply": {
                "id": f"btn_{i}",
                "title": opcion[:20] # El título tiene un límite de 20 caracteres
            }
        })

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": texto},
            "action": {"buttons": buttons}
        }
    }
    
    try:
        # Usamos json.dumps con ensure_ascii=False para enviar tildes reales y no códigos \u00xx
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"🔥 ERROR ENVIANDO BOTONES: {e}")
        return False

def enviar_menu_lista(numero, texto, titulo_boton, titulo_seccion, opciones, whatsapp_token, phone_number_id):
    """Envía un mensaje con un menú de lista desplegable (hasta 10 opciones)."""
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    rows = []
    for i, opcion in enumerate(opciones[:10]):
        rows.append({
            "id": f"list_{i}",
            "title": opcion[:24], # El título tiene un límite de 24 caracteres
            "description": "" # Opcional
        })

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": texto},
            "action": {
                "button": titulo_boton[:20],
                "sections": [
                    {
                        "title": titulo_seccion[:24],
                        "rows": rows
                    }
                ]
            }
        }
    }

    try:
        # Usamos json.dumps con ensure_ascii=False para enviar tildes reales y no códigos \u00xx
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"🔥 ERROR ENVIANDO LISTA: {e}")
        return False
