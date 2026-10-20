import asyncio
import os
import sys

# Ensure .env from /root/gce-mcp is loaded
from dotenv import load_dotenv
load_dotenv("/root/gce-mcp/.env")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "opnsense_automated_major_upgrade_playbook",
            "content": (
                "Sprawdzona procedura (Playbook) automatycznego Major Upgrade OPNsense w Proxmoxie: "
                "1. Snapshot ze stanem RAM: 'qm snapshot 100 <SNAP_NAME> --vmstate 1'. "
                "2. Strażnik Rollbacku: /root/scripts/auto_rollback.sh z 'MAX_WAIT_MINUTES=60' sprawdzający 'ping 8.8.8.8', który w razie awarii zatrzymuje VM, przywraca snapshot ('qm rollback 100 <SNAP_NAME>') i uruchamia VM. "
                "3. Środowisko Cron: Skrypty crona muszą zawierać 'export PATH=\"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"', by 'qm' było widoczne. "
                "4. Wywołanie SSH na FreeBSD: Z uwagi na powłokę csh roota, polecenia z przekierowaniem strumieni należy opakowywać w sh: "
                "ssh -i /root/.ssh/id_ed25519 root@192.168.1.1 \"sh -c 'nohup /usr/local/opnsense/scripts/firmware/upgrade.sh > /var/log/firmware_upgrade.log 2>&1 &'\"."
            )
        },
        {
            "label": "opnsense_26_7_successful_upgrade_status_2026",
            "content": (
                "W nocy 25 września 2026 r. router OPNsense (VM 100) został pomyślnie zaktualizowany w pełni bezobsługowo z wersji 26.1.11_10 do gałęzi 26.7.1_1 (FreeBSD 15.1-RELEASE-p1). "
                "Wszystkie usługi (AdGuard Home z routingiem warunkowym, Kea DHCPv4, Tailscale z Exit Node i DNS override, CrowdSec z bouncerem) działają stabilnie."
            )
        }
    ]
    
    for mem in memories:
        print(f"Adding memory with label: {mem['label']}...")
        try:
            res = await gce_add_memory(content=mem['content'], label=mem['label'], namespace="memories")
            print(f"Result for {mem['label']}: {res}")
        except Exception as e:
            print(f"Error for {mem['label']}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
