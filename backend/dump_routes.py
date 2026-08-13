from syncsphere.main import app
for route in app.routes:
    if hasattr(route, "path") and 'task' in route.path:
        print(f"{list(route.methods)} {route.path}")
