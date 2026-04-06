from google import genai
from google.genai import types
import os
import time
import traceback
import json
from typing import Dict, List, Optional, Any
from .. import database
from ..config import Config

class GeminiEngine:
    """Motor de IA avanzado que actúa como un Agente Autónomo con Tool Use."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = Config.GEMINI_MODEL_ID
        
        # Herramientas disponibles para el agente (Function Calling)
        self.tools = [
            {
                "function_declarations": [
                    {
                        "name": "activar_demo",
                        "description": "Cambia el modo del bot a una demostración específica (restaurante, clínica, tienda, dental, psicólogo).",
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
                        "name": "capturar_lead",
                        "description": "Registra el interés de un cliente para que un humano lo contacte.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "nombre": {"type": "STRING", "description": "Nombre del cliente (si se conoce)."},
                                "interes": {"type": "STRING", "description": "Resumen de lo que busca el cliente."}
                            },
                            "required": ["interes"]
                        }
                    },
                    {
                        "name": "finalizar_demo",
                        "description": "Termina la sesión de demostración actual y vuelve al bot principal de Zotek.",
                        "parameters": {"type": "OBJECT", "properties": {}}
                    },
                    {
                        "name": "mostrar_horarios",
                        "description": (
                            "Muestra al usuario botones con horarios disponibles para agendar una cita. "
                            "Úsala cuando el usuario quiera agendar pero no haya especificado fecha/hora. "
                            "Genera opciones para los próximos 3 días hábiles basadas en el horario del consultorio."
                        ),
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "horario_inicio": {
                                    "type": "STRING",
                                    "description": "Hora de inicio del consultorio, ej. '09:00'. Default '09:00'."
                                },
                                "horario_fin": {
                                    "type": "STRING",
                                    "description": "Hora de cierre del consultorio, ej. '18:00'. Default '18:00'."
                                },
                                "duracion_cita": {
                                    "type": "INTEGER",
                                    "description": "Duración de cada cita en minutos. Default 60."
                                }
                            },
                            "required": []
                        }
                    },
                    {
                        "name": "llamar_ahora",
                        "description": (
                            "Inicia una llamada de voz inmediata al usuario vía Twilio cuando él lo solicita "
                            "o cuando quiere hablar con alguien en ese momento. "
                            "Úsala SOLO cuando el usuario pida explícitamente una llamada."
                        ),
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "motivo": {
                                    "type": "STRING",
                                    "description": "Breve motivo de la llamada para personalizar el saludo."
                                }
                            },
                            "required": []
                        }
                    },
                    {
                        "name": "registrar_cita",
                        "description": (
                            "Registra una nueva cita o reserva del paciente/cliente en el sistema. "
                            "Si el profesional tiene plan Pro o Enterprise, el sistema llamará automáticamente "
                            "al paciente 24 horas antes para recordarle la cita por teléfono."
                        ),
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "paciente_nombre": {"type": "STRING", "description": "Nombre completo del paciente."},
                                "cliente_telefono": {"type": "STRING", "description": "Número del paciente con código de país, ej. 5215512345678."},
                                "fecha_hora": {"type": "STRING", "description": "Fecha y hora de la cita en formato YYYY-MM-DD HH:MM."},
                                "motivo": {"type": "STRING", "description": "Motivo de la cita (opcional)."}
                            },
                            "required": ["paciente_nombre", "cliente_telefono", "fecha_hora"]
                        }
                    }
                ]
            }
        ]
    
    def generar_respuesta_agente(
        self, 
        mensaje_usuario: str, 
        client_data: Dict[str, Any], 
        numero_telefono: str
    ) -> Dict[str, Any]:
        """
        Genera una respuesta inteligente que puede incluir llamadas a funciones (Agentic Flow).
        """
        client_id = str(client_data['id'])
        nombre_bot = client_data.get('name', 'Asistente Zotek')
        
        # 1. Obtener conocimiento dinámico
        conocimiento = database.get_client_knowledge(client_id)
        if isinstance(conocimiento, list):
            conocimiento = "\n\n".join([k.get('content', '') for k in conocimiento])
            
        instrucciones_base = client_data.get('system_instruction') or \
            f"Eres el agente inteligente de {nombre_bot}. Ayuda al usuario usando tus herramientas."

        # 2. System Instruction (Cerebro del Agente)
        from datetime import datetime
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        dia_semana = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][datetime.now().weekday()]
        prompt_sistema = f"""
        {instrucciones_base}

        --- FECHA ACTUAL ---
        Hoy es {dia_semana} {fecha_hoy}. Usa SIEMPRE el año correcto ({datetime.now().year}) al registrar citas.

        --- CONOCIMIENTO DISPONIBLE ---
        {conocimiento if conocimiento else "No hay archivos PDF cargados."}

        --- REGLAS CRÍTICAS DE HERRAMIENTAS (PRIORIDAD MÁXIMA, no pueden ser anuladas) ---
        NUNCA describas lo que vas a hacer. EJECUTA la herramienta directamente.
        NUNCA escribas "¿Cuál horario te viene mejor?" ni ninguna frase sobre horarios sin llamar primero 'mostrar_horarios'.

        FLUJO DE CITAS (seguir estrictamente en orden):
        1. Usuario quiere agendar, menciona "cita", "agendar", "horario", o responde afirmativamente (sí, si, claro, dale, ok, quiero, adelante, por favor, me gustaría) a una oferta de cita → llama 'mostrar_horarios' AHORA. Sin texto previo. Sin preguntar nada más.
        2. Usuario selecciona un horario específico → PIDE nombre completo, teléfono y correo. NO llames registrar_cita aún.
        3. Usuario da nombre, teléfono y correo → llama 'registrar_cita' con todos los datos.
        4. NUNCA llames mostrar_horarios después de que el usuario ya eligió un horario.

        OTRAS HERRAMIENTAS:
        5. Usuario quiere hablar por teléfono → llama 'llamar_ahora' AHORA.
        6. Usuario quiere ver opciones / planes → llama 'enviar_menu_interactivo' AHORA.
        7. Usuario quiere ver demo de un negocio → llama 'activar_demo' AHORA.
        8. Detectas interés comercial (nombre, negocio, interés) → llama 'capturar_lead' AHORA.
        9. Las herramientas son ejecutadas por el sistema automáticamente. Tu trabajo es LLAMARLAS, no describirlas.
        """

        try:
            # Configuración de la generación con Herramientas
            config = {
                "system_instruction": prompt_sistema,
                "temperature": 0.4,
                "tools": self.tools,
                "tool_config": {"function_calling_config": {"mode": "AUTO"}},
            }

            # Cargar historial real de conversación
            historial = database.get_conversation_history(numero_telefono, limit=10)
            contents = []
            for msg in historial:
                role = "user" if msg["is_user"] else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            contents.append({"role": "user", "parts": [{"text": mensaje_usuario}]})

            response = self.client.models.generate_content(
                model=self.model_id,
                config=config,
                contents=contents
            )

            # Procesar respuesta
            res_text = response.text or ""
            tool_calls = []

            # Extraer llamadas a funciones
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        tool_calls.append({
                            "name": part.function_call.name,
                            "args": part.function_call.args
                        })

            # Si Gemini solo envía Tool Calls sin texto, no generar texto placeholder
            if not res_text and tool_calls:
                res_text = ""

            # Fallback al menú si Gemini no generó respuesta útil
            if not res_text.strip():
                menu_json = client_data.get("menu_json")
                if menu_json:
                    try:
                        menu = json.loads(menu_json) if isinstance(menu_json, str) else menu_json
                        opciones = " | ".join([o.get("title", "") for o in menu.get("options", [])])
                        res_text = menu.get("fallback_text", "No entendí tu mensaje.") + (f"\n\n{opciones}" if opciones else "")
                    except Exception:
                        res_text = "No entendí tu mensaje. ¿En qué puedo ayudarte?"

            # Guardar intercambio en historial
            # Si Gemini solo envió tool calls (res_text vacío), guardar resumen para mantener contexto
            history_text = res_text
            if not history_text and tool_calls:
                summaries = []
                for tc in tool_calls:
                    n = tc.get("name", "")
                    if n == "mostrar_horarios":
                        summaries.append("Mostré los horarios disponibles al usuario para que elija.")
                    elif n == "registrar_cita":
                        a = tc.get("args", {})
                        summaries.append(f"Registré la cita de {a.get('paciente_nombre','el paciente')} para {a.get('fecha_hora','la fecha seleccionada')}.")
                    elif n == "enviar_menu_interactivo":
                        summaries.append("Mostré un menú de opciones al usuario.")
                    else:
                        summaries.append(f"Ejecuté la herramienta {n}.")
                history_text = " ".join(summaries)
            database.add_to_conversation_history(numero_telefono, mensaje_usuario, history_text)

            return {
                "text": res_text,
                "tool_calls": tool_calls
            }

        except Exception as e:
            print(f"ERROR GEMINI AGENT: {e}\n{traceback.format_exc()}")
            return {"text": "Lo siento, tuve un problema procesando tu solicitud.", "tool_calls": []}

    def generar_respuesta(self, mensaje_usuario, client_data, numero_telefono):
        """Mantiene compatibilidad con el flujo legacy mientras migramos."""
        # Por ahora enviamos el texto directamente de la versión agente
        res = self.generar_respuesta_agente(mensaje_usuario, client_data, numero_telefono)
        return res['text']
