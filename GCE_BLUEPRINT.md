# GCE (Gemini Context Engine) - System Blueprint & Memory

## 1. Cel i Wizja (L0 Context)
GCE to autorski, lekki i ultrawydajny silnik bazy danych kontekstu, stworzony jako natywny serwer **MCP (Model Context Protocol)**. Został zbudowany od zera, aby zastąpić OpenGCE, eliminując problemy z blokadami SQLite, nieczytelnymi URI oraz wąskim gardłem wektoryzacji na procesorze Intel N100.

## 2. Architektura Techniczna (L1 Context)
- **Serwer MCP**: `server.py` (FastMCP) – integruje się bezpośrednio z Gemini CLI.
- **Baza Wektorowa**: **LanceDB** (folder `/root/gce-mcp/data/lancedb`) – serverless, format Apache Arrow, brak dodatkowych procesów, brak blokad zapisu.
- **Wektoryzacja (L2)**: Lokalna **Ollama** na hoście z wymuszoną akceleracją **iGPU Vulkan** (`OLLAMA_VULKAN=1`). Model: `nomic-embed-text`.
- **Model Juggler (QuotaManager)**: Zarządza pulą 7 modeli (Gemini 3.1 Flash Lite, 2.5 Flash oraz Gemma 3 1b-27b). Priorytetyzuje najwyższe limity RPD (np. Gemma 3 IT - 14k RPD) i rotuje klucze API.

## 3. Zaawansowane Funkcjonalności
- **Hybrid Search**: Autorska metoda łącząca Semantic Search (Vector) i Keyword Search (FTS).
- **Smart Abstracting**: Model Juggler generuje streszczenie pliku (L0) przed jego zindeksowaniem.
- **Safe Indexing (GCE-Safe)**: Priorytet `nice 19` i opóźnienia dla ochrony usług krytycznych (router).

## 4. Mapa Projektu (File Map)
- `/root/gce-mcp/server.py`: Główny punkt wejścia MCP (Narzędzia: `gce_add_resource`, `gce_add_memory`, `gce_search_context`).
- `/root/gce-mcp/quota_manager.py`: Silnik rotacji modeli.
- `/root/gce-mcp/vector_store.py`: Logika LanceDB i Hybrid Search.
- `/root/gce-mcp/embedding_engine.py`: Interfejs do Ollama Vulkan.
- `/root/gce-mcp/config.py`: Konfiguracja limitów i ścieżek.

## 5. Aktualny Stan (Current State)
- **Homelab & SOR App**: Pełny indeks (257+ fragmentów).
- **GPU Acceleration**: Aktywna (iGPU Alder Lake-N).

## 6. Protokół Proaktywnej Pamięci (Agent Instruction)
GCE nakłada na Agenta obowiązek proaktywnego zarządzania wiedzą:
1. **Wykrywanie Sygnału**: Jeśli Agent rozwiąże skomplikowany błąd, ustali nową preferencję użytkownika lub dokona ważnej zmiany architektonicznej, musi uznać to za "High-Signal Info".
2. **Potwierdzenie (ask_user)**: Agent NIE zapisuje wspomnienia automatycznie. Musi zapytać: *"Wykryłem ważne rozwiązanie [Opis]. Czy chcesz zapisać to w GCE Memories pod etykietą [Sugerowana Etykieta]?"*.
3. **Utrwalenie (gce_add_memory)**: Po uzyskaniu zgody (Tak), Agent wywołuje `gce_add_memory(content, label)`, co zapisuje fakt pod czytelnym URI `gce://user/memories/...`.

*Dokument ten jest częścią pamięci trwałej GCE pod URI: gce://gce/blueprint*
