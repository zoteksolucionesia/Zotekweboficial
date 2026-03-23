# DEMO TEST - Script para probar si los demos funcionan

import requests
import json

WEBHOOK_URL = "https://api-handler-gfd2ph2qpq-uc.a.run.app/webhook"

print("="*70)
print("PRUEBA DE DEMOS")
print("="*70)

# Test 1: demo restaurante
print("\n1. Enviando 'demo restaurante'...")
payload1 = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "123",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"display_phone_number": "980996958435648", "phone_number_id": "980996958435648"},
                "messages": [{"from": "5219999999999", "id": "test1", "timestamp": "1234567890", "type": "text", "text": {"body": "demo restaurante"}}]
            },
            "field": "messages"
        }]
    }]
}

r1 = requests.post(WEBHOOK_URL, json=payload1, timeout=30)
print(f"   Respuesta: {r1.text}")

# Test 2: demo dental
print("\n2. Enviando 'demo dental'...")
payload2 = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "123",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"display_phone_number": "980996958435648", "phone_number_id": "980996958435648"},
                "messages": [{"from": "5219999999998", "id": "test2", "timestamp": "1234567891", "type": "text", "text": {"body": "demo dental"}}]
            },
            "field": "messages"
        }]
    }]
}

r2 = requests.post(WEBHOOK_URL, json=payload2, timeout=30)
print(f"   Respuesta: {r2.text}")

print("\n" + "="*70)
print("Si las respuestas son {'status':'ok'}, el webhook funciona pero NO envia mensajes.")
print("Si las respuestas son {'status':'demo_started'}, el webhook SÍ detecta los demos.")
print("="*70)
