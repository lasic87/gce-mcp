import asyncio
import os
import time
import logging
from pathlib import Path
from server import gce_add_resource

# Konfiguracja logowania do pliku
logging.basicConfig(
    filename='/root/gce_safe_index.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def safe_index(directory, extensions):
    logging.info(f"SAFE INDEXING START: {directory}")
    path = Path(directory)
    count = 0
    
    # Sortujemy pliki, by mieć stały porządek
    files = sorted([f for f in path.rglob('*') if f.is_file() and f.suffix in extensions])
    
    for file in files:
        if any(p in str(file) for p in ['node_modules', 'dist', '.git', '.next', '.venv']):
            continue
        
        if file.stat().st_size > 100000 and file.suffix == '.json':
            logging.info(f"Skipping too large JSON: {file}")
            continue
            
        logging.info(f"Safe indexing: {file}")
        try:
            result = await gce_add_resource(str(file))
            logging.info(f"Result: {result}")
            count += 1
            # PAUZA DLA ROUTERA: 2 sekundy po każdym pliku
            await asyncio.sleep(2.0)
        except Exception as e:
            logging.error(f"Error indexing {file}: {e}")
            
    logging.info(f"SAFE INDEXING END: {count} files.")

async def main():
    try:
        # 1. Homelab
        await safe_index("/root/HA_asystent", ['.md', '.py', '.txt', '.yaml', '.yml', '.env'])
        # 2. SOR App
        await safe_index("/root/SOR_app", ['.ts', '.tsx', '.css', '.html', '.json', '.md'])
    except Exception as e:
        logging.critical(f"FATAL ERROR in indexing loop: {e}")

if __name__ == "__main__":
    asyncio.run(main())
