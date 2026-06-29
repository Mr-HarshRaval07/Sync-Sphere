import asyncio

from app.llm.factory import get_llm


async def main():

    llm = get_llm()

    response = await llm.generate(
        "Reply with exactly: Sync Sphere is working."
    )

    print(response)


asyncio.run(main())