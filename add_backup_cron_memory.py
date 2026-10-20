import asyncio
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    label = "immich_wlaczenie_do_vzdump_cron"
    content = "W dniu 5 lipca 2026 r. zaktualizowano systemowy harmonogram Proxmox /etc/pve/vzdump.cron, dodając kontener LXC 106 (Immich) do automatycznego, cotygodniowego zadania kopii zapasowej vzdump, które uruchamia się w każdą niedzielę o godzinie 03:00 rano."
    
    print(f"Adding memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
