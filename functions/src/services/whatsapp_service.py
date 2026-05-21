import requests
import json
import sys
from datetime import datetime

def enviar_mensaje_whatsapp(numero, texto, whatsapp_token, phone_number_id):
    """Envía un mensaje de texto plano a través de la API de WhatsApp Cloud."""
    if not whatsapp_token or not phone_number_id:
        print(f"❌ ERROR: WhatsApp token o phone_number_id faltantes"); sys.stdout.flush()
        return False
    
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
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            print(f"✅ WHATSAPP [{numero}]: {texto[:50]}..."); sys.stdout.flush()
            return True
        else:
            print(f"❌ ERROR WHATSAPP ({response.status_code}): {response.text}"); sys.stdout.flush()
            return False
    except Exception as e:
        print(f"🔥 EXCEPCIÓN WHATSAPP: {e}"); sys.stdout.flush()
        return False


def enviar_menu_botones(numero, texto, opciones, whatsapp_token, phone_number_id):
    """Envía un mensaje con hasta 3 botones de respuesta rápida."""
    if not whatsapp_token or not phone_number_id:
        print(f"❌ ERROR: WhatsApp token o phone_number_id faltantes"); sys.stdout.flush()
        return False
    
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
                "title": opcion[:20]
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
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code != 200:
            print(f"❌ ERROR WHATSAPP LISTA/BOTONES ({response.status_code}): {response.text}"); sys.stdout.flush()
        return response.status_code == 200
    except Exception as e:
        print(f"🔥 ERROR ENVIANDO BOTONES/LISTA: {e}"); sys.stdout.flush()
        return False


def enviar_menu_lista(numero, texto, titulo_boton, titulo_seccion, opciones, whatsapp_token, phone_number_id):
    """Envía un mensaje con un menú de lista desplegable (hasta 10 opciones)."""
    if not whatsapp_token or not phone_number_id:
        print(f"❌ ERROR: WhatsApp token o phone_number_id faltantes"); sys.stdout.flush()
        return False
    
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    rows = []
    for i, opcion in enumerate(opciones[:10]):
        rows.append({
            "id": f"list_{i}",
            "title": opcion[:24],
            "description": ""
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
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=payload)

        return response.status_code == 200
    except Exception as e:
        print(f"🔥 ERROR ENVIANDO LISTA: {e}")
        return False


def enviar_template_whatsapp(phone_number_id, whatsapp_token, to_phone, template_name, variables, language="es_MX"):
    """Envía una plantilla HSM aprobada por Meta (mensajes proactivos fuera de ventana 24h)."""
    if not whatsapp_token or not phone_number_id:
        print(f"❌ ERROR: WhatsApp token o phone_number_id faltantes"); sys.stdout.flush()
        return False

    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": str(v)} for v in variables]
            }]
        }
    }
    try:
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            print(f"✅ WA TEMPLATE [{to_phone}]: {template_name}"); sys.stdout.flush()
            return True
        else:
            print(f"❌ ERROR WA TEMPLATE ({response.status_code}): {response.text}"); sys.stdout.flush()
            return False
    except Exception as e:
        print(f"🔥 EXCEPCIÓN WA TEMPLATE: {e}"); sys.stdout.flush()
        return False
