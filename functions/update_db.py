import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Initialize Firebase (it might already be initialized if imported from database.py)
try:
    firebase_admin.initialize_app()
except ValueError:
    pass

db = firestore.client()

def update_menu():
    print("Updating Salon de Belleza menu...")
    client_id = "1"
    
    menu_ref = db.collection('clients').document(client_id).collection('config').document('menu')
    menu_doc = menu_ref.get()
    
    if not menu_doc.exists:
        print("Menu doc not found!")
        return

    menu_data = menu_doc.to_dict()
    
    # 1. Update the main text
    old_text = menu_data.get('text', '')
    new_text = "¡Hola! Bienvenido al Salon de Belleza. 👋\n\n¿En qué podemos ayudarte hoy? Selecciona una opción del menú:"
    menu_data['text'] = new_text
    print(f"Updated text: '{old_text}' -> '{new_text}'")
    
    # 2. Update service options if they mention Zotek
    options = menu_data.get('options', [])
    updated_options = []
    for opt in options:
        if isinstance(opt, dict):
            if 'response' in opt:
                opt['response'] = opt['response'].replace("Zotek", "nuestro salón")
            if opt.get('submenu') and 'options' in opt['submenu']:
                for sub_opt in opt['submenu']['options']:
                    if isinstance(sub_opt, dict) and 'response' in sub_opt:
                        sub_opt['response'] = sub_opt['response'].replace("Zotek", "nuestro salón")
        updated_options.append(opt)
    
    menu_data['options'] = updated_options
    
    # 3. Save back to Firestore
    menu_ref.set(menu_data)
    print("Firestore menu updated successfully!")

if __name__ == "__main__":
    update_menu()
