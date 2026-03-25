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

## ✨ Key Features / Główne Funkcje

### 💾 Persistent Memory / Pamięć Trwała
*   **EN:** Store facts, preferences, and bug fixes in a high-performance vector database (**LanceDB**).
*   **PL:** Przechowuj fakty i rozwiązania problemów w wydajnej bazie wektorowej (**LanceDB**).

### 🔍 Hybrid Search / Wyszukiwanie Hybrydowe
*   **EN:** Semantic + Keyword matching with **RRF reranking** for pinpoint accuracy.
*   **PL:** Połączenie wyszukiwania semantycznego i słów kluczowych (RRF) dla maksymalnej trafności.

### 🏗️ Architectural Awareness / Świadomość Architektury
*   **EN:** Index your codebase, Proxmox configs, Docker setups, and documentation.
*   **PL:** Indeksuj kod źródłowy, konfiguracje Proxmox, Docker oraz dokumentację.

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

## 📄 License
Licensed under the **MIT License**.
Built with ❤️ for the Homelab community.
