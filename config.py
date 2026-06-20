import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv() # Ładowanie klucza z /root/gce-mcp/.env

class Settings(BaseSettings):
    GCE_DB_PATH: str = "/root/gce-mcp/data/lancedb"
    KG_DB_PATH: str = "/root/gce-mcp/data/knowledge_graph.sqlite3"
    OLLAMA_HOST: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "nomic-embed-text" # Możemy zmienić na inny wspierany przez Ollamę
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Parametry fragmentacji tekstu
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 200
    
    # GCE 2.2: Stabilność i Inteligentne Indeksowanie
    INDEX_CACHE_PATH: str = "/root/gce-mcp/data/index_cache.json"
    THROTTLE_DELAY: float = 0.5  # Sekundy przerwy dla ochrony CPU/Routera
    IGNORE_PATTERNS: list[str] = [
        "node_modules", ".git", ".venv", "__pycache__", 
        "dist", ".next", "build", ".cache", ".npm"
    ]
    
    # GCE 2.3: Orchestrator Ready
    PROJECT_CONTEXT_DIR: str = ".gce" # Folder bazy wiedzy wewnątrz projektu
    
    # Modele do Juggler'a (nazwa, rpm_limit, rpd_limit)
    MODEL_POOL: list[dict] = [
        {"name": "models/gemini-3.1-flash-lite-preview", "rpm": 15, "rpd": 500},
        {"name": "models/gemini-3-flash-preview", "rpm": 15, "rpd": 1000},
        {"name": "models/gemini-3.1-pro-preview", "rpm": 5, "rpd": 50},
        {"name": "models/deep-research-pro-preview-12-2025", "rpm": 2, "rpd": 10},
        {"name": "models/gemini-2.5-flash-lite", "rpm": 10, "rpd": 20},
        {"name": "models/gemini-2.5-flash", "rpm": 5, "rpd": 20},
        {"name": "models/gemma-4-31b-it", "rpm": 25, "rpd": 14000},
        {"name": "models/gemma-4-26b-a4b-it", "rpm": 25, "rpd": 14000},
        {"name": "models/gemma-3-27b-it", "rpm": 25, "rpd": 14000},
        {"name": "models/gemma-3-12b-it", "rpm": 25, "rpd": 14000},
        {"name": "models/gemma-3-4b-it", "rpm": 25, "rpd": 14000},
        {"name": "models/gemma-3-1b-it", "rpm": 25, "rpd": 14000}
    ]

settings = Settings()
