#!/root/gce-mcp/.venv/bin/python3
import os
import sys
import json
import re
import difflib
import hashlib
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Ensure gce-mcp path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import settings
from vector_store import vector_store
from embedding_engine import embedding_engine
from quota_manager import QuotaManager

logger = logging.getLogger("ObsidianDiffArbiter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [DiffArbiter] %(message)s")

SNAPSHOT_FILE = "/root/gce-mcp/data/obsidian_snapshots.json"
VAULT_BASE = "/root/vault"
MEMORIES_DIR = os.path.join(VAULT_BASE, "Memories")

quota_manager = QuotaManager()

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_snapshots() -> Dict[str, dict]:
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Błąd odczytu {SNAPSHOT_FILE}: {e}")
    return {}

def save_snapshots(snapshots: Dict[str, dict]):
    os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
    tmp_file = f"{SNAPSHOT_FILE}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, SNAPSHOT_FILE)

def extract_clean_lines(content: str) -> List[str]:
    """Wyciąga czyste linie faktów z notatki, ignorując frontmatter i nagłówki."""
    lines = content.splitlines()
    in_frontmatter = False
    clean = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue

        if not stripped:
            continue
        if stripped.startswith("#"):
            continue

        # Usunięcie punktorów listy (- , * , 1. )
        normalized = re.sub(r'^(\*|-|\d+\.)\s+', '', stripped).strip()
        if len(normalized) > 5:
            clean.append(normalized)

    return clean

def is_in_memory_scope(file_path: str, content: str = "") -> bool:
    """Sprawdza, czy plik należy do strefy pamięci (folder Memories lub tag #memory)."""
    norm_path = os.path.abspath(file_path)
    if norm_path.startswith(os.path.abspath(MEMORIES_DIR)):
        return True
    if content:
        if "type: memory" in content or "tags:" in content and "memory" in content:
            return True
    return False

def record_gce_write(file_path: str, content: str):
    """Rejestruje zapis wykonany przez GCE, aby zapobiec pętli zwrotnej (Loop Suppression)."""
    snapshots = load_snapshots()
    clean_lines = extract_clean_lines(content)
    snapshots[file_path] = {
        "hash": compute_hash(content),
        "lines": clean_lines,
        "last_author": "gce",
        "updated_at": datetime.now().isoformat()
    }
    save_snapshots(snapshots)
    logger.info(f"🛡️ [LoopSuppression] Zarejestrowano zapis GCE dla: {file_path}")

def write_memory_to_vault(content: str, label: str, category: str = "general") -> str:
    """
    Zapisuje/dokleja fakt do odpowiedniej notatki w /root/vault/Memories/
    i oznacza go flagą last_author='gce'.
    """
    os.makedirs(MEMORIES_DIR, exist_ok=True)
    
    # Wybór odpowiedniego pliku tematycznego
    cat_lower = category.lower()
    label_lower = label.lower()
    content_lower = content.lower()
    
    if any(k in cat_lower or k in label_lower or k in content_lower for k in ["homelab", "proxmox", "lxc", "n100", "opnsense", "network", "storage", "dysk"]):
        target_file = os.path.join(MEMORIES_DIR, "Homelab.md")
        title = "Homelab & Infrastruktura"
        tag = "homelab"
    elif any(k in cat_lower or k in label_lower or k in content_lower for k in ["sor_app", "medical", "sor"]):
        target_file = os.path.join(MEMORIES_DIR, "SOR_App.md")
        title = "SOR App Projekt"
        tag = "sor_app"
    elif any(k in cat_lower or k in label_lower or k in content_lower for k in ["rule", "zasada", "protocol"]):
        target_file = os.path.join(MEMORIES_DIR, "Zasady_i_Preferencje.md")
        title = "Zasady i Preferencje"
        tag = "rules"
    else:
        target_file = os.path.join(MEMORIES_DIR, "Wspomnienia.md")
        title = "Baza Wspomnień Ogólnych"
        tag = "general"

    today = datetime.now().strftime("%Y-%m-%d")
    clean_fact = content.strip().replace("\n", " ")
    if not clean_fact.startswith("- "):
        bullet_point = f"- {clean_fact}"
    else:
        bullet_point = clean_fact

    if not os.path.exists(target_file):
        initial_content = f"""---
title: {title}
tags: [memories, gce, {tag}]
created: {today}
updated: {today}
type: memory
---

# {title}

{bullet_point}
"""
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(initial_content)
        record_gce_write(target_file, initial_content)
        logger.info(f"✨ Utworzono nową notatkę pamięci: {target_file}")
    else:
        with open(target_file, "r", encoding="utf-8") as f:
            existing = f.read()

        # Sprawdzamy czy ten fakt już jest
        if clean_fact in existing:
            logger.info(f"ℹ️ Fakt już obecny w {target_file}, pomijam dopisywanie.")
            return target_file

        # Dopisujemy na końcu
        updated_content = existing.rstrip() + "\n" + bullet_point + "\n"
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(updated_content)
        record_gce_write(target_file, updated_content)
        logger.info(f"📝 Dopisano fakt do notatki: {target_file}")

    return target_file

