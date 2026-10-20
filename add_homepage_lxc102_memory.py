import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "homepage_lxc102_docker_service_restore_2026",
            "content": "Aplikacja Homepage działa w kontenerze LXC 102 (debian-apps) pod adresem http://192.168.1.20:3000 (pliki w /opt/homepage/). Zaktualizowano politykę restartu kontenera na 'restart: always' (zarówno w kontenerze, jak i w /opt/homepage/docker-compose.yml), gwarantując automatyczne wznawianie usługi po restartach LXC lub demona Dockera."
        },
        {
            "label": "lxc102_docker_socket_stale_cleanup_fix",
            "content": "W kontenerze LXC 102 (debian-apps) rozwiązano problem błędu 'Cannot connect to the Docker daemon at unix:///var/run/docker.sock'. Przyczyną było osierocone gniazdo UNIX /run/docker.sock odrzucające połączenia (Connection refused), co blokowało dostęp do Dockera i powodowało pętlę restartów kontenera 'portainer_agent'. Procedura naprawcza: zatrzymanie 'docker.service' i 'docker.socket', usunięcie pliku '/run/docker.sock' oraz ponowne uruchomienie obu jednostek systemd."
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
