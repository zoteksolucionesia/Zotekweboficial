from google import genai
from google.genai import types
import os
import time
import traceback
from .. import database  # Relative import within src package

class GeminiEngine:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

    def generar_respuesta(self, mensaje_usuario, client_data, numero_telefono):
        """Genera una respuesta inteligente basada en el contexto del cliente y su base de conocimientos."""
        
        client_id = client_data['id']
        nombre_cliente = client_data['name']
        
        # 1. Recuperar conocimiento específico del PDF/DB
        conocimiento = database.get_client_knowledge(client_id)
        
        # 2. Configurar la instrucción maestra con el contexto dinámico
        # Si el cliente tiene instrucciones personalizadas, las usamos. Si no, usamos una por defecto.
        instrucciones_base = client_data.get('system_instruction') or f"Eres un asistente para {nombre_cliente}. Sé amable, breve y profesional."
        
        prompt_sistema = f"""
        {instrucciones_base}
        
        Usa el siguiente CONOCIMIENTO para responder si es relevante:
        
        REGLAS IMPORTANTES:
        1. Si la respuesta contiene varios puntos, servicios o categorías que el usuario puede elegir, NO escribas una lista larga. 
        2. En su lugar, escribe una breve introducción y luego añade el tag [OPCIONES] seguido de las opciones separadas por '|'.
        3. Cada opción debe ser corta (máximo 20 caracteres).
        4. Ejemplo: "Claro, estos son nuestros servicios: [OPCIONES]: Limpieza | Ortodoncia | Blanqueamiento"
        5. Máximo 10 opciones. SIEMPRE prioriza brevedad.
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    config={
                        "system_instruction": prompt_sistema,
                        "temperature": 0.5,
                    },
                    contents=mensaje_usuario
                )
                return response.text

            except Exception as e:
                error_str = str(e)
                if ("503" in error_str or "429" in error_str) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ Reintentando Gemini ({attempt+1}/{max_retries}) en {wait_time}s por error: {error_str[:50]}...")
                    time.sleep(wait_time)
                    continue
                
                error_msg = f"💀 ERROR GEMINI ({type(e).__name__}): {error_str}\n{traceback.format_exc()}"
                print(error_msg)
                # Ensure logs directory exists if logging to file
                return "Lo siento, tuve un problema procesando tu mensaje. ¿Puedes repetirlo?"

        return "Lo siento, tuve un problema procesando tu mensaje. ¿Puedes repetirlo?"
