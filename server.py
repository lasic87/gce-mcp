import os
import re
import logging
from typing import List, Dict, Optional, Any
from mcp.server.fastmcp import FastMCP
from config import settings
from vector_store import vector_store
from embedding_engine import embedding_engine
from quota_manager import quota_manager
from text_utils import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GCE-MCP")

mcp = FastMCP("GCE-MCP")

# Inicjalizacja splittera zgodnie z ustawieniami
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP
)

async def gce_guardian_diagnostic(error: Exception, tool_name: str, context: str = "") -> str:
    """GCE Guardian: Automatyczna diagnostyka błędów z wykorzystaniem Mining Patterns."""
    logger.error(f"Guardian activated for {tool_name}: {error}")
    
    import traceback
    tb = traceback.format_exc()
    mining_context = f"Błąd w narzędziu: {tool_name}\nBłąd: {str(error)}\nTraceback:\n{tb}\nDodatkowy kontekst: {context}"
    
    try:
        report = await gce_mine_patterns(mining_context)
        
        # Sugestia sesji debugowania
        debug_msg = "\n\n💡 **Sugestia GSD**: Jeśli problem jest złożony, użyj `gce_create_debug_session`, aby śledzić proces naprawy metodą naukową."
        
        return f"🚨 **GCE GUARDIAN DIAGNOSTIC**\n\n{report}{debug_msg}"
    except Exception as e:
        return f"Błąd krytyczny w Guardianie: {e}\nOryginalny błąd: {error}"

@mcp.tool()
async def gce_create_debug_session(project_path: str, symptoms: str) -> str:
    """Tworzy plik .debug.md metodą naukową GSD do śledzenia skomplikowanych błędów."""
    try:
        debug_dir = os.path.join(project_path, ".planning/debug")
        os.makedirs(debug_dir, exist_ok=True)
        
        import time
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"debug_{ts}.md"
        full_path = os.path.join(debug_dir, file_name)
        
        content = f"""# 🔍 Debug Session: {ts}
status: investigating
symptoms: {symptoms}

## 📋 Symptoms
- Expected: 
- Actual: {symptoms}

## 🧪 Hypotheses
1. [Hipoteza 1] - Test: [Jak sprawdzić] - Result: [Oczekiwanie]

## 📑 Evidence
- (Zapisuj tutaj wyniki komend, logi, fragmenty kodu)

## ✅ Resolution
- Root Cause: 
- Fix Applied: 
- Verification: 
"""
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"🛠️ **Debug Session Started**: `{full_path}`\nUżywaj tego pliku jako dziennika, aby nie stracić wątku przy skomplikowanej naprawie."
    except Exception as e:
        return f"Błąd tworzenia sesji debug: {e}"

@mcp.tool()
async def gce_init_spec(project_path: str, description: str) -> str:
    """Generuje ustrukturyzowaną dokumentację projektu (PROJECT, REQUIREMENTS, ROADMAP) w duchu GSD."""
    try:
        os.makedirs(project_path, exist_ok=True)
        
        prompt = f"""
        Jesteś architektem GSD (Get-Shit-Done). Na podstawie opisu użytkownika przygotuj 3 dokumenty w formacie Markdown.
        
        OPIS PROJEKTU:
        {description}
        
        DOKUMENT 1: PROJECT.md (Wizja, cel, stos technologiczny).
        DOKUMENT 2: REQUIREMENTS.md (Lista 'Must-have', 'Nice-to-have' oraz 'Out-of-scope').
        DOKUMENT 3: ROADMAP.md (Podział na 3-5 konkretnych faz implementacji).
        
        Odpowiedz w formacie XML, aby ułatwić mi parsowanie:
        <files>
          <file name="PROJECT.md">treść...</file>
          <file name="REQUIREMENTS.md">treść...</file>
          <file name="ROADMAP.md">treść...</file>
        </files>
        """
        
        response = await quota_manager.generate_content(prompt)
        
        # Proste parsowanie XML (regex)
        import re
        files = re.findall(r'<file name="(.*?)">(.*?)</file>', response, re.DOTALL)
        
        if not files:
            return f"Błąd: Nie udało się wygenerować plików specyfikacji. Odpowiedź modelu:\n{response}"
            
        results = []
        for name, content in files:
            full_path = os.path.join(project_path, name.strip())
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            results.append(full_path)
            
        return f"🚀 **GSD Spec Initialized** w {project_path}:\n" + "\n".join([f"- {r}" for r in results])
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_init_spec", f"Path: {project_path}")

