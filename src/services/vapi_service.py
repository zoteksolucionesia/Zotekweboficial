"""
Servicio de llamadas de voz automatizadas usando VAPI.ai.

Este módulo maneja las llamadas salientes de recordatorio de citas
que Zotek realiza en nombre de sus clientes (psicólogos, dentistas, etc.)
usando su propio número de VAPI, sin que el cliente final necesite configurar nada.
"""

import os
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

# VAPI API endpoint
VAPI_BASE_URL = "https://api.vapi.ai"


class VapiService:
    """
    Cliente para la API de VAPI.ai.
    
    Zotek centraliza un solo número de VAPI y un asistente de voz
    que se personaliza dinámicamente para cada cliente (psicóloga, dentista, etc.).
    """

    def __init__(self):
        self.api_key = os.getenv("VAPI_API_KEY")
        self.assistant_id = os.getenv("VAPI_ASSISTANT_ID")
        self.phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")

        if not self.api_key:
            print("⚠️  VAPI_API_KEY no configurada en .env")

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def iniciar_llamada_recordatorio(
        self,
        numero_paciente: str,
        nombre_paciente: str,
        fecha_cita: str,
        nombre_profesional: str,
        nombre_consultorio: str = "",
        motivo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Inicia una llamada de voz saliente para recordar una cita.

        Args:
            numero_paciente: Número en formato E.164, ej. '+5215512345678'
            nombre_paciente: Nombre del paciente para que el asistente lo llame por nombre.
            fecha_cita: Texto legible de la fecha/hora de la cita, ej. 'mañana a las 3pm'.
            nombre_profesional: Nombre del profesional, ej. 'Dra. González'.
            nombre_consultorio: Nombre del consultorio o negocio.
            motivo: Motivo de la cita (opcional, para personalizar el mensaje).

        Returns:
            Dict con 'success', 'call_id' y 'error' (si aplica).
        """
        if not self.api_key:
            return {"success": False, "error": "VAPI_API_KEY no configurada"}

        # Normalizar número a E.164 si viene sin '+'
        if numero_paciente and not numero_paciente.startswith("+"):
            numero_paciente = f"+{numero_paciente}"

        # Variables dinámicas que el asistente de VAPI usará en su script
        variables = {
            "nombre_paciente": nombre_paciente,
            "fecha_cita": fecha_cita,
            "nombre_profesional": nombre_profesional,
            "nombre_consultorio": nombre_consultorio or nombre_profesional,
        }
        if motivo:
            variables["motivo"] = motivo

        payload = {
            "assistantId": self.assistant_id,
            "phoneNumberId": self.phone_number_id,
            "customer": {
                "number": numero_paciente,
                "name": nombre_paciente,
            },
            "assistantOverrides": {
                "variableValues": variables,
            },
        }

        try:
            print(f"📞 VAPI: Iniciando llamada a {numero_paciente} para {nombre_profesional}")
            response = requests.post(
                f"{VAPI_BASE_URL}/call/phone",
                headers=self._headers,
                json=payload,
                timeout=15,
            )

            if response.status_code in (200, 201):
                data = response.json()
                call_id = data.get("id", "")
                print(f"✅ VAPI: Llamada iniciada. call_id={call_id}")
                return {"success": True, "call_id": call_id, "data": data}
            else:
                error_msg = response.text[:200]
                print(f"❌ VAPI Error ({response.status_code}): {error_msg}")
                return {"success": False, "error": error_msg, "status_code": response.status_code}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con VAPI"}
        except Exception as e:
            print(f"🔥 VAPI Exception: {e}")
            return {"success": False, "error": str(e)}

    def obtener_estado_llamada(self, call_id: str) -> Dict[str, Any]:
        """Consulta el estado de una llamada en curso o completada."""
        if not self.api_key:
            return {"success": False, "error": "VAPI_API_KEY no configurada"}

        try:
            response = requests.get(
                f"{VAPI_BASE_URL}/call/{call_id}",
                headers=self._headers,
                timeout=10,
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            return {"success": False, "error": response.text[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def listar_llamadas(self, limit: int = 10) -> Dict[str, Any]:
        """Lista las últimas llamadas realizadas (para debug y admin)."""
        try:
            response = requests.get(
                f"{VAPI_BASE_URL}/call",
                headers=self._headers,
                params={"limit": limit},
                timeout=10,
            )
            if response.status_code == 200:
                return {"success": True, "calls": response.json()}
            return {"success": False, "error": response.text[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Instancia global reutilizable
vapi = VapiService()
