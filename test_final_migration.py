import asyncio
import os
from google import genai
from dotenv import load_dotenv

async def test_migration():
    load_dotenv("/root/gce-mcp/.env")
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Model dokładnie z Twojej listy config.py
    model_name = "models/gemini-3.1-flash-lite-preview"
    
    print(f"Próba wywołania {model_name} przez nowe SDK...")
    try:
        response = await client.aio.models.generate_content(
            model=model_name,
            contents="TEST"
        )
        print(f"Sukces! Odpowiedź: {response.text}")
    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    asyncio.run(test_migration())
