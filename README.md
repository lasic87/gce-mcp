# 🧠 GCE-MCP (Gemini Context Engine)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-blue.svg)](https://modelcontextprotocol.io/)

> **EN:** The missing memory layer for your AI Homelab Assistant.
> **PL:** Brakująca warstwa pamięci dla Twojego asystenta AI w Homelabie.

---

## 🚀 Overview / Przegląd

**GCE-MCP** is a context management engine built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It provides long-term memory and deep architectural awareness for LLMs.

**GCE-MCP** to silnik zarządzania kontekstem oparty na protokole MCP. Zapewnia asystentom AI trwałą pamięć oraz głęboką świadomość architektury Twojego środowiska.

---

## 🛠️ Technical Deep Dive / Szczegóły Techniczne

**GCE-MCP** is more than just a simple database. It uses advanced strategies to handle large-scale homelab data efficiently.

**GCE-MCP** to coś więcej niż zwykła baza danych. Wykorzystuje zaawansowane strategie do wydajnego zarządzania danymi homelaba.

### 🧠 Smart Abstracting / Inteligentne Streszczanie
*   **EN:** To avoid hitting token limits, GCE generates "Smart Abstracts" before indexing large files. This allows the LLM to understand the *intent* and *structure* of a 500-line config file using only 10-20 tokens.
*   **PL:** Aby uniknąć limitów tokenów, GCE generuje streszczenia przed indeksowaniem dużych plików. Pozwala to asystentowi AI zrozumieć *intencję* i *strukturę* pliku konfiguracyjnego bez czytania setek linii kodu.

### 🔍 Hybrid RRF Search / Wyszukiwanie Hybrydowe
*   **EN:** We combine **Semantic Vector Search** (understanding meaning) with **Full-Text BM25 Search** (matching specific keywords like IP addresses or ports). Results are merged using **Reciprocal Rank Fusion (RRF)** for unparalleled relevance.
*   **PL:** Łączymy **wyszukiwanie semantyczne** (rozumienie znaczenia) z **tradycyjnym wyszukiwaniem tekstowym** (dopasowanie IP, portów itp.). Wyniki są łączone za pomocą algorytmu **RRF**, co gwarantuje najwyższą trafność.

### 🧬 Atomic Fact Consolidation / Konsolidacja Faktów
*   **EN:** GCE can analyze a long conversation and extract "Atomic Facts" — single, unambiguous truths about your system (e.g., *"Frigate uses LXC 150"*). This cleans the context and prevents "context pollution" from chat noise.
*   **PL:** GCE analizuje całe sesje i wyodrębnia "fakty atomowe" — pojedyncze, jednoznaczne prawdy o systemie (np. *"Frigate działa na LXC 150"*). Pozwala to oczyścić pamięć z nieistotnych informacji i "szumu" rozmowy.

---

## ✨ Key Features / Główne Funkcje

*   **💾 Persistent Memory**: Store facts, preferences, and fixes in **LanceDB**.
*   **🔍 Hybrid Search**: Semantic + Keyword matching with **RRF**.
*   **🏗️ Architectural Awareness**: Index your codebase, Proxmox, Docker, and HA configs.

---

## 💡 Usage Examples / Przykłady Użycia

### 🧠 "Remember this fix" / "Zapamiętaj to rozwiązanie"
> *User:* "GCE, remember that for the MediaStack LXC, we need to set `shm_size: 2g` for FlareSolverr."
> *GCE:* "Zapamiętano: gce://user/memories/mediastack_shm_fix"

### 🔍 "How is my network configured?" / "Jak wygląda moja sieć?"
> *User:* "What is the IP of my Frigate instance and where is its config stored?"
> *AI (via GCE):* "Frigate is at `192.168.1.15`, config: `/opt/frigate/config.yml` (LXC 150)."

---

## 🚀 Quick Start / Szybki Start

```bash
git clone https://github.com/lasic87/gce-mcp.git
cd gce-mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # Add your GOOGLE_API_KEY
python server.py
```

---

## 🛠️ Configuration / Konfiguracja (Gemini CLI)

```json
{
  "mcpServers": {
    "gce": {
      "command": "python",
      "args": ["/path/to/gce-mcp/server.py"],
      "env": { "GOOGLE_API_KEY": "your-key-here" }
    }
  }
}
```

---

## 🤝 Contribution / Rozwój projektu

**EN:** This project is in active development. If you find it useful, please feel free to open an **Issue** or submit a **Pull Request**. Let's build the best homelab memory together!

**PL:** Projekt jest aktywnie rozwijany. Jeśli uznasz go za przydatny, śmiało otwieraj **Issue** lub wysyłaj **Pull Requesty**. Zbudujmy razem najlepszą pamięć dla homelaba!

---

## 📄 License
Licensed under the **MIT License**.
Built with ❤️ for the Homelab community.
