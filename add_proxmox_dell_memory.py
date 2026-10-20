import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "proxmox_dell_precision_5820_host_architecture",
            "content": "Host Proxmox VE Dell (hostname: pve2, IP: 192.168.1.12) to stacja robocza Dell Precision 5820 Tower z Proxmox VE 9.1 (kernel 7.0.0-3-pve, 64 GB RAM). Host obsługuje dwie główne maszyny wirtualne ze współdzielonym passthrough karty graficznej NVIDIA RTX 5060 Ti (PCIe 0000:b3:00): 1) VM 100 (ubuntu-ai, 16 GB RAM, 10 vCPU, dysk LVM 100G) oraz 2) VM 120 (Bazzite-Gaming, 32 GB RAM, 10 vCPU, dysk 220G raw na /mnt/ssd-storage). Przełączanie między maszynami realizują skrypty /root/start-gaming.sh oraz /root/start-ai.sh. Pamięci masowe: local (/var/lib/vz), local-lvm (cienka pula pve/data na sdc3), ssd-storage (/mnt/ssd-storage na sdb1) oraz partycje hdd /mnt/hdd-part2 i /mnt/hdd-part3 na sda."
        },
        {
            "label": "proxmox_dell_agy_and_mcp_configuration",
            "content": "Na hoście Proxmox Dell (pve2, 192.168.1.12) zainstalowano i skonfigurowano agenta agy (Antigravity CLI) oraz gemini CLI. Skonfigurowano serwery MCP w ~/.gemini/settings.json oraz ~/.gemini/config/mcp_config.json: 1) context7 (typ http, endpoint https://mcp.context7.com/mcp z kluczem API CONTEXT7_API_KEY), 2) github (typ stdio, binarka /root/.gemini/extensions/github/github-mcp-server z argumentami stdio, --toolsets=all i tokenem GITHUB_PERSONAL_ACCESS_TOKEN). Skopiowano wtyczki github i ponytail do ~/.gemini/antigravity-cli/plugins/. Skonfigurowano klucze SSH umożliwiające bezpośrednią komunikację pomiędzy hostem Dell (192.168.1.12) a Lark (192.168.1.10)."
        }
    ]
    
    for mem in memories:
        lbl = mem["label"]
        cnt = mem["content"]
        print("Adding memory:", lbl)
        try:
            res = await gce_add_memory(content=cnt, label=lbl)
            print("Result for", lbl, ":", res)
        except Exception as e:
            print("Error for", lbl, ":", e)

if __name__ == "__main__":
    asyncio.run(main())