def detect_language(uri: str) -> str:
    """Wykrywa język programowania na podstawie rozszerzenia URI (pliku)."""
    ext = os.path.splitext(uri)[1].lower()
    mapping = {
        ".py": "python",
        ".js": "js",
        ".ts": "ts",
        ".tsx": "ts",
        ".md": "markdown",
        ".sh": "bash"
    }
    return mapping.get(ext, "text")

def extract_relations_simple(content: str, uri: str) -> List[dict]:
    """Szybkie wyszukiwanie importów i zależności dla automatycznego grafu."""
    relations = []
    
    # Python imports
    if uri.endswith(".py"):
        import_matches = re.findall(r'^from\s+([a-zA-Z0-9_\.]+)\s+import|^import\s+([a-zA-Z0-9_\.]+)', content, re.MULTILINE)
        for m in import_matches:
            # Bierzemy pierwszą niepustą grupę
            module = m[0] or m[1]
            if module:
                relations.append({"predicate": "imports", "object_uri": f"python://{module}"})
    
    # JS/TS imports
    elif uri.endswith((".js", ".ts", ".tsx")):
        # Prosty regex dla import/require
        matches = re.findall(r'from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\)', content)
        for m in matches:
            module = m[0] or m[1]
            if module:
                relations.append({"predicate": "depends_on", "object_uri": f"npm://{module}"})
                
    return relations

import hashlib
import json
import asyncio
import time
from pathlib import Path

def get_file_hash(content: str) -> str:
    """Oblicza MD5 dla treści zasobu."""
    return hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()

