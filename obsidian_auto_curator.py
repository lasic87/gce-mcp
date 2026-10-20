#!/root/gce-mcp/.venv/bin/python3
import sys
import os
import re
import asyncio
from datetime import datetime

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from quota_manager import QuotaManager
from server import gce_add_resource
from obsidian_diff_arbiter import process_note_memory_diff, is_in_memory_scope

quota_manager = QuotaManager()

def has_yaml_frontmatter(content: str) -> bool:
    """Sprawdza, czy notatka ma już poprawny nagłówek YAML frontmatter."""
    stripped = content.strip()
    if not stripped.startswith("---"):
        return False
    # Szukamy zamykającego '---'
    parts = stripped.split("---", 2)
    if len(parts) >= 3:
        frontmatter_block = parts[1]
        # Sprawdzamy czy zawiera kluczowe pola
        if "title:" in frontmatter_block or "tags:" in frontmatter_block:
            return True
    return False

def clean_llm_response(text: str) -> str:
    """Usuwa ewentualne otaczające bloki kodu markdown wygenerowane przez LLM."""
    cleaned = text.strip()
    if cleaned.startswith("```markdown"):
        cleaned = cleaned[len("```markdown"):].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned

async def curate_note(file_path: str, mode: str = "modified"):
    vault_base = "/root/vault"
    abs_path = os.path.join(vault_base, file_path) if not file_path.startswith("/") else file_path

    if not abs_path.endswith(".md"):
        return

    if mode == "deleted" or not os.path.exists(abs_path):
        if is_in_memory_scope(abs_path):
            await process_note_memory_diff(abs_path, mode="deleted")
        return

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
    except Exception as e:
        print(f"Błąd odczytu {abs_path}: {e}")
        return

    # KROK 0: Diff-Arbiter dla pamięci GCE (synchronizacja zmian do LanceDB namespace='memories')
    if is_in_memory_scope(abs_path, raw_content):
        try:
            diff_res = await process_note_memory_diff(abs_path, mode)
            if diff_res and any(diff_res.values()):
                print(f"⚡ [Diff-Arbiter] Zsynchronizowano wspomnienia: {diff_res}")
        except Exception as e:
            print(f"❌ [Diff-Arbiter] Błąd synchronizacji wspomnień: {e}")

    base_name = os.path.splitext(os.path.basename(abs_path))[0]
    today = datetime.now().strftime("%Y-%m-%d")

    # KROK 1: Formatowanie jeśli brak frontmattera
    if not has_yaml_frontmatter(raw_content) and raw_content.strip():
        print(f"🧹 [Auto-Curator] Wykryto surową notatkę bez frontmattera: {base_name}")
        prompt = f"""Jesteś kuratorem wiedzy w systemie Obsidian Vault połączonym z Gemini Context Engine (GCE).
Twoim zadaniem jest przekształcić poniższą surową notatkę użytkownika w profesjonalną, zunifikowaną notatkę Obsidian.

WYMAGANIA:
1. Dodaj na początku poprawny nagłówek YAML frontmatter:
---
title: <Czytelny tytuł, np. nawiązujący do {base_name} lub tematu>
tags: [<3-5 trafnych tagów w lowercase, np. git, dev, homelab, idea, research, links>]
created: {today}
updated: {today}
type: note
---
2. Pod frontmatterem dodaj główny nagłówek markdown: # <Tytuł>.
3. BEZWZGLĘDNIE ZACHOWAJ 100% TREŚCI UŻYTKOWNIKA! Nie usuwaj żadnego linku, słowa ani notatki.
4. Możesz poprawić czytelność (estetyczne punktory, sekcje, poprawne linki), ale nie wymyślaj faktów, których użytkownik nie podał.
5. Zwróć TYLKO czysty tekst notatki w markdownie (zaczynając od ---). Żadnych wstępów i komentarzy.

SUROWA NOTATKA:
{raw_content}
"""
        try:
            formatted = await quota_manager.generate_content(prompt)
            formatted = clean_llm_response(formatted)

            # Bezpiecznik: upewniamy się, że odpowiedź zaczyna się od ---
            if formatted.startswith("---"):
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(formatted + "\n")
                print(f"✨ [Auto-Curator] Pomyślnie zunifikowano i zapisano: {abs_path}")
            else:
                print(f"⚠️ [Auto-Curator] LLM nie wygenerował poprawnego frontmattera, zachowano oryginał.")
        except Exception as e:
            print(f"❌ [Auto-Curator] Błąd formatowania przez AI: {e}")

    # KROK 2: Indeksowanie do GCE LanceDB
    try:
        res = await gce_add_resource(abs_path, namespace="obsidian")
        print(f"🧠 [GCE Indexer] {res}")
    except Exception as e:
        print(f"❌ [GCE Indexer] Błąd indeksowania: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        action_mode = sys.argv[2] if len(sys.argv) > 2 else "modified"
        asyncio.run(curate_note(target_file, action_mode))
