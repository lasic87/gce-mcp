import asyncio
import sys
from server import gce_search_context

async def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "licznik wody"
    print(f"Searching GCE for: {query}")
    result = await gce_search_context(query)
    print("\n=== SEARCH RESULT ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
