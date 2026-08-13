import urllib.request
import json
import traceback

def test_tasks():
    try:
        # First register/login to get token
        base_url = "http://localhost:8000"
        
        req = urllib.request.Request(f"{base_url}/v1/auth/register", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"email":"test3@example.com","password":"password123","first_name":"test","last_name":"test"}).encode('utf-8')
        try:
            urllib.request.urlopen(req, data=data)
        except Exception:
            pass # might already exist
            
        req = urllib.request.Request(f"{base_url}/v1/auth/login", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"email":"test3@example.com","password":"password123"}).encode('utf-8')
        resp = urllib.request.urlopen(req, data=data)
        resp_json = json.loads(resp.read())
        token = resp_json['data']['access_token']
        
        # Test tasks endpoint
        req = urllib.request.Request(f"{base_url}/v1/tasks", method="GET")
        req.add_header('Authorization', f'Bearer {token}')
        
        print("Sending request to /v1/tasks...")
        resp = urllib.request.urlopen(req)
        print("HTTP", resp.getcode())
        print("Response body:")
        print(resp.read().decode('utf-8'))
        
    except Exception as e:
        print("ERROR:", traceback.format_exc())

if __name__ == '__main__':
    test_tasks()
