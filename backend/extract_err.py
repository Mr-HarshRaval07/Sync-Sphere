import re
log = open('uvicorn_log.txt', encoding='utf-8').read()
errors = re.findall(r'ValidationError.*?(?=\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|$)', log, re.DOTALL)
if errors:
    last_err = errors[-1]
    import json
    lines = last_err.strip().split('\n')
    print("-----LAST ERROR-----")
    for l in lines[:15]:
        print(l)
    print("--------------------")
else:
    print("No errors found.")
