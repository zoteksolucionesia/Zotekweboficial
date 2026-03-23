import json

lines = open('logs.json', encoding='utf-16le', errors='replace').read().split('\n')
errs = []

# Because `firebase functions:log --json` dumps newline-separated JSON objects
for line in lines:
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
        textPayload = data.get('textPayload', '')
        # check if word ERROR or Exception or Traceback
        if 'Traceback' in textPayload or 'ERROR' in textPayload or 'Exception' in textPayload or 'Exception' in line or 'Traceback' in line:
            errs.append(textPayload or line)
    except Exception:
        # if not JSON
        if 'Traceback' in line or 'ERROR' in line or 'Exception' in line:
            errs.append(line)

with open('real_errors.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(errs))
