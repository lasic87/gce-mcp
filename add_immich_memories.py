import asyncio
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "immich_backup_i_aktualizacja_v3",
            "content": "W dniu 5 lipca 2026 r. przeprowadzono ręczny backup vzdump kontenera Immich (LXC 106, rozmiar archiwum 7.20 GB, bez /mnt/photos) oraz pomyślnie zaktualizowano aplikację do wersji v3.0.1 (poprzez zmianę IMMICH_VERSION=v3 w .env). Baza danych automatycznie przeszła migrację na VectorChord (wersja 0.4.3)."
        },
        {
            "label": "immich_lxc106_resize_dysku",
            "content": "W trakcie aktualizacji Immicha do v3.0.1 zabrakło miejsca w kontenerze LXC 106. Dysk systemowy kontenera został powiększony z 20 GB do 35 GB przy użyciu poleceń LVM 'pct resize 106 rootfs +15G', a następnie offline z poziomu hosta za pomocą 'e2fsck -f -y /dev/pve/vm-106-disk-0' i 'resize2fs /dev/pve/vm-106-disk-0'."
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
