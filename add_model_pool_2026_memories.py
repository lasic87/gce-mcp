import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv("/root/gce-mcp/.env")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "gce_model_pool_update_2026",
            "content": "Zaktualizowano pulę darmowych modeli GCE w config.py (2026-10-01). Usunięto 8 niedziałających modeli (Gemma 3 wycofana z v1beta - 404, Gemma 4 niestabilna - 500, Gemini 3.1 Pro preview i Deep Research wymagające płatnego planu - 429). Nowa pula oparta jest o 9 zweryfikowanych modeli Flash: gemini-3.6-flash (główny model roboczy), gemini-3.5-flash-lite, gemini-3.8-flash, gemini-3.1-flash-lite, gemini-flash-lite-latest, gemini-3-flash-preview, gemini-3.1-flash-lite-preview, gemini-2.5-flash, gemini-2.5-flash-lite."
        },
        {
            "label": "gce_quotamanager_503_resilience",
            "content": "W quota_manager.py zaimplementowano odporność na błędy 503 UNAVAILABLE oraz przeciążenia (high demand) po stronie Google API. Gdy wybrany model zwróci błąd 503 lub informację o przeciążeniu, QuotaManager natychmiast blokuje go tymczasowo (na 60s) i płynnie przełącza na kolejny model z MODEL_POOL bez przerywania operacji GCE."
        }
    ]
    
    for mem in memories:
        print(f"Adding memory with label: {mem['label']}...")
        try:
            res = await gce_add_memory(content=mem['content'], label=mem['label'], namespace="memories")
            print(f"Result for {mem['label']}: {res}")
        except Exception as e:
            print(f"Error for {mem['label']}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
