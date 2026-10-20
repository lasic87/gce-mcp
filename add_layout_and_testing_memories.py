import asyncio
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "sor_app_layout_fix_waiting_list_2026",
            "content": "Naprawiono błąd layoutu w `App.tsx` polegający na niekontrolowanym zwężaniu się i zanikaniu panelu Poczekalni (`WaitingList`) na ekranach desktopowych. Przyczyną było rozpychanie kontenera sal przez szeroką siatkę łóżek przy braku klasy `min-w-0` na elemencie `flex-grow` oraz brak blokady kurczenia (`shrink-0`) i określonej szerokości minimalnej na bocznym `<aside>`. Rozwiązanie: dodano `min-w-0` do kontenera sal oraz klasy `shrink-0 lg:min-w-[320px] xl:min-w-[360px]` do panelu poczekalni."
        },
        {
            "label": "sor_app_testing_environment_stabilization_2026",
            "content": "Ustabilizowano testy automatyczne (`vitest`) aplikacji SOR App. Rozwiązano problem logowania w testach poprzez dynamiczne wstrzyknięcie zmiennej środowiskowej `VITE_PASSW_HASH` (Base64 hash bcrypt hasła `SOR-Koordynator-2024`) przy użyciu `vi.stubEnv`. Mock WebSocketu został ulepszony o asynchroniczne wyzwalanie zdarzenia `onopen` w konstruktorze, co zapobiega zawieszaniu się testu połączenia w `LoginScreen.tsx`. Poprawiono asercje w `BedGrid.test.tsx` z `Łóżko #1` na `#1` w celu dopasowania ich do rzeczywistego stanu renderowanego przez komponent `BedTile.tsx`."
        }
    ]
    
    for memory in memories:
        print(f"Adding memory with label: {memory['label']}...")
        try:
            res = await gce_add_memory(content=memory['content'], label=memory['label'])
            print(f"Result: {res}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
