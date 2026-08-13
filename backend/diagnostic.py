import traceback
try:
    from syncsphere.presentation.api.v1 import v1_router
    for r in v1_router.routes:
        if hasattr(r, "path"):
            print("V1 ROUTE:", r.path)
        else:
            print("V1 ROUTE HAS NO PATH:", getattr(r, "path", r))
except Exception as e:
    print("FAILED TO IMPORT V1 ROUTER:")
    traceback.print_exc()

try:
    from syncsphere.main import app
    print(f"App created successfully, {len(app.routes)} routes.")
except Exception as e:
    print("FAILED TO IMPORT APP:")
    traceback.print_exc()
