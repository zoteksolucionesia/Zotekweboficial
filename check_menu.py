from functions.src.database import get_db
import traceback

try:
    db = get_db()
    
    print("--- Client: Zotek Soluciones IA ---")
    doc = db.collection('clients').document('Zotek Soluciones IA').get()
    print("Main Data:", doc.to_dict())
    
    menu = db.collection('clients').document('Zotek Soluciones IA').collection('config').document('menu').get()
    print("Menu Data:", menu.to_dict() if menu.exists else "NO MENU")

except Exception as e:
    traceback.print_exc()
