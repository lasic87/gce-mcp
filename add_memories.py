import asyncio
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "zapasowe_backupy_zwolnione_miejsce",
            "content": "W dniu 5 lipca 2026 r. usunięto starsze kopie zapasowe vzdump (z 21 i 28 czerwca 2026 r.) w katalogu `/mnt/HDD_2TB/backups/proxmox/weekly/dump/`, uwalniając 48 GB przestrzeni dyskowej na dysku zewnętrznym 2 TB. Zgodnie z decyzją pozostawiono tylko najnowsze, pojedyncze kopie z dnia 5 lipca 2026 r."
        },
        {
            "label": "nextcloud_lxc102_przywrocone_dzialanie",
            "content": "Kontener Nextcloud (LXC 102) był wyłączony, a przy próbach zapisu zwracał błąd HTTP 507 Insufficient Storage, ponieważ powiązany z nim zewnętrzny dysk `/mnt/HDD_2TB` był w 100% pełny. Po zwolnieniu 48 GB miejsca i ponownym uruchomieniu oraz reboocie kontenera, Nextcloud działa stabilnie na `http://192.168.1.20:8080`."
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
