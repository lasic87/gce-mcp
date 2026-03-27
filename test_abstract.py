import asyncio
import os
from server import gce_add_resource

async def test_summary():
    # Upewnienie się, że środowisko jest gotowe
    if "GOOGLE_API_KEY" not in os.environ:
        from dotenv import load_dotenv
        load_dotenv()
    
    # Podajemy tylko URI pliku - to wymusi nową logikę: 
    # 1. Odczyt z dysku
    # 2. Generowanie abstraktu przez Gemini
    file = "/root/gce-mcp/config.py"
    
    print(f"=== TEST AUTONOMY: {file} ===")
    print("Sending only URI to gce_add_resource...")
    
    # Wywołanie bez content i abstract
    result = await gce_add_resource(uri=file)
    
    print(f"\nResult from server: {result}")
    
    if "Sukces" in result:
        print("\n✅ Test autonomicznego indeksowania zakończony sukcesem.")
    else:
        print("\n❌ Coś poszło nie tak.")

if __name__ == "__main__":
    asyncio.run(test_summary())
