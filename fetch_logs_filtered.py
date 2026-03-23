import subprocess
import json

cmd = "firebase.cmd functions:log --lines 400"
proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = proc.communicate()

try:
    stdout_str = out.decode('utf-8', errors='replace')
except Exception:
    stdout_str = out.decode('cp1252', errors='replace')

lines = stdout_str.split("\n")
filtered = []
for i, line in enumerate(lines):
    if "16:31:" in line or "16:32:" in line or "ERROR" in line or "Traceback" in line:
        start = max(0, i-5)
        end = min(len(lines), i+15)
        filtered.extend(lines[start:end])
        filtered.append("---")

# remove duplicates while preserving order
seen = set()
unique_filtered = []
for item in filtered:
    if item not in seen:
        seen.add(item)
        unique_filtered.append(item)

with open("logs_output_filtered.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(unique_filtered))
