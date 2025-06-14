import asyncio


async def null_strategy():
    pass


if __name__ == "__main__":
    asyncio.run(null_strategy())
