"""
Twilio Service — Llamadas de voz inmediatas y recordatorios.
Reemplaza VAPI para llamadas outbound.
"""
import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Número Twilio con formato +52...


def _get_client():
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError("TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN deben estar en .env")
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def llamar_inmediatamente(numero_destino: str, mensaje_voz: str, url_webhook: str = None) -> dict:
    """
    Inicia una llamada de voz inmediata al usuario.

    Args:
        numero_destino: Número con código de país, ej. +5215512345678
        mensaje_voz:    Texto que el bot leerá al contestar (TwiML Say)
        url_webhook:    URL TwiML externa (opcional). Si se omite, usa mensaje_voz con TwiML inline.

    Returns:
        {"success": bool, "call_sid": str, "status": str, "error": str}
    """
    try:
        client = _get_client()

        if not TWILIO_PHONE_NUMBER:
            raise ValueError("TWILIO_PHONE_NUMBER no definido en .env")

        # TwiML inline: saluda y cuelga. Se puede reemplazar por url_webhook con lógica compleja.
        twiml = (
            f"<Response>"
            f"<Say language='es-MX' voice='Polly.Mia'>{mensaje_voz}</Say>"
            f"<Pause length='1'/>"
            f"</Response>"
        )

        params = {
            "to": numero_destino,
            "from_": TWILIO_PHONE_NUMBER,
        }
        if url_webhook:
            params["url"] = url_webhook
        else:
            params["twiml"] = twiml

        call = client.calls.create(**params)
        logger.info(f"Llamada Twilio iniciada → {numero_destino} | SID: {call.sid}")
        return {"success": True, "call_sid": call.sid, "status": call.status}

    except TwilioRestException as e:
        logger.error(f"Twilio error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error en llamar_inmediatamente: {e}")
        return {"success": False, "error": str(e)}


def llamar_recordatorio(numero_destino: str, paciente_nombre: str, fecha_hora: str, profesional: str) -> dict:
    """
    Llamada de recordatorio de cita 24h antes (reemplaza VAPI).
    """
    mensaje = (
        f"Hola {paciente_nombre}, te recordamos que tienes una cita con {profesional} "
        f"el {fecha_hora}. Si necesitas cancelar o reprogramar, por favor contáctanos. "
        f"Hasta luego."
    )
    return llamar_inmediatamente(numero_destino, mensaje)
