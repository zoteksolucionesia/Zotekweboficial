import requests
import json

WEBHOOK_URL = "https://api-handler-gfd2ph2qpq-uc.a.run.app/webhook"

# Simular mensaje de demo restaurante
payload = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "123456",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {
                    "display_phone_number": "980996958435648",
                    "phone_number_id": "980996958435648"
                },
                "messages": [{
                    "from": "5219991234567",
                    "id": "wamid.test_demo_123",
                    "timestamp": "1710778100",
                    "type": "text",
                    "text": {
                        "body": "demo restaurante"
                    }
                }]
            },
            "field": "messages"
        }]
    }]
}

print("Enviando mensaje 'demo restaurante' al webhook...")
response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("\n✅ Webhook respondió correctamente")
    print("   Si no llego el mensaje a WhatsApp, el problema es:")
    print("   1. El token de WhatsApp no es válido")
    print("   2. El phone_number_id no está configurado en Meta")
    print("   3. Meta no está entregando los mensajes reales")
else:
    print(f"\n❌ Error: {response.status_code}")
