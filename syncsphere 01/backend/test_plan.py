import httpx
import jwt
import time

def main():
    secret = "supersecretjwtkeythatisthirtytwobyteslongtobesecure"
    algo = "HS256"
    org_id = "6a61d992676b5c9402828a20"
    user_id = "6a61d992676b5c9402828a1f" # dummy

    payload = {
        "sub": user_id,
        "org": org_id,
        "exp": int(time.time()) + 3600
    }
    
    token = jwt.encode(payload, secret, algorithm=algo)

    url = "http://localhost:8000/v1/tasks/plan-with-ai"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "prompt": "Create an onboarding system for a new engineer, setup a meeting in my google calendar, and announce them in the #engineering Slack channel"
    }

    print("Making request...")
    with httpx.Client(timeout=60) as client:
        try:
            resp = client.post(url, headers=headers, json=data)
            print("Status:", resp.status_code)
            print("Response:", resp.text)
        except Exception as e:
            print("Error connecting to backend:", e)

if __name__ == '__main__':
    main()
