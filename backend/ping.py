import asyncio
import httpx

async def run():
    async with httpx.AsyncClient() as c:
        try:
            r1 = await c.options("http://localhost:8000/v1/tasks")
            print("OPTIONS /v1/tasks:", r1.status_code)
            
            r2 = await c.get("http://localhost:8000/v1/tasks")
            print("GET /v1/tasks:", r2.status_code)

            r3 = await c.get("http://localhost:8000/v1/connectors")
            print("GET /v1/connectors:", r3.status_code)
            
            r4 = await c.get("http://localhost:8000/v1/connect_typo/status")
            print("GET /v1/connect_typo/status:", r4.status_code)
            
        except Exception as e:
            print("Server not running?", str(e))

asyncio.run(run())
