import asyncio
import os
from pathlib import Path
from server import gce_add_resource

async def index_project(directory, extensions=None):
    if extensions is None:
        extensions = ['.md', '.py', '.txt', '.yaml', '.yml', '.conf', '.json', '.sh', '.env']
    
    print(f"Scanning {directory} for homelab infrastructure data...")
    path = Path(directory)
    count = 0
    
    for file in path.rglob('*'):
        if file.is_file() and file.suffix in extensions:
            if '.venv' in str(file) or '.git' in str(file) or 'node_modules' in str(file):
                continue
            
            print(f"Indexing: {file}")
            result = await gce_add_resource(str(file))
            if "Sukces" in result:
                count += 1
            else:
                print(f"Failed to index {file}: {result}")
            
            # SAFE MODE: Przerwa 1.5 sekundy, aby router mógł "odetchnąć"
            await asyncio.sleep(1.5)
                
    print(f"Finished. Indexed {count} files from {directory}.")

async def main():
    # 1. Indeksujemy główny projekt asystenta HA
    await index_project("/root/HA_asystent")
    
    # 2. Indeksujemy kluczowe skrypty i konfiguracje systemowe
    critical_files = [
        "/root/opengce_setup_log.md",
        "/root/mcp_config.json",
        "/root/google_vlm.py",
        "/root/gce_monitor.sh"
    ]
    
    for f in critical_files:
        if os.path.exists(f):
            print(f"Indexing critical file: {f}")
            await gce_add_resource(f)

if __name__ == "__main__":
    asyncio.run(main())
