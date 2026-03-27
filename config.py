import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv() # Ładowanie klucza z /root/gce-mcp/.env

class Settings(BaseSettings):
    GCE_DB_PATH: str = "/root/gce-mcp/data/lancedb"
    OLLAMA_HOST: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "nomic-embed-text" # Możemy zmienić na inny wspierany przez Ollamę
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Parametry fragmentacji tekstu
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 200
    
    # Modele do Juggler'a (nazwa, rpm_limit, rpd_limit)
    MODEL_POOL: list[dict] = [
        {"name": "models/gemini-3.1-flash-lite-preview", "rpm": 15, "rpd": 500},
        {"name": "models/gemini-2.5-flash-lite", "rpm": 10, "rpd": 20},
        {"name": "models/gemini-2.5-flash", "rpm": 5, "rpd": 20},
        {"name": "models/gemma-3-27b-it", "rpm": 25, "rpd": 14000},
        {"name": "models/gemma-3-12b-it", "rpm": 25, "rpd": 14000},
        {"name": "models/gemma-3-4b-it", "rpm": 25, "rpd": 14000},
        {"name": "models/gemma-3-1b-it", "rpm": 25, "rpd": 14000}
    ]

settings = Settings()
