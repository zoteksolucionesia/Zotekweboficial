import src.database as db
import json

# ID del bot maestro de Zotek Soluciones IA
ZOTEK_BOT_ID = 10

system_instruction = """Eres el Agente Maestro de Zotek Soluciones IA, nuestra plataforma líder en automatización de negocios con IA. 🚀

Tu objetivo es demostrar cómo la IA puede transformar cualquier negocio. Eres experto en:
1. 🍕 Automatización para Restaurantes (Menús interactivos y reservas).
2. 🏥 Soluciones Médicas (Gestión de citas y recordatorios).
3. 🛍️ E-commerce y Retail (Catálogos inteligentes y raseo de pedidos).
4. 🧠 Soluciones Personalizadas (Diseñamos el cerebro de tu empresa).

Nuestros Planes Principales:
- ⭐️ FREE: 100 mensajes/mes y base de conocimientos básica.
- ⚡️ PRO ($79 USD): 10,000 mensajes, soporte prioritario e integración avanzada con PDFs.
- 🏢 ENTERPRISE: Ilimitado, entrenamiento personalizado y consultoría 1-a-1.

Responde siempre con entusiasmo, usa emojis para que la lectura sea amena y mantén un tono profesional pero muy innovador. Si preguntan por los demos, diles que pueden escribir 'demo restaurante', 'demo clinica', 'demo tienda', 'demo dental' o 'demo psicologo'."""

menu_json = {
    "text": "¡Hola! Bienvenido al canal oficial de *Zotek Soluciones IA* 🚀. Soy tu asistente experto para la transformación digital de tu negocio.\n\n¿Qué te gustaría explorar hoy?",
    "options": [
        {
            "title": "Nuestras Soluciones",
            "icon": "🚀",
            "submenu": {
                "text": "Elegimos el modelo perfecto para tu industria:",
                "options": [
                    {"title": "Restaurantes 🍕", "response": "Optimiza tu atención con menús digitales y reservas automáticas 24/7."},
                    {"title": "Salud 🏥", "response": "Agiliza tu clínica con gestión de citas y atención al paciente sin esperas."},
                    {"title": "E-commerce 🛍️", "response": "Vende más con catálogos en WhatsApp y rastreo de envíos automático."}
                ]
            }
        },
        {
            "title": "Planes y Precios",
            "icon": "💰",
            "response": "Tenemos el plan ideal para cada etapa:\n\n- *Zotek Free:* $0 (100 msgs)\n- *Zotek Pro:* $79/mes (10,000 msgs)\n- *Zotek Enterprise:* (Ilimitado)\n\n¿Deseas que un consultor te contacte para elegir el mejor?"
        },
        {
            "title": "Probar Demos",
            "icon": "🧪",
            "response": "¡Claro! Escribe cualquiera de estas palabras para activar un bot especializado:\n\n- 'Demo Restaurante'\n- 'Demo Clínica'\n- 'Demo Tienda'\n- 'Demo Dental'\n- 'Demo Psicólogo'\n\n*Nota:* Al terminar, escribe 'SALIR' para volver a hablar conmigo."
        },
        {
            "title": "Hablar con Humano",
            "icon": "📞",
            "response": "¡Perfecto! Un consultor experto se pondrá en contacto contigo en breve para analizar tu proyecto personalmente."
        }
    ],
    "fallback_text": "Lo siento, no entendí esa opción. Por favor, selecciona una de las opciones del menú principal para ayudarte mejor."
}

data = {
    "name": "Zotek Soluciones IA (Official)",
    "system_instruction": system_instruction,
    "menu_json": menu_json
}

if db.update_client(ZOTEK_BOT_ID, data):
    print("✅ Zotek SaaS Bot updated successfully.")
else:
    print("❌ Failed to update Zotek SaaS Bot.")
