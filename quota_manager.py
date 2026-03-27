import logging
import asyncio
from datetime import datetime, timedelta
from google import genai
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QuotaManager")

class ModelStats:
    def __init__(self, name: str, rpm_limit: int, rpd_limit: int):
        self.name = name
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.current_rpm = 0
        self.current_rpd = 0
        self.last_reset_rpm = datetime.now()
        self.is_blocked_until = None

    def can_use(self) -> bool:
        now = datetime.now()
        # Reset RPM counter if a minute has passed
        if now - self.last_reset_rpm > timedelta(minutes=1):
            self.current_rpm = 0
            self.last_reset_rpm = now
        
        if self.is_blocked_until and now < self.is_blocked_until:
            return False
        if self.current_rpm >= self.rpm_limit:
            return False
        if self.current_rpd >= self.rpd_limit:
            return False
        return True

    def mark_used(self):
        self.current_rpm += 1
        self.current_rpd += 1

    def block_temporary(self, seconds: int = 60):
        self.is_blocked_until = datetime.now() + timedelta(seconds=seconds)
        logger.warning(f"Model {self.name} blocked for {seconds} seconds.")

class QuotaManager:
    def __init__(self):
        # Nowe SDK: Inicjalizacja klienta
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.pool = [
            ModelStats(m["name"], m["rpm"], m["rpd"]) 
            for m in settings.MODEL_POOL
        ]
        self.current_model_stats = self.pool[0]

    def _select_next_model(self) -> bool:
        for stats in self.pool:
            if stats.can_use():
                if self.current_model_stats != stats:
                    logger.info(f"Switching to model: {stats.name}")
                    self.current_model_stats = stats
                return True
        return False

    async def generate_content(self, prompt: str) -> str:
        """
        Generuje treść używając aktualnie dostępnego modelu (nowe SDK google-genai).
        W przypadku wyczerpania limitów (429) rotuje modele.
        """
        while True:
            if self._select_next_model():
                try:
                    self.current_model_stats.mark_used()
                    # Nowe SDK: Asynchroniczne wywołanie
                    response = await self.client.aio.models.generate_content(
                        model=self.current_model_stats.name,
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    error_str = str(e).lower()
                    # Obsługa limitów i błędów w nowym SDK
                    if "429" in error_str or "quota" in error_str or "limit" in error_str:
                        logger.warning(f"Quota hit for {self.current_model_stats.name}. Blocking and retrying...")
                        self.current_model_stats.block_temporary()
                        continue
                    else:
                        logger.error(f"Error generating content with {self.current_model_stats.name}: {e}")
                        raise e
            else:
                logger.info("All models at RPM limit. Waiting 15s...")
                await asyncio.sleep(15)

quota_manager = QuotaManager()
