"""
Lead Service para Zotek IA
Gestiona el seguimiento de leads, detección de leads fríos y follow-ups
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import sys


class LeadService:
    """Servicio para gestión de leads y follow-ups"""
    
    def __init__(self):
        """Inicializa el servicio de leads"""
        self.db_url = os.getenv('DATABASE_URL')
    
    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        return psycopg2.connect(self.db_url)
    
    def track_interaction(self, client_id: int, phone_number: str, 
                         message: str, response: str = None) -> int:
        """
        Registra una interacción con un lead
        
        Args:
            client_id: ID del cliente (negocio)
            phone_number: Teléfono del lead
            message: Mensaje del lead
            response: Respuesta del bot
            
        Returns:
            ID del lead tracking creado o actualizado
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Buscar si el lead ya existe
            cursor.execute("""
                SELECT id, followup_count 
                FROM lead_tracking 
                WHERE client_id = %s AND phone_number = %s
                ORDER BY created_at DESC 
                LIMIT 1
            """, (client_id, phone_number))
            
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar lead existente
                cursor.execute("""
                    UPDATE lead_tracking 
                    SET last_interaction = CURRENT_TIMESTAMP,
                        last_message_sent = %s,
                        last_message_response = %s,
                        status = CASE 
                            WHEN status = 'cold' THEN 'contacted'
                            ELSE status
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (message, response, existing['id']))
                
                lead_id = existing['id']
                print(f"[Lead] Updated interaction for {phone_number}")
            else:
                # Crear nuevo lead
                cursor.execute("""
                    INSERT INTO lead_tracking 
                    (client_id, phone_number, last_message_sent, last_message_response, status)
                    VALUES (%s, %s, %s, %s, 'new')
                    RETURNING id
                """, (client_id, phone_number, message, response))
                
                lead_id = cursor.fetchone()['id']
                print(f"[Lead] Created new lead {phone_number} for client {client_id}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return lead_id
            
        except Exception as e:
            print(f"[Lead] Error tracking interaction: {e}")
            return -1
    
    def mark_lead_cold(self, lead_id: int) -> bool:
        """
        Marca un lead como frío (no respondió)
        
        Args:
            lead_id: ID del lead
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE lead_tracking 
                SET status = 'cold',
                    followup_count = followup_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (lead_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[Lead] Marked lead {lead_id} as cold")
            return True
            
        except Exception as e:
            print(f"[Lead] Error marking lead cold: {e}")
            return False
    
    def mark_lead_converted(self, lead_id: int) -> bool:
        """
        Marca un lead como convertido (venta cerrada)
        
        Args:
            lead_id: ID del lead
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE lead_tracking 
                SET status = 'converted',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (lead_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[Lead] Marked lead {lead_id} as converted")
            return True
            
        except Exception as e:
            print(f"[Lead] Error marking lead converted: {e}")
            return False
    
    def get_cold_leads(self, client_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Obtiene leads fríos que no han respondido en X horas
        
        Args:
            client_id: ID del cliente
            hours: Horas sin respuesta
            
        Returns:
            Lista de leads fríos
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT lt.*, c.name as client_name, c.phone_number_id as business_phone
                FROM lead_tracking lt
                JOIN clients c ON lt.client_id = c.id
                WHERE lt.client_id = %s 
                  AND lt.status IN ('new', 'contacted', 'cold')
                  AND lt.last_interaction < CURRENT_TIMESTAMP - INTERVAL '%s hours'
                ORDER BY lt.last_interaction ASC
            """, (client_id, hours))
            
            leads = cursor.fetchall()
            cursor.close()
            conn.close()
            
            print(f"[Lead] Found {len(leads)} cold leads for client {client_id}")
            return [dict(lead) for lead in leads]
            
        except Exception as e:
            print(f"[Lead] Error getting cold leads: {e}")
            return []
    
    def get_lead_by_phone(self, client_id: int, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un lead por teléfono
        
        Args:
            client_id: ID del cliente
            phone_number: Teléfono del lead
            
        Returns:
            Datos del lead o None si no existe
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM lead_tracking
                WHERE client_id = %s AND phone_number = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (client_id, phone_number))
            
            lead = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(lead) if lead else None
            
        except Exception as e:
            print(f"[Lead] Error getting lead by phone: {e}")
            return None
    
    def qualify_lead(self, lead_id: int, score: int, 
                    qualification_data: Dict[str, Any] = None) -> bool:
        """
        Califica un lead con un score
        
        Args:
            lead_id: ID del lead
            score: Score del 0-100
            qualification_data: Datos adicionales de calificación
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Determinar status basado en score
            if score >= 80:
                status = 'qualified'
            elif score >= 50:
                status = 'contacted'
            else:
                status = 'cold'
            
            cursor.execute("""
                UPDATE lead_tracking 
                SET status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, lead_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[Lead] Qualified lead {lead_id} with score {score} -> {status}")
            return True
            
        except Exception as e:
            print(f"[Lead] Error qualifying lead: {e}")
            return False


# Instancia global para uso fácil
lead_service = LeadService()
