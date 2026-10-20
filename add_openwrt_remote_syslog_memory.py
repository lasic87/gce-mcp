import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    label = "openwrt_remote_syslog_configuration"
    content = (
        "Centralny zdalny Syslog dla routerów OpenWrt AX3600 (192.168.1.2) i AX3000T (192.168.1.3): "
        "Na serwerze Proxmox (lasic, 192.168.1.10) wdrożono usługę rsyslog nasłuchującą na porcie UDP 514 "
        "z dedykowaną separacją plików w /var/log/routers/ (ax3600.log oraz ax3000t.log) i regułą 'stop' zapobiegającą "
        "zaśmiecaniu głównego sysloga hosta. Skonfigurowano logrotate w /etc/logrotate.d/routers (rotacja tygodniowa, "
        "kompresja gzip, retencja 4 tygodnie). Na obu routerach OpenWrt aktywowano przesyłanie logów przez demona logread "
        "(uci set system.@system[0].log_ip='192.168.1.10', log_port='514', log_proto='udp'). Pozwala to na pełną trwałość "
        "komunikatów jądra, OOM i awarii sprzętowych w przypadku nagłych restartów urządzeń sieciowych."
    )
    
    print("Adding memory:", label)
    try:
        res = await gce_add_memory(content=content, label=label)
        print("Result:", res)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
