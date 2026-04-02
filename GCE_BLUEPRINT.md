# GCE (Gemini Context Engine) - System Blueprint & Memory

## 1. Cel i Wizja (L0 Context)
GCE to autorski, lekki i ultrawydajny silnik bazy danych kontekstu, stworzony jako natywny serwer **MCP (Model Context Protocol)**. Został zbudowany od zera, aby zastąpić OpenGCE, eliminując problemy z blokadami SQLite, nieczytelnymi URI oraz wąskim gardłem wektoryzacji na procesorze Intel N100.

## 2. Architektura Techniczna (L1 Context)
- **Serwer MCP**: `server.py` (FastMCP) – wersja **2.4 Guardian & Wisdom**.
- **Baza Wektorowa**: **LanceDB** (folder `/root/gce-mcp/data/lancedb`) – serverless, format Apache Arrow, brak dodatkowych procesów, brak blokad zapisu.
- **Wektoryzacja (L2)**: Lokalna **Ollama** na hoście z wymuszoną akceleracją **iGPU Vulkan** (`OLLAMA_VULKAN=1`). Model: `nomic-embed-text`.
- **Model Juggler (QuotaManager)**: Zarządza pulą 7 modeli (Gemini 3.1 Flash Lite, 2.5 Flash oraz Gemma 3 1b-27b). Priorytetyzuje najwyższe limity RPD (np. Gemma 3 IT - 14k RPD) i rotuje klucze API.

## 3. Zaawansowane Funkcjonalności (v2.4)
- **Hybrid Search**: Semantic Search (Vector) + Keyword Search (FTS).
- **Smart Splitter (v2.1)**: Inteligentne dzielenie tekstu zależne od języka (Python, JS, TS, Markdown).
- **Auto-Graph Extraction (v2.1)**: Automatyczne wykrywanie importów i zależności.
- **MD5 Smart Cache (v2.2)**: Oszczędność GPU i RPD poprzez unikanie re-indeksowania niezmienionych plików.
- **Smart Throttle (v2.2)**: 2s opóźnienia między operacjami dla ochrony procesora N100 i routera.
- **Project Wisdom (v2.3)**: Ustrukturyzowana baza wiedzy w folderze `.gce/` (PROJECT, DECISIONS, KNOWLEDGE, REQUIREMENTS).
- **GCE Doctor (v2.4)**: System autodiagnostyki i naprawy silnika (Ollama/DB/FTS).
- **Rule Engine (v2.4)**: Trwałe zasady projektowe i globalne (`gce_add_rule`).
- **Requirement Tracker (v2.4)**: Śledzenie statusu i dowodów (Evidence) spełnienia wymagań.

## 4. Mapa Projektu (File Map)
- `/root/gce-mcp/server.py`: Główny punkt wejścia MCP.
- `/root/gce-mcp/quota_manager.py`: Silnik rotacji modeli.
- `/root/gce-mcp/vector_store.py`: Logika LanceDB i Hybrid Search.
- `/root/gce-mcp/text_utils.py`: Silnik fragmentacji (Language-Aware Splitter).
- `/root/gce-mcp/embedding_engine.py`: Interfejs do Ollama Vulkan.
- `/root/gce-mcp/config.py`: Konfiguracja limitów i ścieżek.

## 5. Aktualny Stan (Current State)
- **Homelab & SOR App**: Pełny indeks (898+ fragmentów).
- **Wersja**: 2.4 (Guardian & Wisdom)
- **GPU Acceleration**: Aktywna (iGPU Alder Lake-N).


## 6. Protokół Proaktywnej Pamięci (Agent Instruction)
GCE nakłada na Agenta obowiązek proaktywnego zarządzania wiedzą:
1. **Wykrywanie Sygnału**: Jeśli Agent rozwiąże skomplikowany błąd, ustali nową preferencję użytkownika lub dokona ważnej zmiany architektonicznej, musi uznać to za "High-Signal Info".
2. **Potwierdzenie (ask_user)**: Agent NIE zapisuje wspomnienia automatycznie. Musi zapytać: *"Wykryłem ważne rozwiązanie [Opis]. Czy chcesz zapisać to w GCE Memories pod etykietą [Sugerowana Etykieta]?"*.
3. **Utrwalenie (gce_add_memory)**: Po uzyskaniu zgody (Tak), Agent wywołuje `gce_add_memory(content, label)`, co zapisuje fakt pod czytelnym URI `gce://user/memories/...`.

*Dokument ten jest częścią pamięci trwałej GCE pod URI: gce://gce/blueprint*
