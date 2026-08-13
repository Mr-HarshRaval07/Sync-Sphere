import sys
import os
import json

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from syncsphere.main import app
from fastapi.routing import APIRoute

def dump_routes():
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(f"{','.join(route.methods)} {route.path}")
        elif hasattr(route, 'path'):
            routes.append(f"{route.path}")
        else:
            routes.append(str(route))
    
    with open("backend-routes-dump.txt", "w", encoding="utf-8") as f:
        for r in sorted(routes):
            f.write(r + "\n")
            
    print("Dumped routes to backend-routes-dump.txt")

if __name__ == "__main__":
    dump_routes()
