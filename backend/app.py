import asyncio
from utils import apiGateway


async def main():
    await apiGateway.main()

if __name__ == "__main__":
    asyncio.run(main())