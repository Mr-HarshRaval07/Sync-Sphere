import sys, os, asyncio, httpx, json, datetime
sys.path.insert(0, 'src')
from dotenv import load_dotenv
load_dotenv('D:/syncsphere 01/syncsphere 01/backend/.env')

TEST_PROMPT = (
    'Launch the SyncSphere website on August 15, 2026. Complete development by August 10, 2026. '
    'Make it high priority and assign it to Janhvi. Create a GitHub issue, notify my team in Slack, '
    'send the launch plan to jayant32@gmail.com, schedule a launch meeting on August 14, 2026 at 10 AM, '
    'and add the project name, deadline, priority, and status to Google Sheets.'
)

print('=== FINAL LIVE ENDPOINT TEST ===')
print('Time:', datetime.datetime.now().isoformat())
print()

async def test():
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            'http://localhost:8001/v1/tasks/plan-with-ai',
            json={'prompt': TEST_PROMPT},
            headers={'Authorization': 'Bearer test'}
        )
        return resp

result = asyncio.run(test())
print('SyncSphere /v1/tasks/plan-with-ai HTTP Status:', result.status_code)
print()

try:
    body = result.json()
    if result.status_code == 200:
        plan = body.get('data', {})
        task = plan.get('task', {})
        integrations = plan.get('integrations', [])
        actions = [i.get('action', '') for i in integrations]

        print('=== EXTRACTION RESULTS ===')
        print('Title       :', task.get('title', 'NOT FOUND'))
        print('Description :', str(task.get('description', ''))[:80])
        print('Assignee    :', task.get('assignee', 'NOT FOUND'))
        print('Due Date    :', task.get('due_date', 'NOT FOUND'))
        print('Priority    :', task.get('priority', 'NOT FOUND'))
        print()
        print('Integrations:', actions)
        print()
        print('GitHub recommended          :', any('github' in a for a in actions))
        print('Slack recommended           :', any('slack' in a for a in actions))
        print('Gmail recommended           :', any('gmail' in a for a in actions))
        print('Google Calendar recommended :', any('calendar' in a for a in actions))
        print('Google Sheets recommended   :', any('sheet' in a for a in actions))
        print()
        print('FULL PLAN JSON:')
        print(json.dumps(plan, indent=2))
    else:
        print('Error:', json.dumps(body, indent=2))
except Exception as e:
    print('Parse error:', e)
    print(result.text[:400])
