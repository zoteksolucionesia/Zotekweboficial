import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from functions.src.database import get_client_by_phone_id
from functions.src.services.whatsapp_service import enviar_template_whatsapp

zob = get_client_by_phone_id("980996958435648")
if not zob:
    print("Error: Zotek client not found in DB!")
    sys.exit(1)

wa_token = zob.get("whatsapp_token")
wa_phone_id = zob.get("phone_number_id")

if not wa_token or not wa_phone_id:
    print("Error: Missing WhatsApp token or phone number ID!")
    sys.exit(1)

variables = ["Omar Test", "Zotek Soluciones IA", "Lunes, 01 de Junio de 2026", "12:00 PM"]
to_phone = "523123173431"

print(f"Sending test template to {to_phone}...")
success = enviar_template_whatsapp(
    phone_number_id=wa_phone_id,
    whatsapp_token=wa_token,
    to_phone=to_phone,
    template_name="zotek_confirmacion_cita_v2",
    variables=variables,
    language="es_MX",
    url_suffix="cita?t=test-token-uuid-1234"
)
print(f"Result: {success}")
