import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    label = "sor_app_6h_inactivity_autologout_2026"
    content = "Wdrożono 6-godzinny stoper bezczynności (Inactivity Auto-Logout) po stronie klienta. Stoper automatycznie odnawia się przy dowolnej interakcji użytkownika na karcie aplikacji. Zapobiega to utracie sesji podczas pracy, jednocześnie bezpiecznie wylogowując porzucone stanowiska robocze po 6 godzinach całkowitego braku aktywności."
    
    print(f"Adding memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
