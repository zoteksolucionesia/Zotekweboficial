import httpx

url = "https://zotek-ia.web.app/api/appointments/token/c7b412cf-f08f-4e56-ba42-725dc88968c8"
try:
    r = httpx.get(url)
    print("Status:", r.status_code)
    print("Headers:", r.headers)
    print("Body:", r.text)
except Exception as e:
    print("Request failed:", e)
