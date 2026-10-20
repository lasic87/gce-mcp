import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "network_topology_and_ax3600_root_cause_diagnosis",
            "content": "Fizyczna topologia sieci i diagnoza awarii routera (2026-09-07): Główne serwery homelabu (LarkBox/OPNsense 192.168.1.10, Proxmox 2 pve2 192.168.1.12, Dell Wyse Home Assistant 192.168.1.50) są wpięte bezpośrednio kablami ethernetowymi do routera Xiaomi AX3600 (192.168.1.2, OpenWrt 24.10.1, aarch64), który pełni rolę centralnego switcha/AP. Zdiagnozowano przyczynę powtarzających się awarii sieci (m.in. o 16:02 i 19:12): gwałtowny twardy restart AX3600 (wykryto stan UBIFS recovery needed po crashu). Restart wywoływany był przez sprzętowy watchdog SoC Qualcomm IPQ8074 po zawieszeniu pod obciążeniem oraz brak pamięci RAM (OOM/kernel panic przy braku SWAP) spowodowany m.in. wyciekami i narzutem pamięciowym nieużywanej usługi Tailscale (65 MB RSS, 1.3 GB VSZ) oraz ryzykiem pętli broadcastowych na mostku br-lan z bezprzewodowym meshem 802.11s."
        },
        {
            "label": "openwrt_ax3600_ax3000t_hardening_and_tailscale_removal",
            "content": "Optymalizacja i zabezpieczenie routerów OpenWrt AX3600 (192.168.1.2) i AX3000T (192.168.1.3): 1) Włączono ochronę Spanning Tree Protocol (STP) na mostkach br-lan na obu urządzeniach (uci set network.@device[0].stp='1'), zabezpieczając sieć przed pętlami pakietów i burzami broadcastowymi pomiędzy portami LAN a bezprzewodowym meshem 802.11s (LSCmesh, 5 GHz HE80). 2) Zainstalowano i włączono zram-swap w pamięci RAM: 202 MiB na AX3600 (algorytm LZO) oraz 117 MiB na AX3000T, zapobiegając awariom Out-of-Memory (OOM). 3) Całkowicie odinstalowano i usunięto zbędną usługę Tailscale z obu routerów (odzyskano 65 MB RAM na AX3600 i 10 MB flash na AX3000T, wyczyszczono reguły ip rule lookup 52). Głównym i jedynym węzłem Tailscale w sieci LAN pozostaje wirtualny OPNsense (192.168.1.1, IP Tailscale 100.106.34.74). 4) Skonfigurowano klucz SSH z hosta lasic w authorized_keys na obu routerach."
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
