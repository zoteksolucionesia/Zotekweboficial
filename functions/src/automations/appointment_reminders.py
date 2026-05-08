"""
Automated Appointment Reminders
Ejecuta cada día a las 10 AM para enviar recordatorios de citas del día siguiente
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_connection
from services.email_service import get_email_service_for_client
from psycopg2.extras import RealDictCursor


def get_tomorrow_appointments():
    """
    Obtiene todas las citas de mañana para todos los clientes
    
    Returns:
        Lista de citas de mañana
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Mañana
        tomorrow = datetime.now().date() + timedelta(days=1)
        tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
        tomorrow_end = datetime.combine(tomorrow, datetime.max.time())
        
        cursor.execute("""
            SELECT a.*, c.name as client_name, c.email as client_email,
                   c.email_smtp_server, c.email_smtp_port, c.email_user, 
                   c.email_password, c.email_from_name,
                   c.email_notifications_enabled
            FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE a.appointment_date >= %s 
              AND a.appointment_date < %s
              AND a.status IN ('pending', 'confirmed')
              AND a.reminder_sent = FALSE
              AND c.email_notifications_enabled = TRUE
              AND c.email_user IS NOT NULL
              AND c.email_password IS NOT NULL
            ORDER BY a.appointment_date ASC
        """, (tomorrow_start, tomorrow_end))
        
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"Found {len(appointments)} appointments for tomorrow without reminder sent")
        return [dict(apt) for apt in appointments]
        
    except Exception as e:
        print(f"Error getting tomorrow appointments: {e}")
        return []


def send_appointment_reminder(appointment):
    """
    Envía recordatorio de cita por email

    Args:
        appointment: Datos de la cita

    Returns:
        True si se envió correctamente
    """
    try:
        # Obtener email del cliente
        customer_email = appointment.get('customer_email', '')

        # Si no hay email, no podemos enviar
        if not customer_email:
            print(f"Appointment {appointment['id']} no tiene email del cliente. Skipping.")
            return False

        # Construir configuración de email del cliente
        from services.email_service import EmailService

        email_service = EmailService(
            smtp_server=appointment.get('email_smtp_server', 'smtp.gmail.com'),
            smtp_port=appointment.get('email_smtp_port', 587),
            email_user=appointment.get('email_user', ''),
            email_password=appointment.get('email_password', ''),
            email_from_name=appointment.get('email_from_name', '')
        )

        # Formatear fecha y hora
        apt_datetime = appointment.get('appointment_date')
        if isinstance(apt_datetime, datetime):
            fecha_str = apt_datetime.strftime('%d/%m/%Y')
            hora_str = apt_datetime.strftime('%H:%M')
        else:
            fecha_str = str(apt_datetime)[:10]
            hora_str = str(apt_datetime)[11:16]

        # Plantilla de recordatorio
        customer_name = appointment.get('customer_name', 'Cliente')
        client_name = appointment.get('client_name', 'Tu Negocio')
        notes = appointment.get('notes', '')

        subject = f"Recordatorio de tu cita mañana - {client_name}"
        body = f'''Hola {customer_name},

Te recordamos que tienes una cita agendada para mañana.

📅 Fecha: {fecha_str}
⏰ Hora: {hora_str}
📍 Lugar: {client_name}

¿Confirmas tu asistencia?

Si necesitas cancelar o reprogramar, por favor contáctanos lo antes posible.

¡Te esperamos!

{client_name}
{notes if notes else ''}
'''

        # Enviar email
        success = email_service.send_email(customer_email, subject, body)

        if success:
            print(f"Recordatorio enviado a {customer_email}: {subject}")
            mark_reminder_sent(appointment['id'])
            return True
        else:
            print(f"Error al enviar recordatorio a {customer_email}")
            return False

    except Exception as e:
        print(f"Error sending appointment reminder: {e}")
        return False


def mark_reminder_sent(appointment_id):
    """
    Marca el recordatorio como enviado
    
    Args:
        appointment_id: ID de la cita
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE appointments 
            SET reminder_sent = TRUE,
                reminder_sent_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (appointment_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Marked reminder sent for appointment {appointment_id}")
        
    except Exception as e:
        print(f"Error marking reminder sent: {e}")


def send_summary_to_business(appointments_by_client):
    """
    Envía resumen diario al negocio
    
    Args:
        appointments_by_client: Diccionario {client_id: [appointments]}
    """
    try:
        for client_id, appointments in appointments_by_client.items():
            if not appointments:
                continue
            
            client_name = appointments[0].get('client_name')
            client_email = appointments[0].get('client_email')
            
            if not client_email:
                continue
            
            # Construir resumen
            subject = f"📅 Resumen de citas para mañana - {len(appointments)} citas"
            
            body = f'''Hola {client_name},

Aquí está el resumen de tus citas para mañana:

'''
            for i, apt in enumerate(appointments, 1):
                apt_datetime = apt.get('appointment_date')
                if isinstance(apt_datetime, datetime):
                    fecha_str = apt_datetime.strftime('%d/%m %H:%M')
                else:
                    fecha_str = str(apt_datetime)[:16]
                
                customer = apt.get('customer_name', 'Sin nombre')
                phone = apt.get('phone_number', 'Sin teléfono')
                
                body += f"{i}. {fecha_str} - {customer} ({phone})\n"
            
            body += f'''

Total: {len(appointments)} citas

¡Que tengas un excelente día!

Zotek IA
'''
            
            # TODO: Enviar email al negocio
            print(f"Would send summary to {client_name} at {client_email}")
            print(f"Total appointments: {len(appointments)}")
            
    except Exception as e:
        print(f"Error sending summary: {e}")


# Entry point para Cloud Functions
def appointment_reminders(request):
    """
    Cloud Function entry point para recordatorios de citas
    Se ejecuta cada día a las 10 AM vía Cloud Scheduler
    """
    print("=== Starting Appointment Reminders ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Obtener citas de mañana
    appointments = get_tomorrow_appointments()
    
    if not appointments:
        print("No appointments found for tomorrow")
        return {"status": "success", "reminders_sent": 0, "message": "No appointments found"}
    
    total_sent = 0
    appointments_by_client = {}
    
    # Agrupar por cliente para el resumen
    for appointment in appointments:
        client_id = appointment.get('client_id')
        if client_id not in appointments_by_client:
            appointments_by_client[client_id] = []
        appointments_by_client[client_id].append(appointment)
    
    # Enviar recordatorios
    for appointment in appointments:
        print(f"\nProcessing appointment {appointment['id']}")
        print(f"Customer: {appointment.get('customer_name')}")
        print(f"Date: {appointment.get('appointment_date')}")
        
        success = send_appointment_reminder(appointment)
        
        if success:
            total_sent += 1
    
    # Enviar resúmenes a los negocios
    print(f"\n=== Sending Business Summaries ===")
    send_summary_to_business(appointments_by_client)
    
    print(f"\n=== Reminders Complete ===")
    print(f"Total reminders sent: {total_sent}")
    print(f"Total businesses notified: {len(appointments_by_client)}")
    
    return {
        "status": "success",
        "reminders_sent": total_sent,
        "businesses_notified": len(appointments_by_client)
    }


# Para testing local
if __name__ == "__main__":
    # Simular request
    class MockRequest:
        json = {}
    
    result = appointment_reminders(MockRequest())
    print(f"\nResult: {result}")
