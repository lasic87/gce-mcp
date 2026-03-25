import asyncio
from server import gce_search_context

async def run_tests():
    print("\n=== TEST 1: URZĄDZENIA XIAOMI (HOMELAB) ===")
    res1 = await gce_search_context("Adresy IP i tokeny urządzeń Xiaomi")
    print(res1)
    
    print("\n=== TEST 2: STRUKTURA POKOJU (SOR APP) ===")
    res2 = await gce_search_context("Interface Room Bed structure SOR app types")
    print(res2)

if __name__ == "__main__":
    asyncio.run(run_tests())
