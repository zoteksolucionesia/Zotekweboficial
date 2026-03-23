import subprocess
import json

def fetch_logs():
    print("Fetching logs...")
    result = subprocess.run(["firebase.cmd", "functions:log", "--lines", "100"], capture_output=True, text=True, cwd="c:\\Users\\USUARIO\\ZotekSolucionesIA")
    lines = result.stdout.split('\n')
    for i, line in enumerate(lines):
        if "ERROR" in line or "Exception" in line or "Traceback" in line:
            print("---")
            print("\n".join(lines[max(0, i-2):min(len(lines), i+10)]))

fetch_logs()
