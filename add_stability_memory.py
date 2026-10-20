import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    label = "sor_app_24_7_stability_package_2026"
    content = "Zaimplementowano pakiet stabilności 24/7 dla SOR App: (1) WebSocket Ping-Pong Heartbeat (30s) likwidujący wycieki pamięci nieaktywnych zombie połączeń po stronie Node.js, (2) Debounced Async Write (500ms) dla zapisu state.json zrzucający migawkę dyskową bez blokowania I/O i bez retencji danych wypisanych pacjentów, (3) Jednolity stoper minutowy minuteTick zsynchronizowany z App.tsx eliminujący plagę osobnych timerów w kafelkach łóżek przy zachowaniu 100% unikalności czasów dla każdego pacjenta."
    
    print(f"Adding memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
