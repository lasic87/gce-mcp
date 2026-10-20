import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "proxmox_postfix_default_transport_discard_2026",
            "content": "Skonfigurowano Postfix na hoście Proxmox VE (lasic) z parametrem 'default_transport = discard' oraz wyczyszczono kolejkę 125 zaległych wiadomości ('postsuper -d ALL'). Zapobiega to pętli prób wysyłki powiadomień systemowych/cron na zablokowany przez ISP port 25 Gmaila oraz eliminuje niepotrzebne wybudzenia procesora i próby połączeń sieciowych."
        },
        {
            "label": "proxmox_intel_n100_epp_balance_power_2026",
            "content": "Zaktualizowano usługę systemd 'powertop-tune.service' na hoście Proxmox VE (LarkBox X, Intel N100) o wpis 'echo balance_power | tee /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference'. Rozwiązuje to problem blokowania taktowania rdzeni na maksymalnym zegarze 2.9 GHz pod sterownikiem intel_pstate, umożliwiając prawidłowe schodzenie do taktowań spoczynkowych 700-1200 MHz, co wycisza wentylator i obniża temperaturę CPU z 58°C do 53-54°C."
        }
    ]
    
    for mem in memories:
        print(f"Adding memory with label: {mem['label']}...")
        try:
            res = await gce_add_memory(content=mem['content'], label=mem['label'])
            print(f"Result for {mem['label']}: {res}")
        except Exception as e:
            print(f"Error for {mem['label']}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
