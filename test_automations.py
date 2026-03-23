#!/usr/bin/env python3
"""
Test manual de las automatizaciones
Para probar sin Cloud Scheduler
"""

import requests
import sys

# URLs de las funciones (actualiza con tu URL real)
FOLLOWUP_URL = "https://us-central1-zotek-ia.cloudfunctions.net/followup_cold_leads"
REMINDER_URL = "https://us-central1-zotek-ia.cloudfunctions.net/appointment_reminders"

def test_followup():
    """Prueba follow-up de leads fríos"""
    print("\n=== PROBANDO FOLLOW-UP DE LEADS FRIOS ===")
    try:
        response = requests.post(FOLLOWUP_URL, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

def test_reminder():
    """Prueba recordatorio de citas"""
    print("\n=== PROBANDO RECORDATORIO DE CITAS ===")
    try:
        response = requests.post(REMINDER_URL, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("\n╔════════════════════════════════════════╗")
    print("║  ZOTEK IA - TEST AUTOMATIZACIONES    ║")
    print("╚════════════════════════════════════════╝")
    
    print("\n1. Test Follow-up de Leads Fríos")
    print("2. Test Recordatorio de Citas")
    print("3. Test Ambos")
    
    choice = input("\nElige una opción (1-3): ").strip()
    
    if choice == "1":
        test_followup()
    elif choice == "2":
        test_reminder()
    elif choice == "3":
        test_followup()
        test_reminder()
    else:
        print("Opción inválida")
        sys.exit(1)
    
    print("\n✅ Tests completados. Revisa los logs en Cloud Console para más detalles.")
    print("https://console.cloud.google.com/logs?project=zotek-ia")