def load_index_cache() -> dict:
    """Wczytuje cache MD5 z dysku."""
    if os.path.exists(settings.INDEX_CACHE_PATH):
        try:
            with open(settings.INDEX_CACHE_PATH, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_index_cache(cache: dict):
    """Zapisuje cache MD5 na dysk."""
    os.makedirs(os.path.dirname(settings.INDEX_CACHE_PATH), exist_ok=True)
    with open(settings.INDEX_CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2)

def should_ignore(uri: str) -> bool:
    """Sprawdza czy ścieżka powinna być zignorowana."""
    return any(p in uri for p in settings.IGNORE_PATTERNS)

@mcp.tool()
async def gce_index_folder(path: str, extensions: str = ".py,.md,.ts,.tsx,.yaml,.yml") -> str:
    """Bezpiecznie indeksuje cały folder (Smart Indexing z Throttle)."""
    try:
        folder = Path(path)
        if not folder.is_dir():
            return f"Błąd: Ścieżka {path} nie jest katalogiem."
            
        ext_list = extensions.split(",")
        files = [f for f in folder.rglob("*") if f.is_file() and f.suffix in ext_list]
        
        indexed = 0
        skipped = 0
        for f in files:
            res = await gce_add_resource(str(f))
            if "Sukces" in res:
                indexed += 1
                # GCE 2.2 Throttle: Ochrona procesora/routera
                await asyncio.sleep(settings.THROTTLE_DELAY)
            elif "Pominięto" in res:
                skipped += 1
                
        return f"📂 **Index Folder Complete**: `{path}`\nZindeksowano: {indexed}, Pominięto: {skipped}."
    except Exception as e:
        return f"Błąd indeksowania folderu: {e}"

@mcp.tool()
async def gce_add_resource(uri: str, content: str = "", abstract: str = "") -> str:
    """Indeksuje nowy zasób (v2.2: MD5 Smart Cache + Throttle)."""
    try:
        if should_ignore(uri):
            return f"Pominięto: Ścieżka {uri} jest na liście IGNORE."

        # Jeśli content jest pusty, spróbuj odczytać plik z dysku
        if not content:
            if os.path.exists(uri):
                with open(uri, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                return f"Błąd: Nie podano treści i plik nie istnieje."

        # GCE 2.2: MD5 Check (Smart Indexing)
        cache = load_index_cache()
        current_hash = get_file_hash(content)
        if cache.get(uri) == current_hash:
            return f"Pominięto: Zasób {uri} nie zmienił się (identyczny hash)."

        # Jeśli abstract jest pusty, wygeneruj go (L0)
        if not abstract:
            logger.info(f"Generowanie abstraktu (RPD usage) dla {uri}...")
            prompt = f"Wygeneruj ultrazwięzły, techniczny abstrakt (max 150 znaków) dla: {uri}\n\n{content[:2500]}"
            abstract = await quota_manager.generate_content(prompt)
            abstract = abstract.strip().replace("\n", " ")

        lang = detect_language(uri)
        splitter = RecursiveCharacterTextSplitter.from_language(lang, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        chunks = splitter.split_text(content)
        
        metadata = {"relations": extract_relations_simple(content, uri)}
        doc_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_uri = f"{uri}#chunk{i}"
            vector = await embedding_engine.embed_text(f"{abstract}\n\n{chunk}")
            doc_chunks.append({
                "uri": chunk_uri, "text": chunk, "abstract": abstract, 
                "vector": vector, "metadata": json.dumps(metadata)
            })
        
        vector_store.add_documents(doc_chunks)
        
        # Zapis do cache po sukcesie
        cache[uri] = current_hash
        save_index_cache(cache)
        
        return f"Sukces. Zasób {uri} dodany ({len(doc_chunks)} fragmentów, {len(metadata['relations'])} relacji)."
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_add_resource", f"URI: {uri}")

@mcp.tool()
async def gce_add_relation(subject_uri: str, predicate: str, object_uri: str) -> str:
    """Tworzy relację między dwoma zasobami w GCE (np. 'depends_on', 'part_of', 'at_ip')."""
    try:
        import json
        # Aktualizacja metadanych podmiotu
        relation = {"predicate": predicate, "object_uri": object_uri}
        
        # Pobieramy aktualne metadane
        doc = vector_store.get_by_uri(subject_uri)
        if not doc:
            return f"Błąd: Podmiot {subject_uri} nie istnieje w bazie."
            
        current_meta = json.loads(doc.get('metadata', '{}'))
        relations = current_meta.get('relations', [])
        
        # Unikanie duplikatów
        if not any(r['predicate'] == predicate and r['object_uri'] == object_uri for r in relations):
            relations.append(relation)
            current_meta['relations'] = relations
            vector_store.update_metadata(subject_uri, current_meta)
            return f"Sukces: Utworzono relację {subject_uri} --({predicate})--> {object_uri}"
        else:
            return f"Relacja już istnieje."
    except Exception as e:
        return f"Błąd tworzenia relacji: {e}"

@mcp.tool()
async def gce_add_memory(content: str, label: str) -> str:
    """Zapisuje fakt lub preferencję użytkownika bezpośrednio w GCE (v2.0 z autorelami)."""
    try:
        safe_label = re.sub(r'[^a-z0-9]', '_', label.lower())
        uri = f"gce://user/memories/{safe_label}"
        
        try:
            prompt = f"Wygeneruj bardzo krótką, merytoryczną etykietę (max 8 słów) dla faktu:\n{content[:500]}"
            abstract = await quota_manager.generate_content(prompt)
            abstract = abstract.strip().strip('"').replace("\n", " ")
        except:
            abstract = f"Memory: {label}"

        # GCE 2.0: Próba automatycznego wykrycia relacji
        metadata = {"relations": []}
        try:
            # Szybkie wyszukiwanie podobnych faktów, aby zaproponować relację
            query_vector = await embedding_engine.embed_text(content)
            similar = vector_store.hybrid_search(query=content, query_vector=query_vector, limit=2)
            for res in similar:
                if res['uri'] != uri:
                    metadata['relations'].append({"predicate": "related_to", "object_uri": res['uri']})
        except:
            pass

        import json
        vector = await embedding_engine.embed_text(f"{abstract}\n\n{content}")
        
        vector_store.add_documents([{
            "uri": uri,
            "text": content,
            "abstract": abstract,
            "vector": vector,
            "metadata": json.dumps(metadata)
        }])
        
        return f"Zapamiętano: {uri} (Label: {abstract})\nDodano {len(metadata['relations'])} automatycznych relacji."
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_add_memory", f"Label: {label}")

@mcp.tool()
async def gce_analyze_session(context: str) -> str:
    """Analizuje kontekst rozmowy i sugeruje listę atomowych faktów do zapamiętania w GCE."""
    prompt = f"""
    Jesteś analitykiem pamięci GCE. Przeanalizuj poniższy kontekst rozmowy i wyodrębnij fakty o wysokiej wartości:
    - Rozwiązane problemy techniczne (Root Cause + Fix).
    - Nowe preferencje użytkownika (styl kodowania, tech stack).
    - Parametry infrastruktury (IP, porty, ścieżki).
    - Ważne decyzje architektoniczne.

    Dla każdego faktu zaproponuj:
    1. Treść faktu (zwięzła, konkretna).
    2. Sugerowaną etykietę (label).
    3. Krótkie uzasadnienie, dlaczego warto to zapamiętać.
    4. Jeśli fakt sugeruje działanie, dodaj je w formacie:
       <task type="auto"><name>...</name><action>...</action><verify>...</verify></task>

    KONTEKST:
    {context}
    Zwróć odpowiedź w czytelnym formacie listy.
    """
    
    try:
        suggestions = await quota_manager.generate_content(prompt)
        return f"### Sugestie do zapamiętania w GCE:\n\n{suggestions}\n\nCzy chcesz, abym zapisał te fakty w pamięci?"
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_analyze_session")

@mcp.tool()
async def gce_consolidate_memories(content: str, category: str = "general") -> str:
    """Wyodrębnia atomowe fakty z tekstu i zapisuje je seryjnie jako osobne wspomnienia."""
    prompt = f"""
    Wyodrębnij atomowe fakty (preferencje, parametry, rozwiązania) z tekstu. 
    Krótkie, konkretne zdania od '-' bez dodatkowego komentarza.
    Każde zdanie musi być samodzielną informacją.

    TEKST:
    {content}
    """
    
    try:
        response = await quota_manager.generate_content(prompt)
        facts = [line.strip("- ").strip() for line in response.split('\n') if line.strip("- ").strip()]
        
        if not facts:
            return "Brak istotnych faktów do konsolidacji."
            
        doc_chunks = []
        for fact in facts:
            label_words = re.sub(r'[^a-z0-9\s]', '', fact.lower()).split()
            label = "_".join(label_words[:4])
            safe_label = f"{category}_{label}"
            uri = f"gce://user/memories/{safe_label}"
            
            # Generujemy etykietę (abstract) dla każdego faktu (L0)
            try:
                # Szybki prompt dla etykiety
                abstract = f"Fact: {' '.join(label_words[:6])}..."
            except:
                abstract = f"Memory: {label}"

            vector = await embedding_engine.embed_text(f"{abstract}\n\n{fact}")
            
            doc_chunks.append({
                "uri": uri,
                "text": fact,
                "abstract": abstract,
                "vector": vector,
                "metadata": "{}"
            })
            
        if doc_chunks:
            vector_store.add_documents(doc_chunks)
            return f"Sukces: Zapisano {len(doc_chunks)} faktów w kategorii '{category}' (Batch mode)."
        return "Brak danych do zapisu."
    except Exception as e:
        logger.error(f"Consolidation error: {e}")
        return f"Błąd konsolidacji: {e}"

@mcp.tool()
async def gce_mine_patterns(context: str) -> str:
    """Wykrywa powtarzające się wzorce, 'repeat offenders' (błędy) i proponuje stałe zasady/optymalizacje."""
    try:
        # Krok 1: Wyodrębnienie kluczowych pojęć z kontekstu sesji
        extraction_prompt = f"Zidentyfikuj 3-5 kluczowych tematów technicznych (np. nazwa usługi, kod błędu, ścieżka) z tego tekstu: {context[:1000]}"
        topics = await quota_manager.generate_content(extraction_prompt)
        
        # Krok 2: Wyszukiwanie w GCE, czy te tematy już się pojawiały (Hybrid Search)
        query_vector = await embedding_engine.embed_text(topics)
        past_memories = vector_store.hybrid_search(query=topics, query_vector=query_vector, limit=5)
        
        memories_text = "\n".join([f"- {m['uri']}: {m['text']}" for m in past_memories]) if past_memories else "Brak powiązanych wspomnień."

        # Krok 3: Analiza wzorców (Session vs History)
        mining_prompt = f"""
        Jesteś 'GCE Pattern Miner'. Twoim zadaniem jest wykrycie, czy bieżąca sytuacja jest częścią większego wzorca lub powtarzającego się błędu.
        
        BIEŻĄCA SESJA:
        {context}
        
        HISTORIA Z GCE (PODOBNE TEMATY):
        {memories_text}
        
        ZADANIE:
        1. Czy to jest 'Repeat Offender'? (Czy ten problem/zadanie już się pojawiło?)
        2. Czy widać stały wzorzec w preferencjach użytkownika?
        3. Zaproponuj 'Zasadę Systemową' (System Invariant), która zapobiegnie powtórkom lub zautomatyzuje ten proces.
        
        Format odpowiedzi:
        - [Wykryty Wzorzec]: Opis
        - [Status]: (NOWY / POWTARZAJĄCY SIĘ)
        - [Proponowana Zasada]: Konkretna instrukcja do zapisania w GCE Memories.
        """
        
        report = await quota_manager.generate_content(mining_prompt)
        return f"🔍 **GCE PATTERN MINING REPORT**\n\n{report}"
    except Exception as e:
        logger.error(f"Mining error: {e}")
        return f"Błąd mining'u: {e}"

@mcp.tool()
async def gce_cleanup() -> str:
    """Usuwa z bazy zasoby, które nie istnieją już na dysku (Synchronizacja)."""
    try:
        db_stats = vector_store.get_stats()
        # Pobieramy wszystkie unikalne zasoby (base_uris)
        results = vector_store.table.search().to_list()
        all_uris = list(set([res['uri'].split('#')[0] for res in results]))
        
        removed_count = 0
        for uri in all_uris:
            # Sprawdzamy tylko lokalne ścieżki (zaczynające się od /)
            if uri.startswith("/"):
                if not os.path.exists(uri):
                    logger.info(f"Usuwanie nieistniejącego zasobu: {uri}")
                    vector_store.table.delete(f"uri LIKE '{uri}%'")
                    removed_count += 1
                    
        return f"🧹 **GCE Cleanup Complete**\nUsunięto {removed_count} nieaktualnych zasobów z bazy."
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return f"Błąd czyszczenia bazy: {e}"

@mcp.tool()
async def gce_init_project_context(path: str, description: str) -> str:
    """Inicjalizuje ustrukturyzowaną bazę wiedzy .gce (Project Wisdom) w folderze projektu."""
    try:
        ctx_dir = os.path.join(path, settings.PROJECT_CONTEXT_DIR)
        os.makedirs(ctx_dir, exist_ok=True)
        
        # Generowanie PROJECT.md na podstawie opisu
        prompt = f"Stwórz krótki, profesjonalny opis projektu (cel, wizja) dla PROJECT.md na podstawie: {description}"
        project_md = await quota_manager.generate_content(prompt)
        
        files = {
            "PROJECT.md": project_md,
            "DECISIONS.md": "# 🏛 Architectural Decisions Log\n\n*Append decisions here using gce_log_decision.*",
            "KNOWLEDGE.md": "# 🧠 Project Knowledge & Patterns\n\n*General rules, patterns and lessons learned.*",
            "REQUIREMENTS.md": "# 📋 Requirements (Must-have/Nice-to-have)"
        }
        
        results = []
        for name, content in files.items():
            full_path = os.path.join(ctx_dir, name)
            if not os.path.exists(full_path):
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content.strip())
                # Automatyczne indeksowanie nowych plików w GCE
                await gce_add_resource(full_path)
                results.append(name)
        
        return f"🌟 **Project Wisdom Initialized** in {ctx_dir}:\n- Utworzono i zindeksowano: {', '.join(results)}"
    except Exception as e:
        return f"Błąd inicjalizacji projektu: {e}"

@mcp.tool()
async def gce_log_decision(project_path: str, decision: str, context: str = "") -> str:
    """Zapisuje decyzję architektoniczną do DECISIONS.md i wektoryzuje ją jako fakt (Immutable Fact)."""
    try:
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ctx_dir = os.path.join(project_path, settings.PROJECT_CONTEXT_DIR)
        dec_file = os.path.join(ctx_dir, "DECISIONS.md")
        
        entry = f"\n\n### [{ts}] {decision}\n**Context:** {context}\n"
        
        # Append to file
        os.makedirs(ctx_dir, exist_ok=True)
        with open(dec_file, 'a', encoding='utf-8') as f:
            f.write(entry)
            
        # Zapisz jako Memory (Immutable Fact) w GCE
        project_name = os.path.basename(project_path)
        await gce_add_memory(
            content=f"PROJECT: {project_name}\nDECISION: {decision}\nCONTEXT: {context}\nTIMESTAMP: {ts}",
            label=f"decision_{project_name}_{int(time.time())}"
        )
        
        return f"🏛 **Decision Logged**: Zapisano w {dec_file} i wektoryzowano jako fakt."
    except Exception as e:
        return f"Błąd zapisu decyzji: {e}"

@mcp.tool()
async def gce_query_project_health(path: str) -> str:
    """Analizuje spójność bazy wiedzy (Grafu) dla projektu (GSD-2 pattern)."""
    try:
        # Pobieramy wszystkie zasoby projektu
        results = vector_store.table.search().where(f"uri LIKE '{path}%'").to_list()
        if not results:
            return f"Baza nie zawiera zasobów dla ścieżki: {path}"
            
        uris = {res['uri'].split('#')[0] for res in results}
        all_relations = []
        for res in results:
            try:
                meta = json.loads(res.get('metadata', '{}'))
                all_relations.extend(meta.get('relations', []))
            except: pass
            
        # Sprawdzanie brakujących ogniw (tylko lokalne zależności)
        missing_uris = []
        for rel in all_relations:
            obj_uri = rel['object_uri']
            if obj_uri.startswith("/") and obj_uri not in uris:
                missing_uris.append(obj_uri)
        
        report = f"📋 **GCE Project Health: {os.path.basename(path)}**\n"
        report += f"- Indexed Resources: {len(uris)}\n"
        report += f"- Total Relations: {len(all_relations)}\n"
        
        if missing_uris:
            report += f"- ⚠️ Missing Links in Knowledge Graph: {len(set(missing_uris))}\n"
            for m in list(set(missing_uris))[:5]:
                report += f"  - `{m}`\n"
        else:
            report += "- ✅ Knowledge Graph is consistent.\n"
            
        return report
    except Exception as e:
        return f"Błąd analizy zdrowia: {e}"

@mcp.tool()
async def gce_doctor(fix: bool = False) -> str:
    """Diagnozuje stan zdrowia GCE (Ollama, DB, Cache) i opcjonalnie naprawia błędy."""
    report = "🩺 **GCE DOCTOR REPORT**\n\n"
    issues = []
    
    # 1. Test Ollama (Embedding Engine)
    try:
        test_vector = await embedding_engine.embed_text("health check")
        if len(test_vector) == 768:
            report += "✅ Ollama: Active (iGPU nomic-embed-text)\n"
        else:
            issues.append("Ollama returned invalid vector size.")
    except Exception as e:
        issues.append(f"Ollama connection failed: {e}")
        
    # 2. Test LanceDB & FTS
    try:
        db_stats = vector_store.get_stats()
        report += f"✅ LanceDB: {db_stats['total_chunks']} chunks in {db_stats['db_size']}\n"
        # Test wyszukiwania FTS
        vector_store.table.search("test", query_type="fts").limit(1).to_list()
        report += "✅ FTS Index: Functional\n"
    except Exception as e:
        issues.append(f"LanceDB/FTS error: {e}")
        
    # 3. Test Cache
    if os.path.exists(settings.INDEX_CACHE_PATH):
        try:
            cache = load_index_cache()
            report += f"✅ Index Cache: {len(cache)} entries\n"
        except:
            issues.append("Index Cache is corrupted.")
    else:
        report += "⚠️ Index Cache: Missing (will be created on first index)\n"
        
    if not issues:
        return report + "\n✨ **All systems nominal.**"
    
    report += "\n❌ **Found Issues:**\n" + "\n".join([f"- {i}" for i in issues])
    
    if fix:
        report += "\n\n🛠️ **Attempting Auto-fix...**\n"
        fixed = []
        for issue in issues:
            if "FTS" in issue:
                vector_store.table.create_fts_index("text", replace=True)
                vector_store.table.create_fts_index("abstract", replace=True)
                fixed.append("Rebuilt FTS indexes.")
            if "Cache" in issue:
                if os.path.exists(settings.INDEX_CACHE_PATH):
                    os.remove(settings.INDEX_CACHE_PATH)
                fixed.append("Reset corrupted cache.")
        
        report += "\n".join([f"✅ Fixed: {f}" for f in fixed]) if fixed else "⚠️ Could not auto-fix some issues."
        
    return report

@mcp.tool()
async def gce_add_rule(scope: str, rule: str, project_path: Optional[str] = None) -> str:
    """Dodaje trwałą zasadę (Persistent Rule) do projektu lub pamięci globalnej (GSD-2 pattern)."""
    try:
        if scope == "project":
            if not project_path:
                return "Błąd: Brak ścieżki projektu dla zasady typu 'project'."
            
            ctx_dir = os.path.join(project_path, settings.PROJECT_CONTEXT_DIR)
            know_file = os.path.join(ctx_dir, "KNOWLEDGE.md")
            os.makedirs(ctx_dir, exist_ok=True)
            
            with open(know_file, 'a', encoding='utf-8') as f:
                f.write(f"\n- **RULE:** {rule}")
            
            # Re-index KNOWLEDGE.md
            await gce_add_resource(know_file)
            return f"🧠 **Project Rule Added** to {know_file} and indexed."
            
        elif scope == "global":
            await gce_add_memory(content=f"GLOBAL RULE: {rule}", label=f"global_rule_{int(time.time())}")
            return "🌍 **Global Rule Added** to GCE Memories."
            
        return "Błąd: Nieprawidłowy zakres (scope). Użyj 'project' lub 'global'."
    except Exception as e:
        return f"Błąd dodawania zasady: {e}"

@mcp.tool()
async def gce_verify_requirement(project_path: str, req_id: str, status: str, evidence: str = "") -> str:
    """Aktualizuje status wymagania w REQUIREMENTS.md i dołącza dowód (Evidence)."""
    try:
        ctx_dir = os.path.join(project_path, settings.PROJECT_CONTEXT_DIR)
        req_file = os.path.join(ctx_dir, "REQUIREMENTS.md")
        
        if not os.path.exists(req_file):
            return f"Błąd: Nie znaleziono REQUIREMENTS.md w {ctx_dir}."
            
        with open(req_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated = False
        new_lines = []
        
        for line in lines:
            if req_id in line:
                new_lines.append(f"- [ {status} ] {req_id} (Updated: {ts})\n")
                if evidence:
                    new_lines.append(f"  - **Evidence:** {evidence}\n")
                updated = True
            else:
                new_lines.append(line)
                
        if not updated:
            # Jeśli nie znaleziono, dodaj na końcu
            new_lines.append(f"\n- [ {status} ] {req_id} (Added: {ts})\n")
            if evidence:
                new_lines.append(f"  - **Evidence:** {evidence}\n")
        
        with open(req_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        # Re-index
        await gce_add_resource(req_file)
        return f"✅ **Requirement Verified**: {req_id} status set to {status}."
    except Exception as e:
        return f"Błąd weryfikacji wymagania: {e}"

@mcp.tool()
async def gce_get_stats() -> str:
    """Zwraca statystyki bazy danych GCE oraz stan limitów modeli AI."""
    try:
        db_stats = vector_store.get_stats()
        model_stats = quota_manager.get_stats()
        
        report = "📊 **GCE SYSTEM STATS**\n\n"
        report += f"**Database (LanceDB):**\n"
        report += f"- Total Chunks: {db_stats['total_chunks']}\n"
        report += f"- Unique Resources: {db_stats['unique_resources']}\n"
        report += f"- Memories: {db_stats['memories_count']}\n"
        report += f"- DB Size: `{db_stats['db_size']}`\n"
        report += f"- DB Path: `{db_stats['db_path']}`\n\n"
        
        if db_stats.get('top_resources'):
            report += "**Top 5 Resources (by chunk count):**\n"
            for r in db_stats['top_resources']:
                report += f"- `{r['uri']}` ({r['chunks']} chunks)\n"
            report += "\n"
        
        report += "**AI Models Quota (Model Juggler):**\n"
        for m in model_stats:
            # Tworzymy prosty pasek postępu (10 segmentów)
            if m['rpd_limit'] > 0:
                usage_pct = int((m['rpd'] / m['rpd_limit']) * 100)
                filled = min(10, int(usage_pct / 10))
                bar = "█" * filled + "░" * (10 - filled)
                color_indicator = "🟢" if usage_pct < 70 else ("🟡" if usage_pct < 90 else "🔴")
            else:
                bar = "░" * 10
                usage_pct = 0
                color_indicator = "⚪"

            status = "🔴 BLOCKED" if m['is_blocked'] else "🟢 ACTIVE"
            report += f"- **{m['name']}** [{status}]\n"
            report += f"  RPD: [{bar}] {usage_pct}% ({m['rpd']}/{m['rpd_limit']}) {color_indicator}\n"
            report += f"  RPM: {m['rpm']}/{m['rpm_limit']}\n"
            
        return report
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return f"Błąd pobierania statystyk: {e}"

@mcp.tool()
async def gce_search_context(query: str, limit: int = 5, where: Optional[str] = None) -> str:
    """Wyszukiwanie hybrydowe w bazie GCE (Semantyka + Słowa kluczowe)."""
    try:
        query_vector = await embedding_engine.embed_text(query)
        results = vector_store.hybrid_search(query=query, query_vector=query_vector, limit=limit, where=where)
        
        if not results:
            return "Brak wyników."

        response = "Wyniki z GCE:\n\n"
        for i, res in enumerate(results, 1):
            response += f"{i}. SOURCE: {res['uri']}\n"
            if res.get('abstract'):
                response += f"   LABEL: {res['abstract']}\n"
            response += f"   CONTENT: {res['text']}\n"
            response += "-" * 30 + "\n"
            
        return response
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_search_context", f"Query: {query}")

if __name__ == "__main__":
    mcp.run()
