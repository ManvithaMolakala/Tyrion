import os
import asyncio
from extract_apy import fetch_investment_options  # Import the async function

VESU_API_URL = os.getenv("VESU_API_URL")

async def main():
    await fetch_investment_options(VESU_API_URL)

if __name__ == "__main__":
    asyncio.run(main())
