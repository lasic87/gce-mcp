import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server import gce_add_memory, gce_delete_memory
from vector_store import vector_store

async def main():
    print("=== AKTUALIZACJA PAMIĘCI GCE: HOMELAB STAN PAŹDZIERNIK 2026 ===")
    
    # 1. Usuwamy lub zastępujemy stare, nieaktualne wpisy
    old_uris_to_clean = [
        "gce://user/memories/network_infrastructure_audit_2026_04_24",
    ]
    for uri in old_uris_to_clean:
        try:
            print(f"Czyszczenie/zastępowanie starego wpisu: {uri}")
            res = await gce_delete_memory(uri)
            print(f"Wynik: {res}")
        except Exception as e:
            print(f"Błąd przy usuwaniu {uri}: {e}")

    # 2. Dodajemy uaktualnione, zweryfikowane fakty architektoniczne
    new_memories = [
        {
            "label": "homelab_inwentaryzacja_lxc_i_uslug_pazdziernik_2026",
            "content": """Kompletna inwentaryzacja kontenerów i usług w Homelabie (LarkBox X, Proxmox VE 9.2, październik 2026):
- VM 100: Router OPNsense 25.7 (192.168.1.1, Tailscale 100.106.34.74, Kea DHCP, Unbound DNS, AdGuard Home).
- LXC 101: Media Stack (192.168.1.194, rootfs 186 GB / 12% zajęte). Jellyfin (natywny :8096), qBittorrent (:8081), Sonarr (:8989), Radarr (:7878), Prowlarr (:9696), Tdarr (:8265), FlareSolverr, Jellyseerr, Bazarr, Unmanic.
- LXC 102: debian-apps (192.168.1.20, rootfs 32 GB / 32% zajęte). Docker: Nextcloud (:8080), Homepage dashboard (:3000), CouchDB (:5984 dla Obsidian LiveSync), MariaDB, Redis, dnsmasq, Portainer Agent (:9001).
- LXC 103: docker-registry (192.168.1.104) z Portainer Server (:9000, :9443).
- LXC 105: HA-Voice-Engine (192.168.1.113, port 8080).
- LXC 106: Immich (192.168.1.124, port 2283, rootfs 35 GB / 39% zajęte). Kontener unprivileged (mapowanie UID 100000).
- LXC 108: wled (192.168.1.120) z LedFx (:8888) i HyperHDR (:19444).
- LXC 150: Frigate (192.168.1.15) - status STOPPED (onboot: 0), wyłączony celowo ze względu na obciążenie CPU N100 na LarkBoxie. Zarządzanie z poziomu `/root/HA_asystent/frigate_tool.py`.
- LXC 151: SOR App v2 (192.168.1.153, port 8088 -> 8080). Utwardzona aplikacja medyczna (SEC-01 do SEC-07).
- LXC 160: Firecrawl (192.168.1.110, kontenery Docker wygaszone)."""
        },
        {
            "label": "homelab_storage_hdd_2tb_i_bind_mounts_pazdziernik_2026",
            "content": """Stan magazynu dyskowego i bind-mountów USB 2TB (październik 2026):
- Dysk zewnętrzny WD Elements 2TB (/dev/sdb1, ext4) zamontowany na stałe pod `/mnt/HDD_2TB`. Stan zajętości: 88% (1.6 TB zajęte, 226 GB wolne). Zredukowano rezerwę ext4 do 1% (tune2fs -m 1).
- Bind mounty do kontenerów:
  * LXC 101 (MediaStack): `/mnt/HDD_2TB/media/movies` -> `/media/movies`, `/mnt/HDD_2TB/media/tv` -> `/media/tv`, `/mnt/HDD_2TB/media/downloads` -> `/media/downloads`.
  * LXC 102 (debian-apps): `/mnt/HDD_2TB/nextcloud` -> `/mnt/data` (uprawnienia 100033:100000).
  * LXC 106 (Immich): `/mnt/HDD_2TB/immich` -> `/mnt/photos` (uprawnienia 100000:100000).
  * LXC 150 (Frigate): `/mnt/HDD_2TB/frigate` -> `/opt/frigate/media`.
  * Magazyn vzdump (hdd_backups): `/mnt/HDD_2TB/backups/proxmox/weekly`.
  * Obsidian Vault: `/mnt/HDD_2TB/obsidian_vault`.
- Autonaprawa I/O: Skrypt `/root/scripts/hdd_repair.sh` w cronie roota co minutę testuje zapis (.write_test) i w razie problemów remountuje dysk oraz restartuje kontenery 101, 102, 106 oraz wznawia kontenery onboot: 1."""
        },
        {
            "label": "homelab_backups_vzdump_i_power_management_2026",
            "content": """Konfiguracja backupów Proxmox i optymalizacji zasilania (październik 2026):
- Backupy VZDUMP: Harmonogram `/etc/pve/vzdump.cron` co niedzielę o 03:00. Kopie snapshot z kompresją zstd na storage `hdd_backups` (`/mnt/HDD_2TB/backups/proxmox/weekly`). Objęte: VM 100, LXC 101, 102, 103, 106, 150, 151. Retencja w storage.cfg ustawiona na `keep-last=2` (zapobiega zapełnieniu dysku 2TB).
- Plany typu 'backup_script.sh' (cold storage do szuflady) oraz Scrutiny w Dockerze nie zostały wdrożone - zastąpiono je automatyzacją vzdump PVE i doraźnym smartctl.
- Zasilanie i CPU: Usługa `powertop-tune.service` przy starcie systemu wykonuje powertop auto-tune, ustawia CPU governor powersave oraz EPP balance_power. Autosuspend dysku USB wyłącza reguła udev `/etc/udev/rules.d/99-usb-hdd-stability.rules`."""
        }
    ]

    for mem in new_memories:
        print(f"\nDodawanie pamięci: {mem['label']}...")
        try:
            res = await gce_add_memory(content=mem['content'], label=mem['label'])
            print(f"Zapisano: {res}")
        except Exception as e:
            print(f"Błąd zapisu {mem['label']}: {e}")

    print("\n=== AKTUALIZACJA ZAKOŃCZONA SUKCESEM ===")

if __name__ == "__main__":
    asyncio.run(main())
