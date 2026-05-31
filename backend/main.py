from fastapi import FastAPI

app = FastAPI()

# @app.get("/")
# def home():
#     return {"message": "Sync Sphere Backend Running"}
@app.get("/test")
def test():
    return {"message": "Hello from FastAPI"}