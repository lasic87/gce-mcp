import asyncio
import os
from google import genai
from dotenv import load_dotenv

async def check_available_models():
    # Szukamy .env w gce-mcp
    load_dotenv("/root/gce-mcp/.env")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Błąd: Brak GOOGLE_API_KEY w .env")
        return

    client = genai.Client(api_key=api_key)
    print("=== DOSTĘPNE MODELE (Nowe SDK) ===")
    try:
        models = client.models.list()
        for m in models:
            if "generateContent" in m.supported_generation_methods:
                print(f"- {m.name} (Zgodny)")
        print("\n✅ Modele pobrane pomyślnie.")
    except Exception as e:
        print(f"❌ Błąd podczas listowania modeli: {e}")

if __name__ == "__main__":
    asyncio.run(check_available_models())
