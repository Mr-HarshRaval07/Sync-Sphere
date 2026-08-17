
import asyncio, motor.motor_asyncio
async def main():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://sync_user:secure_password_123@localhost:27017/syncsphere?authSource=admin')
    db = client.syncsphere
    
    print('PROMPTS:', await db.prompt_executions.count_documents({}))
    p = await db.prompt_executions.find_one({}, sort=[('created_at', -1)])
    print('LATEST PROMPT:', p)
    
    print('EXECUTIONS (execution_runs):', await db.execution_runs.count_documents({}))
    print('EXECUTIONS (workflow_execution_logs):', await db.workflow_execution_logs.count_documents({}))
    w = await db.workflow_execution_logs.find_one({}, sort=[('started_at', -1)])
    print('LATEST WORKFLOW:', w)
    
asyncio.run(main())

