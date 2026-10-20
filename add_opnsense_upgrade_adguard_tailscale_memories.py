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
            "label": "proxmox_pve92_upgrade_postponed_reboot_2026",
            "content": "Host Proxmox VE 'lasic' (LarkBox X, Intel N100) został zaktualizowany z PVE 9.1 do wersji 9.2.20 (283 pakiety zaktualizowane bez konfliktów). Restart hosta został odłożony na dogodne okno serwisowe; system stabilnie działa na kernelu 6.8.12-15-pve z przygotowanymi w GRUB jądrami 7.0.14-19-pve."
        },
        {
            "label": "opnsense_26_7_nightly_upgrade_orchestration_snapshot",
            "content": "Przed major upgradem OPNsense z 26.1.11_10 do gałęzi 26.7 utworzono w Proxmoxie snapshot maszyny VM 100 'PRZED_26_7' ze stanem RAM i dysku. Zaktualizowano strażnika /root/scripts/auto_rollback.sh z czasem oczekiwania 60 minut oraz utworzono skrypt orkiestracji /root/scripts/nightly_upgrade_orchestrator.sh zaplanowany w crontab na godz. 04:00 (jednorazowe wykonanie z auto-wyrejestrowaniem). Aktualizacja wywoływana jest przez SSH kluczem ED25519."
        },
        {
            "label": "opnsense_adguard_home_conditional_upstream_dns",
            "content": "W pliku konfiguracyjnym AdGuard Home (/usr/local/AdGuardHome/AdGuardHome.yaml) na OPNsense wdrożono warunkowy routing DNS: zapytania o strefy '[/lasic.home/]127.0.0.1:5353' i '[/home/]127.0.0.1:5353' trafiają do lokalnego Unbound DNS, a domeny publiczne do szyfrowanego Quad9 DoH ('https://dns10.quad9.net/dns-query'). W składni YAML wpisy z nawiasami kwadratowymi muszą być w cudzysłowach, aby uniknąć błędów parsera go-yaml."
        },
        {
            "label": "tailscale_adguard_global_nameserver_integration",
            "content": "W Tailscale skonfigurowano OPNsense (100.106.34.74) jako Global Nameserver z włączoną opcją 'Override local DNS'. Usunięto serwery publiczne (Google/Cloudflare), aby wyeliminować zjawisko równoległych zapytań (Parallel DNS leak) omijających filtry reklam. Dzięki temu wszystkie urządzenia w Tailnecie (także poza domem, na LTE) korzystają z domowego filtrowania AdGuard Home i rozpoznają lokalne domeny *.lasic.home."
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
