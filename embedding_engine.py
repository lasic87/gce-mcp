import aiohttp
import logging
from typing import List
from config import settings

logger = logging.getLogger("EmbeddingEngine")

class EmbeddingEngine:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.EMBEDDING_MODEL
        # Zakładamy, że Ollama jest już poprawnie skonfigurowana z OLLAMA_VULKAN=1 na poziomie środowiska systemu.

    async def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding vector for the given text using local Ollama.
        """
        url = f"{self.host}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise e

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a batch of texts concurrently.
        """
        import asyncio
        tasks = [self.embed_text(text) for text in texts]
        return await asyncio.gather(*tasks)

embedding_engine = EmbeddingEngine()
