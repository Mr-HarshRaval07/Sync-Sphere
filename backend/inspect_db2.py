import motor.motor_asyncio
import asyncio
import json

client = motor.motor_asyncio.AsyncIOMotorClient('mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/syncsphere?appName=Cluster0')
db = client.get_default_database()

async def main():
    task = await db['tasks'].find_one(
        {'automations.action': 'gmail.send_email'}, 
        sort=[('created_at', -1)]
    )
    if task:
        configs = [a['config'] for a in task.get('automations', []) if a['action'] == 'gmail.send_email']
        print(json.dumps(configs, indent=2))
    else:
        print("No task found")

asyncio.run(main())
