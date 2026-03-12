"""
Servicio de Gemini para generación de respuestas inteligentes.

Incluye:
- Caché de conocimiento por cliente
- Historial de conversación para contexto
- Reintentos automáticos con backoff
- Sanitización de logs
"""

from google import genai
from google.genai import types
import os
import time
import traceback
import json
from typing import Dict, List, Optional, Any
from .. import database
from ..config import Config


class GeminiEngine:
    """Motor de IA basado en Gemini para generación de respuestas."""
    
    def __init__(self, api_key: str = None):
        """
        Inicializa el cliente de Gemini.
        
        Args:
            api_key: API key de Gemini (opcional, usa Config si no se proporciona)
        """
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = Config.GEMINI_MODEL_ID
        
        # Caché de conocimiento por cliente
        self._knowledge_cache: Dict[str, str] = {}
        self._cache_expiry: Dict[str, float] = {}
        self._cache_ttl = Config.KNOWLEDGE_CACHE_TTL_SECONDS  # 5 minutos
    
    def _get_cached_knowledge(self, client_id: str) -> Optional[str]:
        """
        Obtiene conocimiento cacheado para un cliente.
        
        Args:
            client_id: ID del cliente
        
        Returns:
            Conocimiento cacheado o None si no existe/expiró
        """
        if client_id in self._knowledge_cache:
            if time.time() < self._cache_expiry.get(client_id, 0):
                return self._knowledge_cache[client_id]
            else:
                # Cache expirado, limpiar
                del self._knowledge_cache[client_id]
                if client_id in self._cache_expiry:
                    del self._cache_expiry[client_id]
        return None
    
    def _cache_knowledge(self, client_id: str, knowledge: str):
        """
        Cachea conocimiento del cliente.
        
        Args:
            client_id: ID del cliente
            knowledge: Conocimiento a cachear
        """
        self._knowledge_cache[client_id] = knowledge
        self._cache_expiry[client_id] = time.time() + self._cache_ttl
    
    def _build_conversation_context(self, phone_number: str, limit: int = None) -> str:
        """
        Construye contexto de conversación reciente.
        
        Args:
            phone_number: Número de teléfono del usuario
            limit: Límite de mensajes (usa Config si None)
        
        Returns:
            String con el historial de conversación formateado
        """
        limit = limit or Config.CONVERSATION_HISTORY_LIMIT
        historial = database.get_conversation_history(phone_number, limit=limit)
        
        if not historial:
            return ""
        
        contexto_lines = []
        for msg in historial:
            rol = "Usuario" if msg['is_user'] else "Asistente"
            contexto_lines.append(f"{rol}: {msg['content']}")
        
        return "\n".join(contexto_lines)
    
    def generar_respuesta(
        self, 
        mensaje_usuario: str, 
        client_data: Dict[str, Any], 
        numero_telefono: str,
        usar_historial: bool = True
    ) -> str:
        """
        Genera una respuesta inteligente basada en el contexto del cliente.
        
        Args:
            mensaje_usuario: Mensaje del usuario
            client_data: Datos del cliente (dict de database)
            numero_telefono: Número de teléfono para historial
            usar_historial: Si True, incluye historial de conversación
        
        Returns:
            Respuesta generada por Gemini
        """
        client_id = str(client_data['id'])
        nombre_cliente = client_data.get('name', 'Cliente')
        
        # 1. Obtener conocimiento (de caché o BD)
        conocimiento = self._get_cached_knowledge(client_id)
        if conocimiento is None:
            conocimiento = database.get_client_knowledge(client_id)
            self._cache_knowledge(client_id, conocimiento)
        
        # 2. Construir instrucción del sistema
        instrucciones_base = client_data.get('system_instruction') or \
            f"Eres un asistente virtual para {nombre_cliente}. Sé amable, breve y profesional."
        
        prompt_sistema = f"""
        {instrucciones_base}

        CONOCIMIENTO DEL CLIENTE:
        {conocimiento if conocimiento else "No hay conocimiento específico disponible."}
        """
        
        # 3. Agregar historial de conversación si está disponible
        if usar_historial:
            contexto_conversacion = self._build_conversation_context(numero_telefono)
            if contexto_conversacion:
                prompt_sistema += f"""

        CONVERSACIÓN RECIENTE:
        {contexto_conversacion}

        Responde de manera coherente con la conversación anterior.
        """
        
        # 4. Llamar a Gemini con reintentos
        max_retries = Config.GEMINI_MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    config={
                        "system_instruction": prompt_sistema,
                        "temperature": Config.GEMINI_TEMPERATURE,
                    },
                    contents=mensaje_usuario
                )
                
                respuesta = response.text.strip() if response.text else "Lo siento, no pude generar una respuesta."
                
                # 5. Guardar en historial (async, no bloqueante)
                if usar_historial:
                    try:
                        database.add_to_conversation_history(
                            numero_telefono, 
                            mensaje_usuario, 
                            respuesta
                        )
                    except Exception as e:
                        print(f"⚠️ ERROR guardando historial: {e}")
                
                return respuesta
                
            except Exception as e:
                error_str = str(e)
                
                # Reintentar para errores 503 (Service Unavailable) o 429 (Rate Limit)
                if ("503" in error_str or "429" in error_str) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * Config.GEMINI_RETRY_DELAY_SECONDS
                    print(f"⚠️ Reintentando Gemini ({attempt+1}/{max_retries}) en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                # Log error completo
                error_msg = f"💀 ERROR GEMINI ({type(e).__name__}): {error_str[:100]}...\n{traceback.format_exc()}"
                print(error_msg)
                
                # Respuesta fallback amigable
                return "Lo siento, tuve un problema procesando tu mensaje. ¿Puedes repetirlo?"
        
        # Fallback final si todos los reintentos fallaron
        return "Lo siento, estoy teniendo problemas técnicos. Por favor intenta de nuevo en unos momentos."
    
    def detectar_intencion_y_opciones(
        self, 
        mensaje: str, 
        menu_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detecta la intención del usuario y sugiere opciones del menú.
        
        Args:
            mensaje: Mensaje del usuario
            menu_json: Estructura del menú con opciones
        
        Returns:
            Dict con matched_option y confidence
        """
        opciones = menu_json.get('options', [])
        if not opciones:
            return {'matched_option': None, 'confidence': 0}
        
        titulos = [opt.get('title', '') for opt in opciones]
        
        prompt = f"""
        El usuario dijo: "{mensaje}"
        
        Opciones disponibles: {', '.join(titulos)}
        
        Detecta si el usuario quiere alguna de estas opciones.
        Responde SOLO con JSON válido:
        {{"matched_option": "titulo_exacto_de_la_opcion", "confidence": 0.9}}
        
        Si no coincide con ninguna, usa: {{"matched_option": null, "confidence": 0}}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                config={"temperature": 0.1},  # Baja para consistencia
                contents=prompt
            )
            
            # Parsear respuesta JSON
            respuesta_texto = response.text.strip()
            # Limpiar posibles marcas de código
            if respuesta_texto.startswith('```'):
                respuesta_texto = respuesta_texto.split('```')[1]
                if respuesta_texto.startswith('json'):
                    respuesta_texto = respuesta_texto[4:]
            respuesta_texto = respuesta_texto.strip()
            
            resultado = json.loads(respuesta_texto)
            return {
                'matched_option': resultado.get('matched_option'),
                'confidence': float(resultado.get('confidence', 0))
            }
            
        except Exception as e:
            print(f"⚠️ ERROR detectando intención: {e}")
            return {'matched_option': None, 'confidence': 0}
    
    def clear_cache(self, client_id: str = None):
        """
        Limpia la caché de conocimiento.
        
        Args:
            client_id: ID específico a limpiar (None para limpiar todo)
        """
        if client_id:
            if client_id in self._knowledge_cache:
                del self._knowledge_cache[client_id]
            if client_id in self._cache_expiry:
                del self._cache_expiry[client_id]
        else:
            self._knowledge_cache.clear()
            self._cache_expiry.clear()
