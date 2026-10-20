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
            "label": "proxmox_openipmi_masking_intel_n100",
            "content": "Na hoście Proxmox VE 'lasic' (LarkBox X, Intel N100) usługa 'openipmi.service' została wyłączona i zamaskowana ('systemctl mask openipmi'). Płyta główna nie posiada sprzętowego kontrolera BMC/IPMI, co po instalacji pakietu ipmitool powodowało stały status 'failed' w systemctl --failed. Po zamaskowaniu status usług jest czysty (0 failed units)."
        },
        {
            "label": "opnsense_vm100_vzdump_qga_timeout",
            "content": "Maszyna wirtualna VM 100 (OPNsense-router, FreeBSD) podczas niedzielnego automatycznego backupu vzdump (godz. 03:00) raportuje 'VM 100 qga command guest-ping failed - got timeout'. Jest to zachowanie nieszkodliwe wynikające z braku uruchomionej wtyczki os-qemu-guest-agent w OPNsense – kopia snapshotowa wykonuje się pomyślnie."
        },
        {
            "label": "firecrawl_lxc160_docker_build_cache_cleanup",
            "content": "Kontener LXC 160 (Firecrawl) po procesach kompilacji i aktualizacji akumuluje znaczne ilości pamięci podręcznej Docker Build Cache (~6-10 GB), co może zapełnić wirtualny dysk 20 GB powyżej 75%. Okresowe wykonanie 'docker builder prune -f' bezpiecznie zwalnia ~6 GB miejsca, redukując użycie dysku do ~45%."
        },
        {
            "label": "ha_voice_engine_lxc105_journald_retention",
            "content": "Kontener LXC 105 (HA-Voice-Engine) gromadzi obszerne archiwalne logi systemd-journald (do 2 GB), co w połączeniu z obrazami Docker potrafi doprowadzić do 95% zajętości dysku (poniżej 1 GB wolnego). Wykonanie 'journalctl --vacuum-time=3d' natychmiast odzyskuje 1.9 GB przestrzeni."
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
