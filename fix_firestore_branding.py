
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase with default credentials
try:
    firebase_admin.initialize_app()
    print("Firebase initialized with default credentials.")
except Exception as e:
    print(f"Failed to initialize with default credentials: {e}")
    # Fallback to local key if we can find it
    try:
        cred = credentials.Certificate("c:/Users/USUARIO/ZotekSolucionesIA/functions/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("Firebase initialized with serviceAccountKey.json.")
    except Exception as e2:
        print(f"All initialization attempts failed. Error: {e2}")
        exit(1)

db = firestore.client()

doc_path = "clients/1/config/menu"
doc_ref = db.document(doc_path)

new_data = {
    "text": "¡Hola! Bienvenido al Salón de Belleza. 👋\n\nA continuación te ofrecemos lo siguiente. Para regresar al menú anterior, solo escribe 'menú'.",
    "options": [
        {
            "title": "Servicios",
            "submenu": {
                "text": "Selecciona una opción:",
                "options": [
                    {
                        "title": "Corte de Cabello",
                        "response": "Ofrecemos cortes modernos para dama y caballero."
                    },
                    {
                        "title": "Peinados",
                        "response": "Peinados para eventos especiales y del diario."
                    },
                    {
                        "title": "Tratamientos",
                        "response": "Hidratación profunda y cuidado capilar profesional."
                    }
                ]
            }
        },
        {"title": "Agendar Cita", "response": "Por favor llama al teléfono 333-4444-5555 o usa nuestro Calendly: {{calendly_url}}"},
        {"title": "Pago", "response": "Aceptamos efectivo y transferencias bancarias."},
        {"title": "Contacto", "response": "Escríbenos a nuestro WhatsApp o llámanos directamente."}
    ]
}

doc_ref.set(new_data)
print(f"Firestore document '{doc_path}' updated successfully.")
