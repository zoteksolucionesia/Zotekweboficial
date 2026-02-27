import firebase_admin
from firebase_admin import credentials, firestore

def create_default_menu():
    phone_id = "980996958435648"
    
    try:
        cred = credentials.Certificate('service-account-key.json')
        # Use a fresh app or handle existing one
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred, {'projectId': 'zotek-ia'})
            
        db = firestore.client()
        
        print(f"Creating default menu in 'zotek-ia' for client {phone_id}...")
        
        # Ensure client document exists first (safety check)
        client_ref = db.collection('clients').document(phone_id)
        if not client_ref.get().exists:
            print(f"Warning: Client {phone_id} document not found. Creating it...")
            client_ref.set({
                "name": "Zotek Soluciones IA",
                "phone_number_id": phone_id,
                "email": "zoteksolucionesia@gmail.com",
                "system_instruction": "Eres greñita, la asistente virtual de Salón RM, estoy aquí para apoyarte en todas las dudas que tengas."
            }, merge=True)

        default_menu = {
            "text": "¡Hola! Bienvenid@ a Salón RM. 👋\n\n¿En qué puedo ayudarte?",
            "options": [
                {"title": "Servicios", "response": "Ofrecemos cortes, color, peinados y tratamientos capilares."},
                {"title": "Agendar Cita", "response": "Contáctanos al WhatsApp o llámanos para reservar tu espacio."},
                {"title": "Ubicación", "response": "Estamos ubicados en la zona centro. ¡Te esperamos!"}
            ]
        }
        
        db.collection('clients').document(phone_id).collection('config').document('menu').set(default_menu)
        print("✅ Default interactive menu created successfully.")
            
    except Exception as e:
        print(f"Error creating menu: {e}")

if __name__ == "__main__":
    create_default_menu()
