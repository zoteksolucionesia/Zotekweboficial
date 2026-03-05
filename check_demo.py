import firebase_admin
from firebase_admin import credentials, firestore
import json

cred = credentials.Certificate('ZotekSolucionesIA/functions/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = db.collection('clients').document('demo_clinica').get()
if doc.exists:
    print(json.dumps(doc.to_dict().get('menu', {}), indent=2))
else:
    print("No doc found")
