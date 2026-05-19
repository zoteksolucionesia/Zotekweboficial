"""
Script para actualizar el contexto y menú de Zotek Soluciones IA en la BD
"""
import sys
import os
import json
import io
from pathlib import Path

# Configurar stdout para UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Agregar la ruta de functions/src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "functions"))

from src import database

def update_zotek_context():
    """Actualiza el cliente Zotek con menú y system_instruction personalizados."""

    # System Instruction personalizado para Zotek
    system_instruction = """Eres el asistente virtual de Zotek SolucionesIA, una agencia especializada en inteligencia artificial y automatización empresarial.

━━━━━━━━━━━━━━━━━━━━━━━
🧭 GUÍA DE NAVEGACIÓN
━━━━━━━━━━━━━━━━━━━━━━━
El usuario puede en cualquier momento:
- Escribir *menú* o *hola* → regresa al menú principal
- Escribir *inicio* → reinicia la conversación desde el principio
- Escribir el nombre de cualquier servicio → información directa

Al finalizar CADA respuesta, recuérdalo con esta línea:
"↩️ Escribe *menú* para ver las opciones o cuéntame en qué más puedo ayudarte."

━━━━━━━━━━━━━━━━━━━━━━━
🤖 SERVICIOS DE ZOTEK
━━━━━━━━━━━━━━━━━━━━━━━

1. 💼 Desarrollo de Software a la Medida
   - Soluciones personalizadas según las necesidades del negocio
   - Arquitectura escalable y mantenible
   - Tecnologías modernas y mejores prácticas

2. ⚙️ Automatización de Procesos (IS/RPA)
   - Reducción de tareas manuales y errores
   - Aumento de eficiencia operacional
   - Integración entre sistemas empresariales

3. 🤖 Desarrollo de Bots Inteligentes
   - Chatbots conversacionales con IA (como este)
   - Bots de WhatsApp para atención al cliente 24/7
   - Asistentes virtuales personalizados por industria
   - Automatización de procesos repetitivos

4. 📚 Capacitación en IA
   - Entrenamientos prácticos para equipos de trabajo
   - Uso de herramientas de IA en el día a día
   - Implementación de soluciones inteligentes
   - Mejora de productividad con IA

━━━━━━━━━━━━━━━━━━━━━━━
🎯 MISIÓN Y BENEFICIOS
━━━━━━━━━━━━━━━━━━━━━━━
Misión: Transformar negocios a través de IA y automatización inteligente.

Beneficios clave:
✅ Reducción de costos operacionales
✅ Mejora en atención al cliente
✅ Automatización de procesos
✅ Toma de decisiones más inteligente
✅ Escalabilidad empresarial

━━━━━━━━━━━━━━━━━━━━━━━
📋 INSTRUCCIONES DE COMPORTAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━
- Responde de manera profesional y amigable
- Si el usuario pregunta algo que no está en tu contexto, ofrece conectarlos con el equipo humano
- Siempre termina invitando a explorar más o a regresar al menú
- Si el usuario parece perdido o confundido, recuérdale cómo navegar
- Para agendar una consulta o demo, indica que pueden escribir "contacto" o usar la opción del menú"""

    # Menú JSON — formato con "options" (lista de títulos que el bot convierte a botones/lista)
    menu_json = {
        "text": (
            "¡Hola! 👋 Bienvenido a *Zotek SolucionesIA*\n\n"
            "Somos una agencia especializada en *Soluciones de IA y Automatización Empresarial*. "
            "Te ayudamos a transformar tu negocio con tecnología inteligente.\n\n"
            "Elige una opción o escríbeme directamente 👇\n"
            "↩️ En cualquier momento escribe *menú* para volver aquí."
        ),
        "options": [
            {"title": "💼 Nuestros Servicios"},
            {"title": "🤖 Ver Demo del Bot"},
            {"title": "📞 Contactar Asesor"},
            {"title": "💡 Preguntas Frecuentes"}
        ]
    }

    try:
        conn = database.get_connection()
        cursor = conn.cursor()

        # Actualizar el cliente Zotek
        cursor.execute("""
            UPDATE clients
            SET
                system_instruction = %s,
                menu_json = %s
            WHERE phone_number_id = %s
            RETURNING id, name, system_instruction, menu_json
        """, (
            system_instruction,
            json.dumps(menu_json),
            "980996958435648"
        ))

        result = cursor.fetchone()

        if result:
            print("✅ Zotek Soluciones IA actualizado correctamente!")
            print(f"\n📊 Detalles:")
            print(f"   ID: {result[0]}")
            print(f"   Nombre: {result[1]}")
            print(f"   ✓ System Instruction: {len(result[2])} caracteres")
            print(f"   ✓ Menú: {len(json.dumps(result[3]))} caracteres")
            print(f"\n🎯 Servicios configurados:")
            print("   ✓ Desarrollo de Software a la Medida")
            print("   ✓ Soluciones IS para Automatizar tu Negocio")
            print("   ✓ Desarrollo de Bots Inteligentes")
            print("   ✓ Capacitación en el Uso de la IA")
        else:
            print("❌ No se encontró el cliente Zotek")
            return False

        conn.commit()
        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_zotek_context()
    sys.exit(0 if success else 1)
