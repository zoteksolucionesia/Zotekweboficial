import sys
sys.stdout.reconfigure(encoding='utf-8')
with open("functions/src/main.py", "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        if "webhook" in line.lower() or "def " in line.lower() and ("status" in line.lower() or "whatsapp" in line.lower()):
            print(f"{line_num}: {line.strip()}")
