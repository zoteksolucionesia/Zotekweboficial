"""
Servicio de lectura de citas para el sistema de recordatorios.

Por ahora lee desde la tabla `citas` de PostgreSQL.
Futuro: integración con Google Calendar API.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def get_upcoming_appointments_for_reminders(hours_ahead: int = 24) -> List[Dict[str, Any]]:
    """
    Obtiene las citas que están dentro de las próximas N horas
    y que aún no han tenido llamada de recordatorio.
    
    Solo aplica para clientes con plan 'pro' o 'enterprise'
    (servicio premium de llamadas).
    
    Args:
        hours_ahead: Margen de horas hacia adelante para buscar citas.
    
    Returns:
        Lista de dicts con información de la cita y del cliente.
    """
    # Importamos aquí para evitar circular imports
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL no configurada")
        return []

    now = datetime.now()
    # Ventana de búsqueda: entre ahora y N horas adelante
    window_start = now.strftime("%Y-%m-%d %H:%M")
    window_end = (now + timedelta(hours=hours_ahead)).strftime("%Y-%m-%d %H:%M")

    query = """
        SELECT 
            citas.id AS cita_id,
            citas.paciente_nombre,
            citas.cliente_telefono,
            citas.fecha_hora,
            citas.motivo,
            citas.reminder_status,
            clients.id AS client_id,
            clients.name AS client_name,
            clients.plan,
            clients.phone_number_id
        FROM citas
        JOIN clients ON citas.client_id = clients.id
        WHERE 
            clients.plan IN ('pro', 'enterprise')
            AND citas.reminder_status IS DISTINCT FROM 'llamado'
            AND citas.reminder_status IS DISTINCT FROM 'fallido_max'
            AND citas.fecha_hora::text >= %s
            AND citas.fecha_hora::text <= %s
        ORDER BY citas.fecha_hora ASC
    """

    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, (window_start, window_end))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ ERROR get_upcoming_appointments_for_reminders: {e}")
        return []


def format_fecha_legible(fecha_hora_str: str) -> str:
    """
    Convierte una fecha ISO a texto legible en español para la llamada de voz.
    Ej: '2026-03-24 15:00' → 'mañana a las 3 de la tarde'
    """
    try:
        dt = datetime.fromisoformat(str(fecha_hora_str).replace("T", " ").split(".")[0])
        now = datetime.now()
        delta_days = (dt.date() - now.date()).days
        
        # Día
        if delta_days == 0:
            dia = "hoy"
        elif delta_days == 1:
            dia = "mañana"
        elif delta_days == 2:
            dia = "pasado mañana"
        else:
            dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            dia = f"el {dias_semana[dt.weekday()]} {dt.day} de {['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'][dt.month-1]}"
        
        # Hora
        hora = dt.hour
        minuto = dt.minute
        if minuto == 0:
            hora_str = f"a las {hora} en punto" if hora >= 12 else f"a las {hora}"
            if hora == 12:
                hora_str = "al mediodía"
            elif hora > 12:
                hora_str = f"a las {hora - 12} de la tarde"
            else:
                hora_str = f"a las {hora} de la mañana"
        else:
            if hora >= 12:
                hora_str = f"a las {hora - 12 if hora > 12 else hora}:{minuto:02d} de la {'tarde' if hora < 18 else 'noche'}"
            else:
                hora_str = f"a las {hora}:{minuto:02d} de la mañana"
        
        return f"{dia} {hora_str}"
    except Exception as e:
        print(f"⚠️ Error formateando fecha: {e}")
        return str(fecha_hora_str)
