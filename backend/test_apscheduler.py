import httpx
import asyncio

async def test_schedule():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First login
        res = await client.post("http://localhost:8000/v1/auth/login", json={
            "email": "demo@syncsphere.ai",
            "password": "Password123!"
        })
        if res.status_code != 200:
            print("Login failed!", res.text)
            # Maybe demo doesn't exist?
            # Let's create it.
            reg_res = await client.post("http://localhost:8000/v1/auth/register", json={
                "email": "demo@syncsphere.ai",
                "password": "Password123!",
                "full_name": "Demo User",
                "organization_name": "Demo Org"
            })
            if reg_res.status_code not in (200, 201):
                print("Reg fail", reg_res.text)
                return
            res = await client.post("http://localhost:8000/v1/auth/login", json={
                "email": "demo@syncsphere.ai",
                "password": "Password123!"
            })
            if res.status_code != 200:
                print("Second login fail", res.text)
                return
        
        token = res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Logged in!")

        # 1. Create a dummy task to schedule
        task_res = await client.post("http://localhost:8000/v1/tasks", json={
            "title": "APScheduler Test Task",
            "status": "Pending"
        }, headers=headers)
        
        if task_res.status_code not in (200, 201):
            print("Task creation failed", task_res.text)
            return

        task_id = task_res.json()["data"]["id"]
        print(f"Created task: {task_id}")

        # 2. Schedule the task to run EVERY 1 hour (so it registers)
        sched_res = await client.post(f"http://localhost:8000/v1/tasks/{task_id}/schedule", json={
            "schedule_type": "hourly",
            "enabled": True
        }, headers=headers)

        if sched_res.status_code not in (200, 201):
            print("Schedule creation failed", sched_res.text)
            return
            
        sched_id = sched_res.json()["data"]["id"]
        print(f"Created schedule successfully! Engine responded: {sched_id}")

        # 3. Test GET Global Schedule
        get_res = await client.get(f"http://localhost:8000/v1/schedules/{sched_id}", headers=headers)
        print("GET Schedule Res:", get_res.json() if get_res.status_code == 200 else get_res.text)

if __name__ == "__main__":
    asyncio.run(test_schedule())
