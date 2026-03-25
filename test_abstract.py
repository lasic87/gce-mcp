import asyncio
import os
from server import gce_add_resource
from quota_manager import quota_manager

async def test_summary():
    if "GOOGLE_API_KEY" not in os.environ:
        from dotenv import load_dotenv
        load_dotenv()
    
    file = "/root/SOR_app/sor-app-v2/App.tsx"
    print(f"Indexing {file}...")
    result = await gce_add_resource(file, "content test", "abstract test")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_summary())
