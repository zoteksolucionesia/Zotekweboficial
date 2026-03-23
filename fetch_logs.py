import subprocess

result = subprocess.run(["firebase.cmd", "functions:log", "--lines", "100"], capture_output=True)
try:
    stdout = result.stdout.decode('utf-8')
except Exception:
    stdout = result.stdout.decode('cp1252', errors='replace')

with open("logs_output.txt", "w", encoding="utf-8") as f:
    f.write(stdout)
