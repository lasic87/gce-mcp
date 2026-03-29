import aiohttp
import logging
import asyncio
from typing import List, Optional
from config import settings

logger = logging.getLogger("EmbeddingEngine")

class EmbeddingEngine:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.EMBEDDING_MODEL
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Returns a singleton-like session for the engine."""
        if self._session is None or self._session.closed:
            # Używamy TCPConnector z limitami, aby nie przeciążyć stosu sieciowego
            connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self):
        """Closes the underlying session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding vector for the given text using local Ollama.
        Reuses the session for efficiency.
        """
        url = f"{self.host}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            raise e

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a batch of texts concurrently using the shared session.
        """
        tasks = [self.embed_text(text) for text in texts]
        return await asyncio.gather(*tasks)

embedding_engine = EmbeddingEngine()
