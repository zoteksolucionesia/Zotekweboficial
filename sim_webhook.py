import requests
import json
import time

payload = {
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "12345",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "52155555555",
              "phone_number_id": "980996958435648"
            },
            "contacts": [
              {
                "profile": {
                  "name": "Test User"
                },
                "wa_id": "5212345678"
              }
            ],
            "messages": [
              {
                "from": "5212345678",
                "id": "wamid.HBgLNTIyMzEyMTI2MDMVAgASGCAyOTQyREUzNEFCOTFENEU0MDU3NTUxMkJGRjE2NDkxMgA=" + str(time.time()),
                "timestamp": str(int(time.time())),
                "type": "text",
                "text": {
                  "body": "quiero probar la demo de Restaurante"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}

print("Testing starting demo...")
resp = requests.post("https://zotek-ia.web.app/webhook", json=payload)
print(resp.status_code, resp.text)

time.sleep(2)
print("Testing interactive reply for demo...")
payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "Hola"
payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = "wamid.2" + str(time.time())
resp2 = requests.post("https://zotek-ia.web.app/webhook", json=payload)
print(resp2.status_code, resp2.text)
