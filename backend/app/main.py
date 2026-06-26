from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to Sync Sphere 🚀"}

@app.get("/health")
def health():
    return {
        "status": "running",
        "project": "Sync Sphere"
    }