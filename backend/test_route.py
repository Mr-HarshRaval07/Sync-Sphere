import sys, os
from fastapi.testclient import TestClient

os.chdir('src')
sys.path.insert(0, os.getcwd())

from syncsphere.main import app

client = TestClient(app)
print("GET /v1/connect/status:", client.get("/v1/connect/status").status_code)
