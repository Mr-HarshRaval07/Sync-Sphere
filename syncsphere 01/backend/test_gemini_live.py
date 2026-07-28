import sys, os, asyncio, httpx, json, time
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv('D:/syncsphere 01/syncsphere 01/backend/.env')
from syncsphere.core.config.settings import settings

api_key = settings.ai.llm_api_key.get_secret_value()
model_name = settings.ai.llm_model
model_clean = model_name if model_name.startswith('models/') else f'models/{model_name}'
gemini_url = f'https://generativelanguage.googleapis.com/v1beta/{model_clean}:generateContent?key={api_key}'

TEST_PROMPT = (
    "Launch the SyncSphere website on August 15, 2026. Complete the development work by August 10, 2026. "
    "Make it high priority and assign it to Janhvi. Create a GitHub issue for the development team, "
    "notify my team in Slack, send the launch plan to jayant32@gmail.com, schedule a launch meeting on "
    "August 14, 2026 at 10 AM, and add the project name, deadline, priority, and status to my Google Sheet."
)

SYSTEM_INSTRUCTION = (
    "You are an AI Project Manager. Extract task info from the user prompt and return a single JSON object with these EXACT top-level keys:\n"
    "  'task': {title, description, assignee, assignee_email, priority (High/Medium/Low), status (Pending), due_date}\n"
    "  'integrations': array of {action (e.g. github.create_issue), selected (bool), config (dict)}\n"
    "  'missing_fields': list of strings\n"
    "  'clarification_question': string or null\n"
    "Return JSON ONLY. No markdown."
)

payload = {
    "system_instruction": {
        "parts": [{"text": SYSTEM_INSTRUCTION}]
    },
    "contents": [{
        "role": "user",
        "parts": [{"text": TEST_PROMPT}]
    }],
    "generationConfig": {
        "responseMimeType": "application/json"
    }
}

async def call_gemini():
    print("=== DIRECT GEMINI API CALL ===")
    print(f"URL   : {gemini_url[:80]}...")
    print(f"Model : {model_name}")
    print()

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(gemini_url, json=payload)
        print(f"Gemini HTTP Status : {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            try:
                parsed = json.loads(raw_text)
                task = parsed.get("task", {})
                integrations = parsed.get("integrations", [])
                actions = [i.get("action", "") for i in integrations]

                print("=== EXTRACTION RESULTS ===")
                print(f"Title           : {task.get('title', 'NOT FOUND')}")
                print(f"Description     : {task.get('description', 'NOT FOUND')[:80]}...")
                print(f"Assignee        : {task.get('assignee', 'NOT FOUND')}")
                print(f"Due Date        : {task.get('due_date', 'NOT FOUND')}")
                print(f"Priority        : {task.get('priority', 'NOT FOUND')}")
                print(f"Status          : {task.get('status', 'NOT FOUND')}")
                print(f"Integrations    : {actions}")
                print()
                print(f"GitHub recommended   : {any('github' in a for a in actions)}")
                print(f"Slack recommended    : {any('slack' in a for a in actions)}")
                print(f"Gmail recommended    : {any('gmail' in a for a in actions)}")
                print(f"Calendar recommended : {any('calendar' in a for a in actions)}")
                print(f"Sheets recommended   : {any('sheet' in a for a in actions)}")
                print()
                print("FULL JSON:")
                print(json.dumps(parsed, indent=2))
                return 200, parsed
            except Exception as e:
                print(f"JSON parse error: {e}")
                print(f"Raw: {raw_text[:500]}")
                return 200, None
        else:
            print(f"Gemini Error: {resp.text[:500]}")
            return resp.status_code, None

status, result = asyncio.run(call_gemini())
print()
print(f"=== FINAL STATUS: {status} ===")
