"""
Email Service for Zotek IA
Envía emails usando configuración SMTP de cada cliente
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import sys


class EmailService:
    """Servicio de emails para envío de notificaciones y follow-ups"""
    
    def __init__(self, smtp_server: str, smtp_port: int, email_user: str, 
                 email_password: str, email_from_name: str = ''):
        """
        Inicializa el servicio de email
        
        Args:
            smtp_server: Servidor SMTP (ej: smtp.gmail.com)
            smtp_port: Puerto SMTP (587 para TLS, 465 para SSL)
            email_user: Email de la cuenta
            email_password: Contraseña de aplicación
            email_from_name: Nombre que aparece como remitente
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_user = email_user
        self.email_password = email_password
        self.email_from_name = email_from_name or email_user
        
    def send_email(self, to: str, subject: str, body: str, 
                   html: bool = False) -> bool:
        """
        Envía un email
        
        Args:
            to: Email del destinatario
            subject: Asunto del email
            body: Cuerpo del email
            html: Si True, el cuerpo es HTML
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.email_from_name} <{self.email_user}>"
            msg['To'] = to
            
            # Adjuntar cuerpo
            mime_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, mime_type, 'utf-8'))
            
            # Conectar y enviar
            if self.smtp_port == 465:
                # SSL
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                # TLS
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, [to], msg.as_string())
            server.quit()
            
            print(f"[Email] Sent to {to}: {subject}")
            return True
            
        except Exception as e:
            print(f"[Email] Error sending to {to}: {e}")
            return False
    
    def send_template(self, to: str, template: str, 
                      variables: Dict[str, str]) -> bool:
        """
        Envía un email usando una plantilla
        
        Args:
            to: Email del destinatario
            template: Plantilla predefinida (followup_24h, appointment_reminder, etc.)
            variables: Diccionario de variables para reemplazar en la plantilla
            
        Returns:
            True si se envió correctamente
        """
        # Plantillas hardcodeadas por defecto
        templates = {
            'followup_24h': {
                'subject': '¡Hola! ¿Te quedaste con dudas?',
                'body': '''Hola {nombre},

Vimos que nos escribiste ayer pero no pudimos continuar la conversación.

¿Te gustaría que te ayudemos con algo?

{nombre_negocio}
'''
            },
            'appointment_reminder': {
                'subject': 'Recordatorio de tu cita mañana',
                'body': '''Hola {nombre},

Te recordamos que tienes una cita agendada para mañana a las {hora}.

¿Confirmas tu asistencia?

{nombre_negocio}
'''
            },
            'appointment_confirmed': {
                'subject': '¡Tu cita está confirmada!',
                'body': '''Hola {nombre},

Tu cita ha sido confirmada exitosamente.

📅 Fecha: {fecha}
⏰ Hora: {hora}
📍 Lugar: {ubicacion}

¡Te esperamos!

{nombre_negocio}
'''
            },
            'lead_qualified': {
                'subject': '🔥 Lead caliente listo para cerrar',
                'body': '''Hola,

Tienes un lead caliente listo para cerrar.

Datos del lead:
- Nombre: {nombre}
- Teléfono: {telefono}
- Interés: {interes}
- Presupuesto: {presupuesto}

¡Contáctalo ahora!

{nombre_negocio}
'''
            }
        }
        
        if template not in templates:
            print(f"[Email] Template '{template}' not found")
            return False
        
        tpl = templates[template]
        subject = tpl['subject']
        body = tpl['body']
        
        # Reemplazar variables
        for key, value in variables.items():
            subject = subject.replace('{' + key + '}', str(value))
            body = body.replace('{' + key + '}', str(value))
        
        return self.send_email(to, subject, body, html=False)
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión SMTP
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            
            server.login(self.email_user, self.email_password)
            server.quit()
            
            print(f"[Email] Connection test successful for {self.email_user}")
            return True
            
        except Exception as e:
            print(f"[Email] Connection test failed: {e}")
            return False


def get_email_service_for_client(client_data: Dict[str, Any]) -> Optional[EmailService]:
    """
    Obtiene un EmailService configurado para un cliente
    
    Args:
        client_data: Datos del cliente desde la base de datos
        
    Returns:
        EmailService configurado o None si no hay configuración
    """
    # Verificar si el cliente tiene configuración SMTP
    if not client_data.get('email_user') or not client_data.get('email_password'):
        print(f"[Email] Client {client_data.get('id')} has no email config")
        return None
    
    return EmailService(
        smtp_server=client_data.get('email_smtp_server', 'smtp.gmail.com'),
        smtp_port=client_data.get('email_smtp_port', 587),
        email_user=client_data.get('email_user', ''),
        email_password=client_data.get('email_password', ''),
        email_from_name=client_data.get('email_from_name', '')
    )
