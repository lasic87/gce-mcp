# Gemini Context Engine (GCE)

**Gemini Context Engine (GCE)** to system pamięci długoterminowej i świadomości kodu (deep code awareness), zaprojektowany na potrzeby integracji agentów AI (np. Cline, Claude Desktop, Cursor) z moim środowiskiem **Homelab**.

## 🚀 Cel projektu
GCE rozwiązuje problem ograniczonych okien kontekstowych modeli, zapewniając im trwały, wektorowy dostęp do wiedzy o infrastrukturze, historii decyzji oraz bazach kodu, przy jednoczesnym zachowaniu pełnej prywatności wewnątrz lokalnej sieci.

---

## 🏗️ Architektura systemu

GCE opiera się na stosie technologicznym zoptymalizowanym pod kątem wydajności na sprzęcie konsumenckim (iGPU):

### 1. Warstwa Modelowa: Ollama + iGPU
*   **Silnik:** [Ollama](https://ollama.com/) z akceleracją sprzętową na iGPU (Intel QuickSync/Arc) dla wydajnej inferencji LLM.
*   **Orkiestracja:** **Juggler v3** – autorski system przełączania między modelami (np. dobór modelu *coding-focused* vs *reasoning-focused* w zależności od zadania).

### 2. Warstwa Pamięci: LanceDB
*   **Baza danych:** [LanceDB](https://lancedb.com/) – bezserwerowa, natywna dla wektorów baza danych, zoptymalizowana pod kątem szybkości i niskiego zużycia zasobów (idealna dla NAS/Homelab).
*   **Funkcja:** Przechowywanie osadzeń (embeddings) całych repozytoriów kodu oraz logów działań w systemie.

### 3. Warstwa Integracji: MCP (Model Context Protocol)
*   **Standard:** [MCP](https://modelcontextprotocol.io/) pozwala agentom na ustandaryzowany dostęp do narzędzi (tools), plików i baz danych GCE.
*   **Rola:** Umożliwia podpięcie zewnętrznych klientów (np. Cline, Claude Desktop, Cursor) do mojego lokalnego "mózgu" GCE.

---

## 🛠️ Kluczowe komponenty

| Komponent | Technologia | Rola |
| :--- | :--- | :--- |
| **Ingestion Engine** | Python / Tree-sitter | Parsowanie kodu i tworzenie semantycznych chunków. |
| **Vector Store** | LanceDB | Przechowywanie i wyszukiwanie kontekstu (RAG). |
| **Orchestrator** | Juggler v3 | Dynamiczne zarządzanie modelem (routing zapytań). |
| **Interface** | MCP Server | Standardowe API dla agentów AI. |

---

## 📋 Roadmapa

- [ ] **Phase 1: Foundation.** Implementacja serwera MCP z obsługą LanceDB.
- [ ] **Phase 2: RAG Pipeline.** Opracowanie indeksowania kodu za pomocą Tree-sitter dla lepszego zrozumienia struktury projektów.
- [ ] **Phase 3: Juggler v3 Integration.** Implementacja inteligentnego routingu modeli przez Ollama.
- [ ] **Phase 4: Homelab Dashboard.** Prosty interfejs monitorujący stan pamięci wektorowej i zużycie zasobów iGPU.

---

## 💻 Wymagania systemowe
*   **OS:** Linux (zalecany Docker/Podman).
*   **Hardware:** 
    *   CPU: Obsługa instrukcji AVX2.
    *   GPU: Intel iGPU (Gen12+ / Iris Xe / Arc) dla Ollama.
    *   Storage: NVMe SSD (zalecane dla szybkich operacji na LanceDB).
*   **Memory:** Min. 16GB RAM (zależnie od rozmiaru kwantyzacji LLM).

---

## 🤝 Współpraca
Projekt jest w fazie wczesnego rozwoju (PoC). Zapraszam do zgłaszania Issues oraz Pull Requestów dotyczących optymalizacji zapytań wektorowych w LanceDB oraz integracji z nowymi modelami w Ollama.

---
*GCE: Knowledge that stays home.*