import os
import re

patterns = {
    'localhost': r'localhost|127\.0\.0\.1',
    'secrets': r'mongodb\+srv|sk-[a-zA-Z0-9]{32,}|xoxb-[a-zA-Z0-9]+|ya29\.[a-zA-Z0-9_-]+',
    'cors': r'allow_origins\s*=\s*\[\s*\"\\*\"\s*\]',
    'mock': r'mock|dummy|fake'
}

for root, _, files in os.walk('.'):
    if any(x in root for x in ['node_modules', '.venv', '.git', '.next', '__pycache__']):
        continue
    for file in files:
        if file.endswith('.pyc') or file.endswith('.png'):
            continue
        path = os.path.join(root, file)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                for key, pattern in patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        print(f'Found {key} in {path}')
        except Exception as e:
            pass
