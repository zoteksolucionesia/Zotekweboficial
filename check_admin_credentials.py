import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("CREDENCIALES DE ADMIN EN .env")
print("="*60)

admin_email = os.getenv("ADMIN_EMAIL", "zoteksolucionesia@gmail.com")
admin_password = os.getenv("ADMIN_PASSWORD", "Zotek!SecureAdmin9X$2026")
secret_key = os.getenv("SECRET_KEY", "ZotekSeguro2026")

print(f"\nADMIN_EMAIL: {admin_email}")
print(f"ADMIN_PASSWORD: {admin_password}")
print(f"SECRET_KEY: {secret_key}")

print("\n" + "="*60)
print("INTENTA LOGIN CON:")
print("="*60)
print(f"  Email: {admin_email}")
print(f"  Password: {admin_password}")
print("="*60)
