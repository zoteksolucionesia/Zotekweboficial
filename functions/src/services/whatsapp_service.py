import requests


def _post_whatsapp(payload: dict, whatsapp_token: str, phone_number_id: str) -> bool:
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {whatsapp_token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            return True
        print(f"❌ ERROR WHATSAPP ({r.status_code}): {r.text}")
        return False
    except Exception as e:
        print(f"🔥 EXCEPCIÓN WHATSAPP: {e}")
        return False


def enviar_mensaje_whatsapp(numero, texto, whatsapp_token, phone_number_id):
    """Envía un mensaje de texto plano a través de la API de WhatsApp Cloud."""
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    result = _post_whatsapp(payload, whatsapp_token, phone_number_id)
    if result:
        print(f"✅ WHATSAPP [{numero}]: {texto[:50]}...")
    return result


def enviar_botones(numero: str, texto: str, botones: list, whatsapp_token: str, phone_number_id: str) -> bool:
    """
    Envía un mensaje con hasta 3 botones interactivos.
    botones: lista de strings, ej. ["Lunes 10am", "Martes 3pm", "Miércoles 7pm"]
    """
    btns = [
        {"type": "reply", "reply": {"id": f"btn_{i}", "title": b[:20]}}
        for i, b in enumerate(botones[:3])
    ]
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": texto[:1024]},
            "action": {"buttons": btns}
        }
    }
    return _post_whatsapp(payload, whatsapp_token, phone_number_id)


def enviar_lista(numero: str, texto: str, opciones: list, titulo_boton: str, whatsapp_token: str, phone_number_id: str) -> bool:
    """
    Envía un menú de lista. Si hay más de 5 opciones las divide en 2 secciones
    para que WhatsApp muestre scroll nativo y todos los horarios sean accesibles.
    """
    if len(opciones) <= 5:
        sections = [{"title": "Horarios disponibles", "rows": [
            {"id": f"opt_{i}", "title": o[:24]} for i, o in enumerate(opciones)
        ]}]
    else:
        primera = opciones[:5]
        segunda = opciones[5:10]
        sections = [
            {"title": "Próximos horarios", "rows": [
                {"id": f"opt_{i}", "title": o[:24]} for i, o in enumerate(primera)
            ]},
            {"title": "Más opciones", "rows": [
                {"id": f"opt_{i+5}", "title": o[:24]} for i, o in enumerate(segunda)
            ]},
        ]
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": texto[:1024]},
            "action": {
                "button": titulo_boton[:20],
                "sections": sections
            }
        }
    }
    return _post_whatsapp(payload, whatsapp_token, phone_number_id)


def enviar_menu_interactivo(numero: str, texto: str, opciones: list, whatsapp_token: str, phone_number_id: str) -> bool:
    """Elige automáticamente botones (≤3) o lista (>3 opciones)."""
    if len(opciones) <= 3:
        return enviar_botones(numero, texto, opciones, whatsapp_token, phone_number_id)
    return enviar_lista(numero, texto, opciones, "Ver opciones", whatsapp_token, phone_number_id)
