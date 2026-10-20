import asyncio
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "sor_app_event_based_sync_migration_2026",
            "content": "Zmigrowano mechanizm synchronizacji SOR App z modelu wysyłania całego stanu (Fat Client Push) na model oparty w 100% o akcje (Event-based/Action-based). Rozwiązuje to problem cofania się danych pacjentów przy wybudzaniu uśpionych kart w przeglądarkach na stacjonarnych komputerach (Chromium Sleeping Tabs). Serwer przetwarza akcje sekwencyjnie w pętli zdarzeń Node.js i jest jedynym kreatorem stanu głównego, rozsyłając aktualizację przez WebSocket."
        },
        {
            "label": "sor_app_atomic_state_persistence_2026",
            "content": "Wdrożono atomowy zapis pliku stanu state.json na serwerze Node.js. Zamiast bezpośredniego nadpisywania pliku, dane są zapisywane do pliku tymczasowego .tmp, a następnie podmieniane za pomocą operacji systemowej fs.renameSync. Zapobiega to uszkodzeniu bazy danych w przypadku nagłego restartu kontenera w Proxmoxie."
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
