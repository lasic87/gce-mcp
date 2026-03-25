import asyncio
from server import gce_consolidate_memories, gce_search_context

async def run_test():
    test_log = """
    Dzisiejsza sesja:
    - Rozwiązano błąd parsowania JSON w ha_tool.py poprzez dodanie sprawdzenia response.text.
    - Ustalono, że router OPNsense ma stałe IP 192.168.1.1.
    - Użytkownik wspomniał, że preferuje ciemny motyw w aplikacji SOR.
    - Skonfigurowano nową kamerę w Frigate na porcie 5000.
    """
    
    print("\n=== TEST KONSOLIDACJI WSPOMNIEŃ ===")
    res = await gce_consolidate_memories(content=test_log, category="session_summary")
    print(res)
    
    print("\n=== WERYFIKACJA WYSZUKIWANIA (Szukamy IP routera) ===")
    search_res = await gce_search_context("Jaki jest adres IP routera OPNsense?")
    print(search_res)

if __name__ == "__main__":
    asyncio.run(run_test())
