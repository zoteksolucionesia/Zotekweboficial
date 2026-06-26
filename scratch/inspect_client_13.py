import sys
sys.path.insert(0, '.')
from functions.src.database import get_client_by_id

client = get_client_by_id(13)
print("Client 13 details:")
if client:
    for k, v in client.items():
        if k not in ['whatsapp_token', 'stripe_api_key']: # exclude sensitive
            print(f"{k}: {type(v)} - {str(v)[:100]}")
else:
    print("Client 13 not found!")