async def semantic_arbitration_mini(new_line: str, candidate_line: str, candidate_uri: str) -> str:
    """Ultra-zwięzły prompt arbitrażu semantycznego (zużycie ~60-80 tokenów)."""
    prompt = f"""Porównaj dwa fakty i określ relację.
Stary fakt ({candidate_uri}): "{candidate_line}"
Nowy fakt: "{new_line}"

Odpowiedz dokładnie JEDNYM słowem:
DUPLICATE - jeśli nowy fakt nie wnosi nic nowego.
SUPERSEDES - jeśli nowy fakt aktualizuje, poprawia lub zastępuje stary.
NO_CONFLICT - jeśli oba fakty powinny współistnieć."""
    try:
        res = await quota_manager.generate_content(prompt)
        res_upper = res.strip().upper()
        if "SUPERSEDES" in res_upper:
            return "SUPERSEDES"
        if "DUPLICATE" in res_upper:
            return "DUPLICATE"
        return "NO_CONFLICT"
    except Exception as e:
        logger.warning(f"Błąd mini-arbitrażu: {e}")
        return "NO_CONFLICT"

async def process_note_memory_diff(file_path: str, mode: str = "modified") -> Dict[str, int]:
    """
    Analizuje diff zmienionej notatki Obsidian i odzwierciedla zmiany w LanceDB namespace='memories'.
    Zwraca podsumowanie operacji: {'added': x, 'updated': y, 'deleted': z}.
    """
    stats = {"added": 0, "updated": 0, "deleted": 0}
    abs_path = os.path.abspath(file_path)
    snapshots = load_snapshots()
    file_snapshot = snapshots.get(abs_path, {})

    if mode == "deleted" or not os.path.exists(abs_path):
        if abs_path in snapshots:
            logger.info(f"🗑️ Usunięto notatkę {abs_path}. Czyszczenie powiązanych wspomnień...")
            old_lines = file_snapshot.get("lines", [])
            for line in old_lines:
                try:
                    vec = await embedding_engine.embed_text(line)
                    cands = await asyncio.to_thread(
                        vector_store.hybrid_search, query=line, query_vector=vec, limit=1, namespace="memories"
                    )
                    if cands:
                        best = cands[0]
                        # Jeśli dystans mały lub tekst pasuje
                        if best.get("text", "").strip() == line.strip():
                            await asyncio.to_thread(vector_store.delete, best["uri"])
                            stats["deleted"] += 1
                            logger.info(f"Usunięto pamięć: {best['uri']}")
                except Exception as e:
                    logger.warning(f"Błąd usuwania pamięci dla linii: {e}")
            del snapshots[abs_path]
            save_snapshots(snapshots)
        return stats

    # Odczyt pliku
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Nie można odczytać {abs_path}: {e}")
        return stats

    if not is_in_memory_scope(abs_path, content):
        return stats

    current_hash = compute_hash(content)

    # 1. Sprawdzenie pętli zwrotnej (Loop Suppression)
    if file_snapshot.get("last_author") == "gce":
        logger.info(f"🛡️ [LoopSuppression] Pominięto re-indeksację własnego zapisu GCE dla: {abs_path}")
        file_snapshot["last_author"] = None
        file_snapshot["hash"] = current_hash
        file_snapshot["lines"] = extract_clean_lines(content)
        snapshots[abs_path] = file_snapshot
        save_snapshots(snapshots)
        return stats

    # 2. Sprawdzenie czy cokolwiek się zmieniło
    if file_snapshot.get("hash") == current_hash:
        return stats

    old_lines = file_snapshot.get("lines", [])
    new_lines = extract_clean_lines(content)

    # Obliczenie różnic (Diff)
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    added_lines = []
    removed_lines = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            removed_lines.extend(old_lines[i1:i2])
            added_lines.extend(new_lines[j1:j2])
        elif tag == 'delete':
            removed_lines.extend(old_lines[i1:i2])
        elif tag == 'insert':
            added_lines.extend(new_lines[j1:j2])

    if not added_lines and not removed_lines:
        file_snapshot["hash"] = current_hash
        file_snapshot["lines"] = new_lines
        snapshots[abs_path] = file_snapshot
        save_snapshots(snapshots)
        return stats

    logger.info(f"⚡ [DiffArbiter] Wykryto zmiany w {os.path.basename(abs_path)}: +{len(added_lines)} / -{len(removed_lines)} linii")

    # 3. Obsługa linii usuniętych
    for line in removed_lines:
        try:
            vec = await embedding_engine.embed_text(line)
            cands = await asyncio.to_thread(
                vector_store.hybrid_search, query=line, query_vector=vec, limit=1, namespace="memories"
            )
            if cands:
                cand = cands[0]
                if cand.get("text", "").strip() == line.strip():
                    await asyncio.to_thread(vector_store.delete, cand["uri"])
                    stats["deleted"] += 1
                    logger.info(f"🗑️ Usunięto nieaktualny fakt z GCE: {cand['uri']}")
        except Exception as e:
            logger.warning(f"Błąd usuwania faktu: {e}")

    # 4. Obsługa linii dodanych / zmodyfikowanych
    file_slug = re.sub(r'[^a-z0-9]', '_', os.path.splitext(os.path.basename(abs_path))[0].lower())
    for line in added_lines:
        try:
            vec = await embedding_engine.embed_text(line)
            cands = await asyncio.to_thread(
                vector_store.hybrid_search, query=line, query_vector=vec, limit=3, namespace="memories"
            )

            # Identyczny fakt już istnieje -> ignorujemy
            if cands and cands[0].get("text", "").strip() == line.strip():
                logger.info(f"ℹ️ Fakt już istnieje w GCE: {cands[0]['uri']}")
                continue

            # Sprawdzenie arbitrażu jeśli mamy bliskiego kandydata
            action = "NO_CONFLICT"
            target_uri = None
            if cands:
                best_cand = cands[0]
                action = await semantic_arbitration_mini(line, best_cand.get("text", ""), best_cand.get("uri", ""))
                if action == "DUPLICATE":
                    logger.info(f"ℹ️ Pominięto duplikat semantyczny dla: {best_cand.get('uri')}")
                    continue
                elif action == "SUPERSEDES":
                    target_uri = best_cand.get("uri")

            line_slug = "_".join(re.sub(r'[^a-z0-9\s]', '', line.lower()).split()[:4])
            if not line_slug:
                line_slug = f"fact_{int(datetime.now().timestamp())}"

            new_uri = f"gce://user/memories/{file_slug}_{line_slug}"

            if action == "SUPERSEDES" and target_uri:
                await asyncio.to_thread(vector_store.delete, target_uri)
                stats["updated"] += 1
                logger.info(f"🔄 Zastąpiono fakt `{target_uri}` nową wersją `{new_uri}`")
            else:
                stats["added"] += 1
                logger.info(f"✨ Zapisano nowy fakt w GCE: `{new_uri}`")

            abstract = f"Memory: {file_slug} {line_slug}"
            metadata = {"source_file": abs_path, "updated_at": datetime.now().isoformat()}

            await asyncio.to_thread(vector_store.add_documents, [{
                "uri": new_uri,
                "text": line,
                "abstract": abstract,
                "vector": vec,
                "metadata": json.dumps(metadata),
                "namespace": "memories"
            }])
        except Exception as e:
            logger.error(f"Błąd przetwarzania nowej linii: {e}")

    # Aktualizacja migawki
    file_snapshot["hash"] = current_hash
    file_snapshot["lines"] = new_lines
    file_snapshot["updated_at"] = datetime.now().isoformat()
    snapshots[abs_path] = file_snapshot
    save_snapshots(snapshots)

    return stats
