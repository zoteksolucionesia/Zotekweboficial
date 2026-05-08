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
        prompt_sistema = f"""
        {instrucciones_base}

        --- CONOCIMIENTO DISPONIBLE ---
        {conocimiento if conocimiento else "No hay archivos PDF cargados."}

        --- TUS REGLAS DE AGENTE ---
        1. Eres un AGENTE, no solo un chatbot. Tienes permiso para usar herramientas.
        2. Si el usuario pide probar una demo, USA 'activar_demo'.
        3. Si quieres salir de la demo, USA 'finalizar_demo'.
        4. Si quieres presentar opciones claras para que el usuario NO tenga que escribir, USA 'enviar_menu_interactivo'.
        5. Sé proactivo. Si detectas interés comercial, USA 'capturar_lead'.
        6. Si un paciente quiere agendar, confirmar o registrar una CITA, usa 'registrar_cita' con sus datos. Pídele su nombre, teléfono y fecha/hora antes de llamarla.
        7. Si usas una herramienta, el sistema la ejecutará por ti.
        """

        try:
            # Configuración de la generación con Herramientas
            config = {
                "system_instruction": prompt_sistema,
                "temperature": 0.4,
                "tools": self.tools
            }
            
            # TODO: Incorporar historial real desde database.get_conversation_history
            contents = [mensaje_usuario]
            
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
            
            # Fallback de texto si Gemini solo envía Tool Calls
            if not res_text and tool_calls:
                res_text = "[Procesando acción...]"
                
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
