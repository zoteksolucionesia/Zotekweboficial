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
    system_instruction = """Eres un asistente de Zotek SolucionesIA, una agencia especializada en soluciones de inteligencia artificial y automatización empresarial.

🤖 SERVICIOS DE ZOTEK:

1. 💼 **Desarrollo de Software a la Medida**
   - Soluciones personalizadas según tus necesidades específicas
   - Arquitectura escalable y mantenible
   - Tecnologías modernas y best practices

2. ⚙️ **Soluciones IS para Automatizar tu Negocio**
   - Reducción de procesos manuales
   - Aumento de eficiencia operacional
   - Integración de sistemas empresariales

3. 🤖 **Desarrollo de Bots Inteligentes**
   - Chatbots conversacionales con IA
   - Bots de WhatsApp para atención al cliente
   - Asistentes virtuales personalizados
   - Automatización de procesos repetitivos

4. 📚 **Capacitación en el Uso de la IA**
   - Entrenamientos para tu equipo
   - Uso práctico de herramientas de IA
   - Implementación de soluciones inteligentes
   - Mejora de productividad con IA

🎯 **NUESTRA MISIÓN:**
Transformar tu negocio a través de la IA y la automatización inteligente, permitiéndote enfocarte en lo que realmente importa.

💡 **BENEFICIOS:**
✅ Reducción de costos operacionales
✅ Mejora en atención al cliente
✅ Automatización de procesos
✅ Toma de decisiones más inteligente
✅ Escalabilidad empresarial

Responde de manera profesional pero amigable. Ofrece información clara sobre nuestros servicios y cómo podemos ayudar al usuario. Siempre invita a explorar más opciones."""

    # Menú JSON personalizado
    menu_json = {
        "text": "¡Hola! 👋 Bienvenido a **Zotek SolucionesIA**\n\nSomos una agencia especializada en **Soluciones de IA y Automatización Empresarial**.\n\nTe ayudamos a transformar tu negocio a través de tecnología inteligente.\n\n¿Qué te interesa conocer?",
        "buttons": [
            {
                "type": "reply",
                "reply": {
                    "id": "1",
                    "title": "💼 Nuestros Servicios"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "2",
                    "title": "🤖 Casos de Uso"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "3",
                    "title": "📞 Contacto"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "4",
                    "title": "💡 Preguntas Frecuentes"
                }
            }
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
