import requests
from jose import jwt
from datetime import datetime, timedelta

# Default secret from main.py if .env isn't set
SECRET_KEY = "ZOTEK_SECRET_DEFAULT_CHANGE_ME"
ALGORITHM = "HS256"

# Create valid admin JWT
to_encode = {"sub": "zoteksolucionesia@gmail.com", "role": "admin"}
expire = datetime.utcnow() + timedelta(hours=1)
to_encode.update({"exp": expire})
access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

headers = {"Authorization": f"Bearer {access_token}"}
base_url = "https://zotek-ia.web.app/api/clients"

for d_id in ["demo_restaurante", "demo_clinica", "demo_tienda"]:
    resp = requests.post(f"{base_url}/{d_id}/reset", headers=headers)
    print(f"Reset {d_id}: status={resp.status_code}, {resp.text}")

