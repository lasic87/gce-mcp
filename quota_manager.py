import logging
import asyncio
from datetime import datetime, timedelta
from google import genai
from google.genai import types
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
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.pool = [
            ModelStats(m["name"], m["rpm"], m["rpd"]) 
            for m in settings.MODEL_POOL
        ]
        self.current_model_stats = self.pool[0]

    def _select_next_model(self, force_thinking: bool = False) -> bool:
        """
        Wybiera następny dostępny model. 
        Jeśli force_thinking=True, priorytetyzuje modele z serii 2.5 i 3.
        """
        for stats in self.pool:
            if stats.can_use():
                if force_thinking and not ("2.5" in stats.name or "3" in stats.name):
                    continue
                if self.current_model_stats != stats:
                    logger.info(f"Switching to model: {stats.name}")
                    self.current_model_stats = stats
                return True
        return False

    def get_stats(self) -> list[dict]:
        stats_list = []
        for s in self.pool:
            stats_list.append({
                "name": s.name,
                "rpm": s.current_rpm,
                "rpm_limit": s.rpm_limit,
                "rpd": s.current_rpd,
                "rpd_limit": s.rpd_limit,
                "is_blocked": s.is_blocked_until is not None and datetime.now() < s.is_blocked_until
            })
        return stats_list

    async def close(self):
        """Zamyka sesję asynchroniczną klienta Gemini."""
        try:
            # Nowe SDK Google GenAI używa klienta aio, który należy zamknąć
            await self.client.aio.close()
            logger.info("Gemini client session closed successfully.")
        except Exception as e:
            logger.error(f"Error closing Gemini session: {e}")

    async def generate_content(self, prompt: str, thinking: bool = False) -> str:
        """
        Generuje treść z opcjonalnym wsparciem dla Thinking Mode.
        """
        while True:
            if self._select_next_model(force_thinking=thinking):
                try:
                    self.current_model_stats.mark_used()
                    model_name = self.current_model_stats.name
                    
                    # Konfiguracja Thinking Mode dla wspieranych modeli
                    config = None
                    if thinking:
                        if "models/gemini-3" in model_name:
                            logger.info(f"Enabling HIGH reasoning for {model_name}")
                            config = types.GenerateContentConfig(
                                thinking_config=types.ThinkingConfig(
                                    thinking_level=types.ThinkingLevel.HIGH
                                )
                            )
                        elif "models/gemini-2.5" in model_name:
                            logger.info(f"Enabling 2048 token thinking budget for {model_name}")
                            config = types.GenerateContentConfig(
                                thinking_config=types.ThinkingConfig(
                                    thinking_budget=2048
                                )
                            )

                    response = await self.client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    
                    # Logowanie myśli (jeśli model je zwrócił)
                    thoughts = []
                    for part in response.candidates[0].content.parts:
                        if part.thought:
                            thoughts.append(part.text)
                    
                    if thoughts:
                        logger.info(f"Model thought: {' '.join(thoughts)[:200]}...")
                        
                    return response.text
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "quota" in error_str or "limit" in error_str:
                        logger.warning(f"Quota hit for {self.current_model_stats.name}. Blocking and retrying...")
                        self.current_model_stats.block_temporary()
                        continue
                    else:
                        logger.error(f"Error generating content with {self.current_model_stats.name}: {e}")
                        raise e
            else:
                logger.info("No suitable models available. Waiting 15s...")
                await asyncio.sleep(15)

quota_manager = QuotaManager()
