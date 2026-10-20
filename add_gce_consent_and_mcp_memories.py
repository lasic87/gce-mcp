import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "gce_mcp_and_cli_auto_approval_config_2026",
            "content": "Zarejestrowano GCE jako natywny serwer MCP w Antigravity CLI pod adresem http://127.0.0.1:8112/sse (za pomocą agy mcp add gce http://127.0.0.1:8112/sse). Skonfigurowano uprawnienia w /root/.gemini/antigravity-cli/settings.json, dodając mcp(gce/*) oraz command(/root/gce-mcp/.venv/bin/python3) do listy permissions.allow, co eliminuje konieczność ręcznego potwierdzania każdego wywołania w terminalu."
        },
        {
            "label": "gce_session_consent_protocol_2026",
            "content": "Wdrożono protokół zgody sesyjnej (Session-Level Consent Protocol) dla GCE w GEMINI.md: odczyt (wyszukiwanie kontekstu w GCE) jest zawsze w 100% automatyczny i cichy w tle, natomiast potwierdzenie operacji zapisu i konsolidacji wiedzy wymagane jest tylko jednorazowo w danej sesji roboczej. Po pojedynczym zatwierdzeniu przez użytkownika, wszelkie kolejne zapytania, odczyty oraz zapisy do GCE w ramach tej samej sesji są zatwierdzane i realizowane w pełni automatycznie."
        },
        {
            "label": "obsidian_livesync_gce_pipeline_verified",
            "content": "Zweryfikowano działanie pipeline'u automatycznej synchronizacji i indeksowania notatek Obsidian do GCE: zmiany w Obsidian są przesyłane przez livesync-bridge.service (CouchDB <-> /root/vault), po czym skrypt /root/gce-mcp/obsidian_auto_curator.py automatycznie dba o poprawny YAML frontmatter i indeksuje zasoby w LanceDB w przestrzeni nazw 'obsidian'. Potwierdzono poprawne zaindeksowanie pliku /root/vault/Memories/Linki do zbadania.md."
        }
    ]

    for mem in memories:
        lbl = mem["label"]
        cnt = mem["content"]
        print("Adding memory:", lbl)
        try:
            res = await gce_add_memory(content=cnt, label=lbl)
            print("Result for", lbl, ":", res)
        except Exception as e:
            print("Error for", lbl, ":", e)

if __name__ == "__main__":
    asyncio.run(main())
