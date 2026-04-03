import json
from typing import Dict, Any, List

def get_demo_switch_tool():
    """Returns the tool definition for switching between demos."""
    return {
        "name": "switch_to_demo",
        "description": "Cambia la personalidad y el menú del bot a un demo específico.",
        "parameters": {
            "type": "object",
            "properties": {
                "demo_type": {
                    "type": "string",
                    "enum": ["restaurante", "clinica", "tienda", "dental", "psicologo", "salon"],
                    "description": "El tipo de demo a activar."
                }
            },
            "required": ["demo_type"]
        }
    }

def get_whatsapp_menu_tool():
    """Returns the tool definition for sending a WhatsApp menu."""
    return {
        "name": "send_whatsapp_menu",
        "description": "Envía un menú interactivo (botones o lista) al usuario por WhatsApp.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "El texto explicativo del menú."
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Las opciones que aparecerán como botones (máximo 3) o lista (máximo 10)."
                }
            },
            "required": ["text", "options"]
        }
    }

def get_lead_registration_tool():
    """Returns the tool definition for registering a lead."""
    return {
        "name": "register_lead",
        "description": "Registra el interés de un cliente para contacto humano.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre del interesado."},
                "interest": {"type": "string", "description": "Resumen de lo que le interesa (planes, servicios específicos)."}
            },
            "required": ["interest"]
        }
    }


def get_appointment_tool():
    """
    Returns the tool definition for registering a patient appointment.
    When the bot registers an appointment, the premium reminder system
    will automatically call the patient 24 hours before via VAPI.
    """
    return {
        "name": "registrar_cita",
        "description": (
            "Registra una nueva cita o reserva del paciente/cliente en el sistema. "
            "Si el profesional tiene plan Pro o Enterprise, el sistema llamará automáticamente "
            "al paciente 24 horas antes para recordarle la cita."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "paciente_nombre": {
                    "type": "string",
                    "description": "Nombre completo del paciente o cliente."
                },
                "cliente_telefono": {
                    "type": "string",
                    "description": "Número de teléfono del paciente con código de país, ej. 5215512345678."
                },
                "fecha_hora": {
                    "type": "string",
                    "description": "Fecha y hora de la cita en formato YYYY-MM-DD HH:MM, ej. 2026-03-25 15:00."
                },
                "paciente_email": {
                    "type": "string",
                    "description": "Correo electrónico del paciente para enviarle la confirmación de su cita (opcional)."
                },
                "motivo": {
                    "type": "string",
                    "description": "Motivo o descripción breve de la cita (opcional)."
                }
            },
            "required": ["paciente_nombre", "cliente_telefono", "fecha_hora"]
        }
    }

