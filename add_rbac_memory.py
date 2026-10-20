import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    label = "sor_app_server_side_rbac_websocket_2026"
    content = "Zaimplementowano weryfikację ról i uprawnień RBAC na serwerze Node.js dla połączeń WebSocket. Serwer rejestruje aktywowaną rolę każdego gniazda i sprawdza uprawnienia przed wykonaniem akcji w ROLE_PERMISSIONS map. Zapobiega to nieuprawnionym modyfikacjom bazy danych przez tryb Podglądu (Viewer/TV) lub z poziomu konsoli przeglądarki oraz stanowi gotowy fundament pod logowanie na konta indywidualne."
    
    print(f"Adding memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
