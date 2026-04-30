from google import genai
from google.genai import types
import os
import time
import traceback
import json
from typing import Dict, List, Optional, Any
from .. import database

class GeminiEngine:
    """Motor de IA avanzado que actúa como un Agente Autónomo con Tool Use."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash"
        
        # Herramientas disponibles para el agente (Function Calling)
        self.tools = [
            {
                "function_declarations": [
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
        
        # 1. Obtener conocimiento dinámico y horarios
        conocimiento = database.get_client_knowledge(client_id)
        horarios = database.get_client_schedules(client_id)
        
        # 1.5 Obtener citas ya agendadas para bloquearlas
        from .appointment_service import appointment_service
        booked = appointment_service.get_pending_appointments(client_id)
        booked_str = "--- CITAS YA RESERVADAS (NO DISPONIBLES) ---\n"
        if booked:
            for b in booked:
                booked_str += f"- {b['date_time'].strftime('%Y-%m-%d %H:%M')}\n"
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

        duracion = database.get_client_session_duration(client_id)

        # 2. System Instruction (Cerebro del Agente)
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

        try:
            config = {
                "system_instruction": prompt_sistema,
                "temperature": 0.4,
                "tools": self.tools
            }
            
            contents = [mensaje_usuario]
            
            response = self.client.models.generate_content(
                model=self.model_id,
                config=config,
                contents=contents
            )
            
            try:
                res_text = response.text
            except ValueError:
                res_text = ""
                
            tool_calls = []
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        tool_calls.append({
                            "name": part.function_call.name,
                            "args": part.function_call.args
                        })
            
            if not res_text and tool_calls:
                res_text = "Procesando acción solicitada..."
                
            return {
                "text": res_text,
                "tool_calls": tool_calls
            }

        except Exception as e:
            print(f"ERROR GEMINI AGENT: {e}\n{traceback.format_exc()}")
            return {"text": "Lo siento, tuve un problema procesando tu solicitud.", "tool_calls": []}

    def generar_respuesta(self, mensaje_usuario, client_data, numero_telefono):
        """Mantiene compatibilidad con el flujo legacy."""
        res = self.generar_respuesta_agente(mensaje_usuario, client_data, numero_telefono)
        return res['text']
        res = self.generar_respuesta_agente(mensaje_usuario, client_data, numero_telefono)
        return res['text']
