"""
Services package for Zotek IA
"""

from .whatsapp_service import enviar_mensaje_whatsapp, enviar_menu_botones, enviar_menu_lista
from .email_service import EmailService, get_email_service_for_client
from .lead_service import LeadService, lead_service
from .appointment_service import AppointmentService, appointment_service

__all__ = [
    'enviar_mensaje_whatsapp',
    'enviar_menu_botones', 
    'enviar_menu_lista',
    'EmailService',
    'get_email_service_for_client',
    'LeadService',
    'lead_service',
    'AppointmentService',
    'appointment_service'
]
