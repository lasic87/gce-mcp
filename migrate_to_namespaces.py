import asyncio
import sys
import os

# Ścieżka do GCE
sys.path.append('/root/gce-mcp')

from server import gce_index_folder, gce_cleanup
from config import settings

async def run_migration():
    print("🚀 Background Migration Started: GCE 2.5 Namespaces")
    
    # 1. Cleanup old dead entries
    await gce_cleanup()
    
    # 2. Index GCE Core
    await gce_index_folder("/root/gce-mcp", namespace="gce_core")
    
    # 3. Index Home Assistant
    await gce_index_folder("/root/HA_asystent", namespace="infra")
    
    # 4. Index SOR App
    await gce_index_folder("/root/SOR_app", namespace="sor_app")
    
    print("🏁 Background Migration Finished!")

if __name__ == "__main__":
    # Uruchamiamy migrację
    asyncio.run(run_migration())
