from syncsphere.main import app

def print_routes(routes, prefix=""):
    for r in routes:
        if hasattr(r, "routes"):
            print_routes(r.routes, prefix + getattr(r, "path", ""))
        elif hasattr(r, "path"):
            print(f"ROUTE: {prefix}{r.path} [{getattr(r, 'name', '')}]")
        else:
            print(f"OTHER ROUTE: {r}")

print("---------- APP ROUTES ----------")
print_routes(app.routes)
