import asyncio
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_search_context

async def main():
    queries = [
        "Nextcloud LXC 102 config mount IP storage",
        "Nextcloud storage disk mount",
        "Nextcloud nie działa, brak dostępu, błąd",
        "Proxmox disk mount HDD_2TB",
        "gce://user/memories/"
    ]
    
    for q in queries:
        print(f"\n=========================================\nQUERY: {q}\n=========================================")
        try:
            res = await gce_search_context(q)
            print(res)
        except Exception as e:
            print(f"Error during search: {e}")

if __name__ == "__main__":
    asyncio.run(main())
