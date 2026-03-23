import subprocess

# Trying to get the logs without formatting messing up on windows
cmd = "firebase.cmd functions:log --lines 200"
print(f"Executing: {cmd}")
proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = proc.communicate()

try:
    stdout_str = out.decode('utf-8', errors='replace')
except Exception:
    stdout_str = out.decode('cp1252', errors='replace')

# Filter for CRITICAL ERROR or traceback
lines = stdout_str.split("\n")
err_lines = []
for i, line in enumerate(lines):
    if "ERROR" in line or "Traceback" in line or "Exception" in line:
        start = max(0, i-5)
        end = min(len(lines), i+15)
        err_lines.extend(lines[start:end])
        err_lines.append("---")

with open("firebase_errors.txt", "w", encoding="utf-8") as f:
    if err_lines:
        f.write("\n".join(err_lines))
    else:
        f.write("No typical error keywords found.\n")
        # Just write the last 50 lines to see something
        f.write("\n".join(lines[-50:]))
