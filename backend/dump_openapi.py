import sys
import os
import json

app_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(app_dir, 'src'))

from syncsphere.main import app

def dump_openapi_paths():
    openapi_schema = app.openapi()
    paths = list(openapi_schema.get("paths", {}).keys())
    with open("backend_openapi_paths.txt", "w", encoding="utf-8") as f:
        for path in sorted(paths):
            f.write(path + "\n")
            
    print("Dumped OpenAPI paths to backend_openapi_paths.txt")

if __name__ == "__main__":
    dump_openapi_paths()
