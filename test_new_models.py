import asyncio
import logging
from google import genai
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelTest")

async def test_models():
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    models_to_test = [
        "models/gemini-3-flash-preview",
        "models/gemini-3-pro-preview",
        "models/gemma-4-e2b-it"
    ]
    
    for model_name in models_to_test:
        try:
            logger.info(f"Testing model: {model_name}")
            response = await client.aio.models.generate_content(
                model=model_name,
                contents="Say 'Hello, GCE!'"
            )
            logger.info(f"SUCCESS {model_name}: {response.text.strip()}")
        except Exception as e:
            logger.error(f"FAILED {model_name}: {e}")

if __name__ == "__main__":
    asyncio.run(test_models())
