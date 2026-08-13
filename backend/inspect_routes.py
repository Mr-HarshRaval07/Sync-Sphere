from fastapi import FastAPI
from fastapi.routing import APIRoute
from syncsphere.presentation.api.v1 import v1_router

app = FastAPI()
app.include_router(v1_router)

resolved_routes = []
for route in app.routes:
    if isinstance(route, APIRoute):
        methods = ", ".join(route.methods) if route.methods else "None"
        resolved_routes.append(f"{methods} {route.path}")

with open("inspect_routes.txt", "w") as f:
    for rr in sorted(resolved_routes):
        f.write(rr + "\n")
