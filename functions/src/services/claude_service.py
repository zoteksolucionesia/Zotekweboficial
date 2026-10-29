import anthropic
import os
import traceback
from typing import Dict, Any
from .. import database

MODEL_ID = "claude-haiku-5-5"


def _schema(s: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte un esquema estilo Gemini ("OBJECT", "STRING"...) a JSON Schema (minúsculas)."""
    out = {k: v for k, v in s.items() if k not in ("type", "properties", "items")}
    if "type" in s:
        out["type"] = s["type"].lower()
    if "properties" in s:
        out["properties"] = {k: _schema(v) for k, v in s["properties"].items()}
    if "items" in s:
        out["items"] = _schema(s["items"])
    return out


# Herramientas disponibles para el agente (mismas que tenía el motor de Gemini)
_DECLARACIONES = [
    {
        "name": "activar_demo",
        "description": "Cambia el modo del bot a una demostración específica.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tipo": {
                    "type": "STRING",
                    "enum": ["restaurante", "clinica", "tienda", "dental", "psicologo", "salon"],
                    "description": "El tipo de negocio para la demo."
                }
            },
            "required": ["tipo"]
        }
    },
    {
        "name": "enviar_menu_interactivo",
        "description": "Envía un menú con botones o una lista de opciones al usuario por WhatsApp.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "mensaje": {"type": "STRING", "description": "Texto descriptivo sobre qué elegir."},
                "opciones": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Lista de opciones cortas (máximo 10)."
                }
            },
            "required": ["mensaje", "opciones"]
        }
    },
    {
        "name": "ejecutar_automatizacion_n8n",
        "description": "Dispara un flujo de trabajo complejo en n8n (ej. registrar en CRM, enviar correos, generar facturas).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "workflow_id": {"type": "STRING", "description": "Identificador opcional del flujo."},
                "datos": {
                    "type": "OBJECT",
                    "description": "Objeto JSON con toda la información necesaria para el flujo (nombre, tel, pedido, etc.)."
                }
            },
            "required": ["datos"]
        }
    },
    {
        "name": "capturar_lead",
        "description": "Registra el interés de un cliente para contacto humano.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "nombre": {"type": "STRING", "description": "Nombre del cliente."},
                "interes": {"type": "STRING", "description": "Resumen de lo que busca el cliente."}
            },
            "required": ["interes"]
        }
    },
    {
        "name": "finalizar_demo",
        "description": "Termina la sesión de demostración actual.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "registrar_cita",
        "description": "Registra una cita formal en la base de datos.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "nombre_cliente": {"type": "STRING", "description": "Nombre completo del cliente."},
                "telefono_contacto": {"type": "STRING", "description": "Número de teléfono de contacto."},
                "email_cliente": {"type": "STRING", "description": "Correo electrónico del cliente."},
                "fecha_cita": {"type": "STRING", "description": "Fecha de la cita (formato YYYY-MM-DD)."},
                "hora_cita": {"type": "STRING", "description": "Hora de la cita (formato HH:MM)."}
            },
            "required": ["nombre_cliente", "telefono_contacto", "email_cliente", "fecha_cita", "hora_cita"]
        }
    },
    {
        "name": "consultar_disponibilidad",
        "description": "Verifica los horarios y fechas disponibles para citas.",
        "parameters": {"type": "OBJECT", "properties": {}}
    }
]

TOOLS = [
    {"name": d["name"], "description": d["description"], "input_schema": _schema(d["parameters"])}
    for d in _DECLARACIONES
]


class ClaudeEngine:
    """Motor de IA (Claude Haiku 5.5) que actúa como un Agente Autónomo con Tool Use."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        # Timeout corto: Meta reintenta el webhook si tardamos demasiado en responder
        self.client = anthropic.Anthropic(api_key=self.api_key, timeout=25.0, max_retries=1)
        self.model_id = MODEL_ID
        self.tools = TOOLS

    def generar_respuesta_agente(
        self,
        mensaje_usuario: str,
        client_data: Dict[str, Any],
        numero_telefono: str
    ) -> Dict[str, Any]:
        """
        Genera una respuesta inteligente que puede incluir llamadas a funciones (Agentic Flow).
        Devuelve {"text": str, "tool_calls": [{"name": str, "args": dict}]}; main.py ejecuta las herramientas.
        """
        client_id = str(client_data['id'])
        nombre_bot = client_data.get('name', 'Asistente Zotek')

        # 1. Obtener conocimiento dinámico y horarios
        conocimiento = database.get_client_knowledge(client_id)
        horarios = database.get_client_schedules(client_id)

        # 1.5 Obtener citas ya agendadas para bloquearlas
        from .appointment_service import appointment_service
        from datetime import datetime as _dt
        booked = appointment_service.get_pending_appointments(client_id)
        booked_str = "--- CITAS YA RESERVADAS (NO DISPONIBLES) ---\n"
        if booked:
            for b in booked:
                dt = b['date_time']
                if not hasattr(dt, 'strftime'):
                    dt = _dt.fromisoformat(str(dt))
                booked_str += f"- {dt.strftime('%Y-%m-%d %H:%M')}\n"
        else:
            booked_str += "No hay citas reservadas aún.\n"

        if isinstance(conocimiento, list):
            conocimiento = "\n\n".join([k.get('content', '') for k in conocimiento])

        # Formatear horarios para el prompt
        if horarios:
            horarios_str = "--- HORARIOS DE ATENCIÓN DISPONIBLES ---\n"
            for h in horarios:
                horarios_str += f"- {h['schedule_date']}: {h['start_time']} a {h['end_time']}\n"
        else:
            horarios_str = "--- HORARIOS DE ATENCIÓN ---\nNo hay horarios configurados en el sistema por ahora. Informa al usuario que por el momento no es posible agendar citas y pide que contacte más tarde o deje sus datos."

        instrucciones_base = client_data.get('system_instruction') or \
            f"Eres el agente inteligente de {nombre_bot}. Ayuda al usuario usando tus herramientas."

        is_demo = str(client_id).startswith('demo_')

        if is_demo:
            # Demos: prompt limpio sin reglas de agente ni tools de Zotek
            prompt_sistema = instrucciones_base
            tools = []
        else:
            duracion = database.get_client_session_duration(client_id)
            prompt_sistema = f"""
        {instrucciones_base}

        {horarios_str}

        {booked_str}

        --- CONOCIMIENTO DISPONIBLE ---
        {conocimiento if conocimiento else "No hay archivos PDF cargados."}

        --- TUS REGLAS DE AGENTE ---
        1. Eres un AGENTE, no solo un chatbot. Tienes permiso para usar herramientas.
        2. Si el usuario pide probar una demo, USA 'activar_demo'.
        3. Si quieres presentar opciones claras, USA 'enviar_menu_interactivo'.
        4. Si el usuario quiere una automatización avanzada (ej. 'regístrame', 'mándame un email con la info', 'crea un ticket'), USA 'ejecutar_automatizacion_n8n'.
        5. Sé proactivo. Si detectas interés comercial, USA 'capturar_lead'.
        6. Para agendar una cita formal, usa 'registrar_cita' SOLAMENTE después de confirmar disponibilidad con el usuario según los horarios ARRIBA mencionados (restando las reservadas).
        7. El usuario determina la duración de la cita, pero por defecto una sesión dura {duracion} minutos. Confirma siempre la duración con el usuario.
        8. DEBES solicitar obligatoriamente: Nombre completo, Teléfono y Email antes de finalizar el registro de la cita.
        9. Si te preguntan por horarios, diles los que tienes listados arriba de forma clara. (Nota: Solo se te muestran fechas de hoy en adelante).
        10. Si usas una herramienta, el sistema la ejecutará por ti.
        """
            tools = self.tools

        params = {
            "model": self.model_id,
            "max_tokens": 4096,
            "system": prompt_sistema,
            # Chat de WhatsApp: respuestas rápidas y breves
            "output_config": {"effort": "low"},
            "messages": [{"role": "user", "content": mensaje_usuario}],
        }
        if tools:
            params["tools"] = tools

        try:
            response = self.client.messages.create(**params)

            if response.stop_reason == "refusal":
                print(f"CLAUDE REFUSAL: {response.stop_details}")
                return {"text": "Lo siento, no puedo ayudarte con esa solicitud.", "tool_calls": []}

            # La respuesta puede empezar con bloques de razonamiento: leer por tipo, no por posición
            res_text = "\n".join(b.text for b in response.content if b.type == "text").strip()
            tool_calls = [
                {"name": b.name, "args": b.input}
                for b in response.content if b.type == "tool_use"
            ]

            if not res_text and tool_calls:
                res_text = "Procesando acción solicitada..."

            return {
                "text": res_text,
                "tool_calls": tool_calls
            }

        except anthropic.RateLimitError as e:
            print(f"CLAUDE RATE LIMIT: {e}")
            return {"text": "El asistente está temporalmente saturado. Intenta de nuevo en unos segundos.", "tool_calls": []}
        except anthropic.APIStatusError as e:
            # Saldo agotado llega como 400 "credit balance is too low": revisar Billing en platform.claude.com
            print(f"ERROR CLAUDE API ({e.status_code}): {e.message}")
            return {"text": "Lo siento, tuve un problema procesando tu solicitud.", "tool_calls": []}
        except anthropic.APIConnectionError as e:
            print(f"ERROR CLAUDE CONEXIÓN: {e}")
            return {"text": "Lo siento, tuve un problema procesando tu solicitud.", "tool_calls": []}
        except Exception as e:
            print(f"ERROR CLAUDE AGENT: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            return {"text": "Lo siento, tuve un problema procesando tu solicitud.", "tool_calls": []}

    def generar_respuesta(self, mensaje_usuario, client_data, numero_telefono):
        """Mantiene compatibilidad con el flujo legacy."""
        res = self.generar_respuesta_agente(mensaje_usuario, client_data, numero_telefono)
        return res['text']
