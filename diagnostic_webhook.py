#!/usr/bin/env python3
"""
Test para verificar si WhatsApp está enviando mensajes al webhook
"""

import requests
import json
import time

WEBHOOK_URL = "https://api-handler-gfd2ph2qpq-uc.a.run.app/webhook"

# Simular mensaje REAL de WhatsApp
test_payload = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {
                    "display_phone_number": "980996958435648",
                    "phone_number_id": "980996958435648"
                },
                "messages": [{
                    "from": "5219991234567",  # Número de prueba
                    "id": "wamid.diagnostic_test",
                    "timestamp": str(int(time.time())),
                    "type": "text",
                    "text": {
                        "body": "hola"
                    }
                }]
            },
            "field": "messages"
        }]
    }]
}

print("="*70)
print("DIAGNOSTICO DE WEBHOOK")
print("="*70)
print(f"\nURL del webhook: {WEBHOOK_URL}")
print(f"\nEnviando mensaje de prueba...")

try:
    response = requests.post(
        WEBHOOK_URL,
        json=test_payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=test_signature"
        },
        timeout=30
    )
    
    print(f"\nRespuesta del servidor:")
    print(f"  Status Code: {response.status_code}")
    print(f"  Response Body: {response.text[:200]}")
    
    if response.status_code == 200:
        print(f"\n✅ El webhook está FUNCIONANDO correctamente")
        print(f"   Los mensajes se están procesando")
    else:
        print(f"\n⚠️ El webhook respondió con error: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Error de conexión: {e}")

print("\n" + "="*70)
print("POSIBLES PROBLEMAS:")
print("="*70)
print("""
1. Meta NO está enviando mensajes reales
   - Verifica que el webhook URL en Meta sea EXACTAMENTE:
     {WEBHOOK_URL}
   
2. El número de teléfono no está configurado en WhatsApp API
   - Verifica en Meta → WhatsApp → Configuración → Números de teléfono
   
3. El webhook está bloqueado por CORS o autenticación
   - Cloud Run debe permitir solicitudes sin autenticación
   
4. WhatsApp Business API no está conectado
   - Verifica en Meta → WhatsApp → Configuración → Webhooks
   - Debe decir 'Verificado' con check verde
""")

print("="*70)
