#!/usr/bin/env python3
"""
Setup Cloud Scheduler for Zotek IA Automations

Este script configura Cloud Scheduler para ejecutar las automatizaciones:
1. Follow-up de leads fríos (cada hora)
2. Recordatorio de citas (cada día a las 10 AM)

Requisitos:
- gcloud CLI instalado y configurado
- Proyecto de Firebase seleccionado
"""

import subprocess
import sys
import os

# Configuración
PROJECT_ID = "zotek-ia"
REGION = "us-central1"
FUNCTION_BASE_URL = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net"

# Colores para output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'


def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{YELLOW}▶ {description}{RESET}")
    print(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"{GREEN}✓ {result.stdout}{RESET}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}✗ Error: {e.stderr}{RESET}")
        return False


def check_gcloud():
    """Verifica que gcloud esté instalado y configurado"""
    print(f"\n{GREEN}=== Verificando gcloud ==={RESET}")
    
    try:
        result = subprocess.run(["gcloud", "--version"], capture_output=True, text=True, check=True)
        print(f"✓ gcloud instalado: {result.stdout.split()[0]}")
        return True
    except:
        print(f"{RED}✗ gcloud no está instalado{RESET}")
        print("Instala desde: https://cloud.google.com/sdk/docs/install")
        return False


def setup_scheduler():
    """Configura Cloud Scheduler para las automatizaciones"""
    print(f"\n{GREEN}=== Configurando Cloud Scheduler ==={RESET}")
    
    # 1. Follow-up de leads fríos (cada hora)
    followup_command = [
        "gcloud", "scheduler", "jobs", "create", "http", "zotek-followup-cold-leads",
        "--schedule", "0 * * * *",  # Cada hora en minuto 0
        "--uri", f"{FUNCTION_BASE_URL}/followup_cold_leads",
        "--http-method", "POST",
        "--oidc-service-account-email", f"zotek-scheduler@{PROJECT_ID}.iam.gserviceaccount.com",
        "--oidc-token-audience", f"{FUNCTION_BASE_URL}/followup_cold_leads",
        "--location", REGION,
        "--time-zone", "America/Mexico_City"
    ]
    run_command(followup_command, "Creando scheduler para Follow-up de Leads Fríos (cada hora)")
    
    # 2. Recordatorio de citas (cada día a las 10 AM)
    reminder_command = [
        "gcloud", "scheduler", "jobs", "create", "http", "zotek-appointment-reminders",
        "--schedule", "0 10 * * *",  # Cada día a las 10:00
        "--uri", f"{FUNCTION_BASE_URL}/appointment_reminders",
        "--http-method", "POST",
        "--oidc-service-account-email", f"zotek-scheduler@{PROJECT_ID}.iam.gserviceaccount.com",
        "--oidc-token-audience", f"{FUNCTION_BASE_URL}/appointment_reminders",
        "--location", REGION,
        "--time-zone", "America/Mexico_City"
    ]
    run_command(reminder_command, "Creando scheduler para Recordatorio de Citas (diario 10 AM)")


def create_service_account():
    """Crea la service account para Cloud Scheduler"""
    print(f"\n{GREEN}=== Creando Service Account ==={RESET}")
    
    sa_command = [
        "gcloud", "iam", "service-accounts", "create", "zotek-scheduler",
        "--display-name", "Zotek IA Scheduler",
        "--project", PROJECT_ID
    ]
    run_command(sa_command, "Creando service account zotek-scheduler")


def main():
    """Función principal"""
    print(f"\n{GREEN}╔════════════════════════════════════════╗{RESET}")
    print(f"{GREEN}║  Zotek IA - Cloud Scheduler Setup     ║{RESET}")
    print(f"{GREEN}╚════════════════════════════════════════╝{RESET}")
    
    # Verificar gcloud
    if not check_gcloud():
        sys.exit(1)
    
    # Configurar proyecto
    print(f"\n{YELLOW}Configurando proyecto: {PROJECT_ID}{RESET}")
    subprocess.run(["gcloud", "config", "set", "project", PROJECT_ID])
    
    # Crear service account
    create_service_account()
    
    # Configurar schedulers
    setup_scheduler()
    
    print(f"\n{GREEN}╔════════════════════════════════════════╗{RESET}")
    print(f"{GREEN}║  ¡Configuración Completada!           ║{RESET}")
    print(f"{GREEN}╚════════════════════════════════════════╝{RESET}")
    
    print(f"\n{YELLOW}Próximos pasos:{RESET}")
    print("1. Verifica los schedulers en:")
    print(f"   https://console.cloud.google.com/cloudscheduler?project={PROJECT_ID}")
    print("\n2. Para probar manualmente:")
    print("   gcloud scheduler jobs run zotek-followup-cold-leads --location us-central1")
    print("   gcloud scheduler jobs run zotek-appointment-reminders --location us-central1")
    print("\n3. Para ver los logs:")
    print("   https://console.cloud.google.com/logs?project={PROJECT_ID}")


if __name__ == "__main__":
    main()
