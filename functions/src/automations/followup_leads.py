"""
Automated Follow-up for Cold Leads
Ejecuta cada hora para detectar y hacer follow-up de leads fríos
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_connection
from services.email_service import get_email_service_for_client
from psycopg2.extras import RealDictCursor


def get_cold_leads(hours: int = 24):
    """
    Obtiene leads fríos que no han respondido en X horas
    
    Args:
        hours: Horas sin respuesta
        
    Returns:
        Lista de leads fríos
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT lt.*, c.name as client_name, c.email as client_email,
                   c.email_smtp_server, c.email_smtp_port, c.email_user, 
                   c.email_password, c.email_from_name
            FROM lead_tracking lt
            JOIN clients c ON lt.client_id = c.id
            WHERE lt.status IN ('new', 'contacted', 'cold')
              AND lt.last_interaction < CURRENT_TIMESTAMP - INTERVAL '%s hours'
              AND c.email_notifications_enabled = TRUE
              AND c.email_user IS NOT NULL
              AND c.email_password IS NOT NULL
            ORDER BY lt.last_interaction ASC
        """, (hours,))
        
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"Found {len(leads)} cold leads older than {hours} hours")
        return [dict(lead) for lead in leads]
        
    except Exception as e:
        print(f"Error getting cold leads: {e}")
        return []


def send_followup_email(lead, template_key='followup_24h'):
    """
    Envía email de follow-up a un lead frío

    Args:
        lead: Datos del lead
        template_key: Plantilla a usar

    Returns:
        True si se envió correctamente
    """
    try:
        # Obtener email del lead
        lead_email = lead.get('email', '')

        # Si no hay email, no podemos enviar
        if not lead_email:
            print(f"Lead {lead['id']} no tiene email. Skipping.")
            return False

        # Construir configuración de email del cliente
        from services.email_service import EmailService

        email_service = EmailService(
            smtp_server=lead.get('email_smtp_server', 'smtp.gmail.com'),
            smtp_port=lead.get('email_smtp_port', 587),
            email_user=lead.get('email_user', ''),
            email_password=lead.get('email_password', ''),
            email_from_name=lead.get('email_from_name', '')
        )

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
            'followup_48h': {
                'subject': 'Última oportunidad - 20% de descuento',
                'body': '''Hola {nombre},

Notamos que estás interesado en nuestros servicios.

¡Solo por hoy, tenemos 20% de descuento!

¿Te gustaría aprovechar esta oportunidad?

{nombre_negocio}
'''
            },
            'followup_72h': {
                'subject': '¿Aún estás ahí?',
                'body': '''Hola {nombre},

Esta será nuestra última comunicación por ahora.

Si cambias de opinión, estamos aquí para ayudarte.

{nombre_negocio}
'''
            }
        }

        if template_key not in templates:
            print(f"Template {template_key} not found")
            return False

        tpl = templates[template_key]

        # Reemplazar variables
        nombre = lead.get('phone_number', 'Cliente')  # Usamos phone como nombre si no hay
        nombre_negocio = lead.get('client_name', 'Tu Negocio')

        subject = tpl['subject'].format(nombre=nombre, nombre_negocio=nombre_negocio)
        body = tpl['body'].format(nombre=nombre, nombre_negocio=nombre_negocio)

        # Enviar email
        success = email_service.send_email(lead_email, subject, body)

        if success:
            print(f"Email enviado a {lead_email}: {subject}")
            mark_lead_contacted(lead['id'])
            return True
        else:
            print(f"Error al enviar email a {lead_email}")
            return False

    except Exception as e:
        print(f"Error sending followup email: {e}")
        return False


def mark_lead_contacted(lead_id):
    """
    Marca un lead como contactado después del follow-up
    
    Args:
        lead_id: ID del lead
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE lead_tracking 
            SET status = 'contacted',
                followup_count = followup_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (lead_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Marked lead {lead_id} as contacted")
        
    except Exception as e:
        print(f"Error marking lead contacted: {e}")


def send_notification_to_business(lead, followup_count):
    """
    Notifica al negocio sobre un lead frío
    
    Args:
        lead: Datos del lead
        followup_count: Número de follow-ups enviados
    """
    try:
        if not lead.get('client_email'):
            return
        
        email_config = {
            'email_smtp_server': lead.get('email_smtp_server', 'smtp.gmail.com'),
            'email_smtp_port': lead.get('email_smtp_port', 587),
            'email_user': lead.get('email_user', ''),
            'email_password': lead.get('email_password', ''),
            'email_from_name': lead.get('email_from_name', '')
        }
        
        subject = f"🔔 Lead frío - {lead.get('client_name')}"
        body = f'''Hola,

Tienes un lead que no ha respondido después de {followup_count} follow-ups.

Datos del lead:
- Teléfono: {lead.get('phone_number')}
- Última interacción: {lead.get('last_interaction')}
- Estado: {lead.get('status')}

Te recomendamos contactarlo directamente.

{lead.get('client_name')}
'''
        
        # TODO: Enviar email al negocio
        print(f"Would notify business at {lead.get('client_email')}: {subject}")
        
    except Exception as e:
        print(f"Error notifying business: {e}")


# Entry point para Cloud Functions
def followup_cold_leads(request):
    """
    Cloud Function entry point para follow-up de leads fríos
    Se ejecuta cada hora vía Cloud Scheduler
    """
    print("=== Starting Cold Lead Follow-up ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Configuración
    followup_intervals = [24, 48, 72]  # Horas
    templates_map = {
        24: 'followup_24h',
        48: 'followup_48h',
        72: 'followup_72h'
    }
    
    total_sent = 0
    total_leads = 0
    
    for hours in followup_intervals:
        print(f"\n--- Processing leads cold for {hours} hours ---")
        
        leads = get_cold_leads(hours)
        total_leads += len(leads)
        
        template_key = templates_map.get(hours, 'followup_24h')
        
        for lead in leads:
            # Verificar si ya se envió follow-up para este intervalo
            if lead.get('followup_count', 0) >= (hours // 24):
                print(f"Skipping lead {lead['id']} - already contacted")
                continue
            
            print(f"Processing lead {lead['id']} ({lead.get('phone_number')})")
            
            success = send_followup_email(lead, template_key)
            
            if success:
                total_sent += 1
                
                # Notificar al negocio si es el tercer follow-up
                if hours == 72:
                    send_notification_to_business(lead, lead.get('followup_count', 0) + 1)
    
    print(f"\n=== Follow-up Complete ===")
    print(f"Total leads processed: {total_leads}")
    print(f"Total emails sent: {total_sent}")
    
    return {"status": "success", "leads_processed": total_leads, "emails_sent": total_sent}


# Para testing local
if __name__ == "__main__":
    # Simular request
    class MockRequest:
        json = {}
    
    result = followup_cold_leads(MockRequest())
    print(f"\nResult: {result}")
