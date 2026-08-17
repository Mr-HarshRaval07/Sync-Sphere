import asyncio
from httpx import AsyncClient

async def run():
    async with AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/v1/tasks/plan-with-ai",
            json={"prompt": "send email to jayant@gmail.com with subject HIII JAYANT and body HIII JAYANT"},
            headers={"Authorization": "Bearer TEST_TOKEN"} # Requires a valid token though...
        )
        print(res.status_code, res.text)

if __name__ == "__main__":
    asyncio.run(run())
