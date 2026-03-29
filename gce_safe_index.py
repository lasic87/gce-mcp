import asyncio
import os
import time
import logging
import hashlib
import json
from pathlib import Path
from server import gce_add_resource

# Konfiguracja logowania do pliku
logging.basicConfig(
    filename='/root/gce_safe_index.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

CACHE_FILE = "/root/gce-mcp/data/index_cache.json"

def get_file_hash(file_path):
    """Calculates MD5 hash of a file."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Hash calculation error for {file_path}: {e}")
        return None

def load_cache():
    """Loads indexing cache from disk."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Cache load error: {e}")
    return {}

def save_cache(cache):
    """Saves indexing cache to disk."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logging.error(f"Cache save error: {e}")

async def safe_index(directory, extensions):
    logging.info(f"SMART SAFE INDEXING START: {directory}")
    path = Path(directory)
    count = 0
    skipped = 0
    cache = load_cache()
    
    # Sortujemy pliki, by mieć stały porządek
    files = sorted([f for f in path.rglob('*') if f.is_file() and f.suffix in extensions])
    
    for file_path in files:
        str_path = str(file_path)
        if any(p in str_path for p in ['node_modules', 'dist', '.git', '.next', '.venv', '__pycache__']):
            continue
        
        if file_path.stat().st_size > 100000 and file_path.suffix == '.json':
            logging.info(f"Skipping too large JSON: {file_path}")
            continue
            
        # Sprawdzanie hash-a (Smart Indexing)
        current_hash = get_file_hash(str_path)
        if current_hash and cache.get(str_path) == current_hash:
            # logging.debug(f"Skipping unchanged file: {file_path}")
            skipped += 1
            continue

        logging.info(f"Indexing changed file: {file_path}")
        try:
            result = await gce_add_resource(str_path)
            logging.info(f"Result: {result}")
            if "Sukces" in result:
                cache[str_path] = current_hash
                count += 1
                # PAUZA DLA ROUTERA: 2 sekundy po każdym nowym/zmienionym pliku
                await asyncio.sleep(2.0)
        except Exception as e:
            logging.error(f"Error indexing {file_path}: {e}")
            
    save_cache(cache)
    logging.info(f"SMART INDEXING END: {count} new/changed, {skipped} skipped.")

async def main():
    try:
        # 1. Homelab Infrastructure
        await safe_index("/root/HA_asystent", ['.md', '.py', '.txt', '.yaml', '.yml', '.env'])
        # 2. SOR App
        await safe_index("/root/SOR_app", ['.ts', '.tsx', '.css', '.html', '.json', '.md'])
        # 3. GCE Engine itself
        await safe_index("/root/gce-mcp", ['.md', '.py', '.txt', '.env'])
    except Exception as e:
        logging.critical(f"FATAL ERROR in indexing loop: {e}")

if __name__ == "__main__":
    asyncio.run(main())
