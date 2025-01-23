# agent/main.py
import asyncio
import os
from dotenv import load_dotenv
from app.core.config import settings
from app.services.agent_service import AgentService

load_dotenv()

async def main():
    agent = AgentService()
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())