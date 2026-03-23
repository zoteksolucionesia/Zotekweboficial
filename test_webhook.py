#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el webhook de WhatsApp
"""

import requests
import json

# Configuración
WEBHOOK_URL = "https://api-handler-kiawqi4qxq-uc.a.run.app/webhook"
VERIFY_TOKEN = "MI_TOKEN_SECRETO_123"

def test_webhook_verification():
    """Prueba la verificación del webhook (GET request de Meta)"""
    print("="*60)
    print("PRUEBA DE VERIFICACION DEL WEBHOOK")
    print("="*60)
    
    # Meta envia un GET con estos parametros para verificar
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "123456789"
    }
    
    try:
        response = requests.get(WEBHOOK_URL, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n[OK] Webhook verificado correctamente!")
            return True
        else:
            print(f"\n[ERROR] Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error de conexion: {e}")
        return False


def test_webhook_message():
    """Prueba el envío de un mensaje al webhook"""
    print("\n" + "="*60)
    print("PRUEBA DE MENSAJE AL WEBHOOK")
    print("="*60)
    
    # Payload simulando un mensaje de WhatsApp
    payload = {
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
                        "from": "5219991234567",
                        "id": "wamid.test123",
                        "timestamp": "1710777600",
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
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=test"
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500] if response.text else 'Sin contenido'}")
        
        if response.status_code == 200:
            print("\n[OK] Mensaje procesado correctamente!")
            return True
        else:
            print(f"\n[WARNING] Response status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        return False


if __name__ == "__main__":
    print("Testing WhatsApp Webhook Configuration")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Verify Token: {VERIFY_TOKEN}")
    print("")
    
    # Prueba 1: Verificación
    test_webhook_verification()
    
    # Prueba 2: Mensaje
    test_webhook_message()
    
    print("\n" + "="*60)
    print("PRUEBAS COMPLETADAS")
    print("="*60)
