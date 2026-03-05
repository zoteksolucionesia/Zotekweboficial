import firebase_admin
from firebase_admin import credentials, firestore

def add_example_clients():
    cred = credentials.Certificate('service-account-key.json')
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
        
    db = firestore.client()
    
    examples = [
        {
            "id": "demo_restaurante",
            "name": "Restaurante La Trattoria",
            "email": "restaurante@ejemplo.com",
            "phone_number_id": "demo_123",
            "is_active": True,
            "menu": {
                "text": "¡Bienvenido a *La Trattoria*! 👋 Soy tu asistente virtual. ¿Qué te gustaría hacer hoy?",
                "options": [
                    {"title": "Ver Menú", "icon": "🍕", "response": "Nuestro menú incluye pizzas a la leña, pastas frescas y postres italianos."},
                    {"title": "Hacer Reserva", "icon": "📅", "response": "Indícanos la fecha y hora para verificar disponibilidad."},
                    {"title": "Horarios", "icon": "⏰", "response": "Estamos abiertos todos los días de 12:00 PM a 11:00 PM."}
                ],
                "fallback_text": "Lo siento, no entendí eso. Aquí tienes las opciones principales de La Trattoria:"
            }
        },
        {
            "id": "demo_clinica",
            "name": "Clínica San Juan",
            "email": "clinica@ejemplo.com",
            "phone_number_id": "demo_456",
            "is_active": True,
            "menu": {
                "text": "Bienvenido a la *Clínica San Juan*. 🏥 ¿En qué podemos ayudarte hoy?",
                "options": [
                    {"title": "Agendar Cita", "icon": "📅", "response": "Por favor, dinos para qué especialidad buscas cita."},
                    {"title": "Especialidades", "icon": "👨‍⚕️", "response": "Contamos con Medicina General, Odontología y Pediatría."},
                    {"title": "Ubicación", "icon": "📍", "response": "Estamos en Av. Central #123. Haz clic aquí para ver en el mapa: https://maps.google.com"}
                ],
                "fallback_text": "No comprendo tu solicitud. Selecciona una de estas opciones de la clínica:"
            }
        },
        {
            "id": "demo_tienda",
            "name": "Moda Urbana",
            "email": "tienda@ejemplo.com",
            "phone_number_id": "demo_789",
            "is_active": True,
            "menu": {
                "text": "¡Hola! Bienvenido a *Moda Urbana*. 🛍️ ✨ ¿Cómo podemos ayudarte con tu estilo hoy?",
                "options": [
                    {"title": "Ver Catálogo", "icon": "👕", "response": "Nuestra nueva colección de otoño ya está disponible."},
                    {"title": "Tallas", "icon": "📏", "response": "Manejamos tallas desde XS hasta XL en la mayoría de nuestras prendas."},
                    {"title": "Devoluciones", "icon": "🔄", "response": "Tienes 30 días para realizar cambios o devoluciones con tu ticket."}
                ],
                "fallback_text": "Ups, no reconozco eso. Aquí tienes lo que puedo hacer por ti en Moda Urbana:"
            }
        }
    ]
    
    for client in examples:
        client_id = client["id"]
        menu_data = client.pop("menu")
        
        print(f"Adding client: {client['name']}...")
        db.collection('clients').document(client_id).set(client, merge=True)
        
        print(f"Adding menu for {client['name']}...")
        db.collection('clients').document(client_id).collection('config').document('menu').set(menu_data)
        
    print("✅ Example clients added successfully.")

if __name__ == "__main__":
    add_example_clients()
