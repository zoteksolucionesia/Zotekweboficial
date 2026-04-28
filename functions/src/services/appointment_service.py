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
                          email: str = '', notes: str = None) -> int:
        """
        Crea una nueva cita
        
        Args:
            client_id: ID del cliente (negocio)
            phone: Teléfono del cliente
            date_time: Fecha y hora de la cita
            name: Nombre del cliente (opcional)
            email: Email del cliente (opcional)
            notes: Notas adicionales
            
        Returns:
            ID de la cita creada
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Nota: el schema actual de `appointments` no tiene columnas `email`/`notes`;
            # los parámetros se conservan por compatibilidad con los callers pero se ignoran.
            cursor.execute("""
                INSERT INTO appointments
                (client_id, phone, date_time, name)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (client_id, phone, date_time, name))
            
            appointment_id = cursor.fetchone()['id']
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[Appointment] Created appointment {appointment_id} for {phone}")
            return appointment_id
            
        except Exception as e:
            print(f"[Appointment] Error creating appointment: {e}")
            return -1
    
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
    
    def cancel_appointment(self, appointment_id: int) -> bool:
        """
        Cancela una cita
        
        Args:
            appointment_id: ID de la cita
            
        Returns:
            True si se canceló correctamente
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE appointments
                SET status = 'cancelled'
                WHERE id = %s
            """, (appointment_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[Appointment] Cancelled appointment {appointment_id}")
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
