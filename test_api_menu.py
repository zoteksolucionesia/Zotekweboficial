from jose import jwt
from datetime import datetime, timedelta
import requests

SECRET_KEY = "ZotekSeguro2026"
ALGORITHM = "HS256"

def generate_token(email, role="admin", client_id=None):
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {"sub": email, "role": role, "client_id": client_id, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def test_menu_api(client_id):
    token = generate_token("zoteksolucionesia@gmail.com")
    url = f"https://zotek-ia.web.app/api/clients/{client_id}/menu"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing URL: {url}")
    resp = requests.get(url, headers=headers)
    
    print(f"Status Code: {resp.status_code}")
    try:
        print("Response Body:")
        import json
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except:
        print(f"Response (non-JSON): {resp.text}")

if __name__ == "__main__":
    test_menu_api("demo_clinica")
