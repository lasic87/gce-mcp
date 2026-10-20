import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    label = "sor_app_zero_trust_sanitization_uuid_2026"
    content = "Wdrożono natywną walidację XSS (sanitizeText) oraz unikalne ID (crypto.randomUUID) na backendzie Node.js bez użycia zewnętrznych bibliotek npm (zgodnie z polityką Zero Trust). Wyeliminowano użycie typów any w serwerze."
    
    print(f"Adding memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
