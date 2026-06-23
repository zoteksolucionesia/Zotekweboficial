"""
Appointment Service para Zotek IA
Gestiona citas, recordatorios y confirmaciones
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import sys


class AppointmentService:
    """Servicio para gestión de citas y recordatorios"""
    
    def __init__(self):
        """Inicializa el servicio de citas"""
        self.db_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        return psycopg2.connect(self.db_url)
    
    def create_appointment(self, client_id: int, phone: str,
                          date_time: datetime, name: str = None,
                          email: str = '', notes: str = None) -> dict:
        """
        Crea una nueva cita.

        Returns:
            {"id": int, "token": str} o {"id": -1, "token": None} en error
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                INSERT INTO appointments
                (client_id, phone, date_time, name, email, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, token
            """, (client_id, phone, date_time, name, email or '', notes or ''))

            row = cursor.fetchone()
            appointment_id = row['id']
            token = str(row['token'])
            conn.commit()
            cursor.close()
            conn.close()

            print(f"[Appointment] Created appointment {appointment_id} for {phone}")
            return {"id": appointment_id, "token": token}

        except Exception as e:
            print(f"[Appointment] Error creating appointment: {e}")
            return {"id": -1, "token": None}
    
    def confirm_appointment(self, appointment_id: int) -> bool:
        """
        Confirma una cita
        
        Args:
            appointment_id: ID de la cita
            
        Returns:
            True si se confirmó correctamente
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE appointments
                SET status = 'confirmed'
                WHERE id = %s
            """, (appointment_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[Appointment] Confirmed appointment {appointment_id}")
            return True
            
        except Exception as e:
            print(f"[Appointment] Error confirming appointment: {e}")
            return False
    
    def cancel_appointment(self, appointment_id: int, cancelled_by: str = None) -> bool:
        """
        Cancela una cita

        Args:
            appointment_id: ID de la cita
            cancelled_by: quién canceló — 'business' (negocio desde admin/portal)
                          o 'patient' (paciente desde el link público). Opcional.

        Returns:
            True si se canceló correctamente
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE appointments
                SET status = 'cancelled', cancelled_by = %s
                WHERE id = %s
            """, (cancelled_by, appointment_id))

            conn.commit()
            cursor.close()
            conn.close()

            print(f"[Appointment] Cancelled appointment {appointment_id} by {cancelled_by}")
            return True

        except Exception as e:
            print(f"[Appointment] Error cancelling appointment: {e}")
            return False
    
    def get_tomorrow_appointments(self, client_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene las citas de mañana para un cliente
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Lista de citas de mañana
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Mañana
            tomorrow = datetime.now().date() + timedelta(days=1)
            tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
            tomorrow_end = datetime.combine(tomorrow, datetime.max.time())
            
            cursor.execute("""
                SELECT a.*, c.name as client_name, c.phone_number_id as business_phone
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                WHERE a.client_id = %s 
                  AND a.date_time >= %s 
                  AND a.date_time < %s
                  AND a.status IN ('pending', 'confirmed')
                ORDER BY a.date_time ASC
            """, (client_id, tomorrow_start, tomorrow_end))
            
            appointments = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(apt) for apt in appointments]
            
        except Exception as e:
            print(f"[Appointment] Error getting tomorrow appointments: {e}")
            return []

    def get_appointment_by_id(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una cita por ID
        
        Args:
            appointment_id: ID de la cita
            
        Returns:
            Datos de la cita o None si no existe
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT a.*, c.name as client_name, c.phone_number_id as business_phone
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                WHERE a.id = %s
            """, (appointment_id,))
            
            appointment = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(appointment) if appointment else None
            
        except Exception as e:
            print(f"[Appointment] Error getting appointment: {e}")
            return None
    
    def get_pending_appointments(self, client_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene citas pendientes de un cliente (desde hoy en adelante)
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Lista de citas pendientes
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT a.*, c.name as client_name
                FROM appointments a
                JOIN clients c ON a.client_id = c.id
                WHERE a.client_id = %s 
                  AND a.status = 'pending'
                  AND a.date_time >= CURRENT_TIMESTAMP
                ORDER BY a.date_time ASC
            """, (client_id,))
            
            appointments = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(apt) for apt in appointments]
            
        except Exception as e:
            print(f"[Appointment] Error getting pending appointments: {e}")
            return []


# Instancia global para uso fácil
appointment_service = AppointmentService()
