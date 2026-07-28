import asyncio
from httpx import AsyncClient
import os
from dotenv import load_dotenv

async def test_gemini():
    load_dotenv()
    
    # Check credentials
    print("=== Environment Variables ===")
    vars_to_check = ['GEMINI_API_KEY','OPENROUTER_API_KEY', 'GEMINI_API', 'GOOGLE_API_KEY', 'SYNCSPHERE_LLM_API_KEY']
    api_key_used = None
    for var in vars_to_check:
        val = os.getenv(var)
        print(f" - {var}: {'[PRESENT]' if val else '[MISSING]'}")
        if val and not api_key_used:
            api_key_used = val
            
    print(f"\nProvider: {os.getenv('SYNCSPHERE_LLM_PROVIDER', 'gemini')}")
    model = os.getenv('SYNCSPHERE_LLM_MODEL', 'gemini-flash-latest')
    print(f"Model: {model}")
    
    if not api_key_used:
        print("No API key could be found!")
        return
        
    print("\n=== Direct Connection Test ===")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key_used}"
    
    payload = {
        "contents": [{
            "parts":[{"text": 'Return JSON with exactly:\n{\n  "test": "ok"\n}'}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    import time
    start = time.perf_counter()
    async with AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            elapsed = time.perf_counter() - start
            print(f"HTTP Status: {response.status_code}")
            print(f"Response Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                print("Valid JSON returned:")
                print(response.json())
            else:
                print("Response text:", response.text)
        except Exception as e:
            print(f"Direct connection failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
