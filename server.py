import os
import re
import logging
import hashlib
import json
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from mcp.server.fastmcp import FastMCP
from config import settings
from vector_store import vector_store
from embedding_engine import embedding_engine
from quota_manager import quota_manager
from text_utils import RecursiveCharacterTextSplitter
from knowledge_graph import knowledge_graph

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
        debug_msg = "\n\n💡 **Sugestia GSD**: Jeśli problem jest złożony, użyj `gce_create_debug_session`."
        return f"🚨 **GCE GUARDIAN DIAGNOSTIC**\n\n{report}{debug_msg}"
    except Exception as e:
        return f"Błąd krytyczny w Guardianie: {e}\nOryginalny błąd: {error}"

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
    if uri.endswith(".py"):
        import_matches = re.findall(r'^from\s+([a-zA-Z0-9_\.]+)\s+import|^import\s+([a-zA-Z0-9_\.]+)', content, re.MULTILINE)
        for m in import_matches:
            module = m[0] or m[1]
            if module:
                relations.append({"predicate": "imports", "object_uri": f"python://{module}"})
    elif uri.endswith((".js", ".ts", ".tsx")):
        matches = re.findall(r'from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\)', content)
        for m in matches:
            module = m[0] or m[1]
            if module:
                relations.append({"predicate": "depends_on", "object_uri": f"npm://{module}"})
    return relations

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
async def gce_list_namespaces() -> str:
    """Listuje wszystkie dostępne przestrzenie nazw (Namespaces) w bazie GCE."""
    try:
        stats = vector_store.get_stats()
        ns_list = stats.get('namespaces', ['default'])
        return "📂 **GCE Namespaces:**\n" + "\n".join([f"- {ns}" for ns in ns_list])
    except Exception as e:
        return f"Błąd listowania namespace: {e}"

@mcp.tool()
async def gce_index_folder(path: str, extensions: str = ".py,.md,.ts,.tsx,.yaml,.yml", namespace: str = "default") -> str:
    """Bezpiecznie indeksuje cały folder do konkretnego namespace."""
    try:
        folder = Path(path)
        if not folder.is_dir():
            return f"Błąd: Ścieżka {path} nie jest katalogiem."
        ext_list = extensions.split(",")
        files = [f for f in folder.rglob("*") if f.is_file() and f.suffix in ext_list]
        indexed = 0
        skipped = 0
        for f in files:
            res = await gce_add_resource(str(f), namespace=namespace)
            if "Sukces" in res:
                indexed += 1
                await asyncio.sleep(settings.THROTTLE_DELAY)
            elif "Pominięto" in res:
                skipped += 1
        return f"📂 **Index Folder Complete**: `{path}` (Namespace: {namespace})\nZindeksowano: {indexed}, Pominięto: {skipped}."
    except Exception as e:
        return f"Błąd indeksowania folderu: {e}"

@mcp.tool()
async def gce_add_resource(uri: str, content: str = "", abstract: str = "", namespace: str = "default") -> str:
    """Indeksuje nowy zasób w konkretnym namespace."""
    try:
        if should_ignore(uri):
            return f"Pominięto: Ścieżka {uri} jest na liście IGNORE."
        if not content:
            if os.path.exists(uri):
                with open(uri, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                return f"Błąd: Nie podano treści i plik nie istnieje."
        cache = load_index_cache()
        cache_key = f"{namespace}:{uri}"
        current_hash = get_file_hash(content)
        if cache.get(cache_key) == current_hash:
            return f"Pominięto: Zasób {uri} w namespace {namespace} nie zmienił się."
        if not abstract:
            logger.info(f"Generowanie abstraktu dla {uri}...")
            prompt = f"Wygeneruj ultrazwięzły, techniczny abstrakt (max 150 znaków) dla: {uri}\n\n{content[:2500]}"
            abstract = await quota_manager.generate_content(prompt)
            abstract = abstract.strip().replace("\n", " ")
        lang = detect_language(uri)
        splitter = RecursiveCharacterTextSplitter.from_language(lang, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        chunks = splitter.split_text(content, language=lang)
        metadata = {"relations": extract_relations_simple(content, uri)}
        doc_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_uri = f"{uri}#chunk{i}"
            vector = await embedding_engine.embed_text(f"{abstract}\n\n{chunk}")
            doc_chunks.append({
                "uri": chunk_uri, "text": chunk, "abstract": abstract, 
                "vector": vector, "metadata": json.dumps(metadata),
                "namespace": namespace
            })
        vector_store.add_documents(doc_chunks)
        cache[cache_key] = current_hash
        save_index_cache(cache)
        return f"Sukces. Zasób {uri} dodany do namespace '{namespace}'."
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_add_resource", f"URI: {uri}")

@mcp.tool()
async def gce_add_memory(content: str, label: str, namespace: str = "memories") -> str:
    """Zapisuje fakt bezpośrednio do konkretnego namespace (domyślnie: memories)."""
    try:
        safe_label = re.sub(r'[^a-z0-9]', '_', label.lower())
        uri = f"gce://user/memories/{safe_label}"
        try:
            prompt = f"Wygeneruj bardzo krótką, merytoryczną etykietę dla faktu:\n{content[:500]}"
            abstract = await quota_manager.generate_content(prompt)
            abstract = abstract.strip().strip('"').replace("\n", " ")
        except:
            abstract = f"Memory: {label}"
        metadata = {"relations": []}
        vector = await embedding_engine.embed_text(f"{abstract}\n\n{content}")
        vector_store.add_documents([{
            "uri": uri, "text": content, "abstract": abstract, 
            "vector": vector, "metadata": json.dumps(metadata),
            "namespace": namespace
        }])
        return f"Zapamiętano: {uri} w namespace '{namespace}' (Label: {abstract})"
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_add_memory", f"Label: {label}")

@mcp.tool()
async def gce_distill_patterns(context: str, project_name: str = "general") -> str:
    """Analizuje kontekst sesji i destyluje z niego 'Złote Wzorce' (sukcesy) oraz 'Wzorce Negatywne' (błędy)."""
    prompt = f"""
    Jesteś 'GCE Neural Distiller'. Przeanalizuj poniższy kontekst techniczny i wydestyluj z niego mądrość operacyjną.
    
    KONTEKST (Sesja/Projekt):
    {context}
    
    ZADANIE:
    1. Zidentyfikuj 'Złote Wzorce' (Golden Patterns): Konkretne rozwiązania, konfiguracje lub podejścia, które zadziałały i powinny być powtarzane.
    2. Zidentyfikuj 'Wzorce Negatywne' (Negative Patterns): Błędy, ślepe uliczki lub nieefektywne metody, których należy unikać.
    3. Dla każdego wzorca stwórz krótki, techniczny opis (max 2 zdania).
    
    FORMAT ZWROTNY (XML):
    <patterns>
      <pattern type="golden" label="nazwa_wzorca">opis...</pattern>
      <pattern type="negative" label="nazwa_bledu">opis...</pattern>
    </patterns>
    """
    
    try:
        response = await quota_manager.generate_content(prompt)
        patterns = re.findall(r'<pattern type="(.*?)" label="(.*?)">(.*?)</pattern>', response, re.DOTALL)
        
        if not patterns:
            return "Nie znaleziono wyraźnych wzorców do wydestylowania."
            
        count = 0
        for p_type, label, desc in patterns:
            full_content = f"TYPE: {p_type.upper()} PATTERN\nPROJECT: {project_name}\nDESCRIPTION: {desc.strip()}"
            safe_label = f"pattern_{p_type}_{re.sub(r'[^a-z0-9]', '_', label.lower())}"
            
            # Zapisujemy do specjalnego namespace 'patterns'
            await gce_add_memory(content=full_content, label=safe_label, namespace="patterns")
            count += 1
            
        return f"🧠 **Neural Distillation Complete**: Wydestylowano i zapamiętano {count} wzorców w namespace 'patterns'."
    except Exception as e:
        return f"Błąd destylacji wzorców: {e}"

@mcp.tool()
async def gce_search_context(query: str, limit: int = 5, where: Optional[str] = None, namespace: Optional[str] = None) -> str:
    """Wyszukiwanie hybrydowe (v2.5: Automatycznie dołącza istotne wzorce z 'patterns')."""
    try:
        query_vector = await embedding_engine.embed_text(query)
        
        # 1. Główne wyszukiwanie w wybranym namespace
        results = vector_store.hybrid_search(query=query, query_vector=query_vector, limit=limit, where=where, namespace=namespace)
        
        # 2. Inteligentne dołączanie wzorców (jeśli nie szukamy już w patterns)
        pattern_results = []
        if namespace != "patterns":
            pattern_results = vector_store.hybrid_search(query=query, query_vector=query_vector, limit=2, namespace="patterns")
        
        if not results and not pattern_results:
            return "Brak wyników."

        response = "Wyniki z GCE:\n\n"
        
        # Najpierw dołączamy wzorce jako 'Lekcje z przeszłości' (jeśli istnieją)
        if pattern_results:
            response += "💡 **POWIĄZANE WZORCE (Lekcje z przeszłości):**\n"
            for res in pattern_results:
                response += f"   - [{res['uri']}] {res['text']}\n"
            response += "\n" + "="*30 + "\n\n"

        for i, res in enumerate(results, 1):
            response += f"{i}. SOURCE: {res['uri']} [{res.get('namespace', 'default')}]\n"
            if res.get('abstract'):
                response += f"   LABEL: {res['abstract']}\n"
            response += f"   CONTENT: {res['text']}\n"
            response += "-" * 30 + "\n"
            
        return response
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_search_context", f"Query: {query}")

@mcp.tool()
async def gce_get_stats() -> str:
    """Zwraca rozszerzone statystyki bazy danych GCE per namespace."""
    try:
        db_stats = vector_store.get_stats()
        model_stats = quota_manager.get_stats()
        report = "📊 **GCE SYSTEM STATS**\n\n"
        report += f"**Database (LanceDB):**\n"
        report += f"- Total Chunks: {db_stats['total_chunks']}\n"
        report += f"- Unique Resources: {db_stats['unique_resources']}\n"
        report += f"- Namespaces: {', '.join(db_stats['namespaces'])}\n"
        report += f"- DB Size: `{db_stats['db_size']}`\n"
        report += f"- DB Path: `{db_stats['db_path']}`\n\n"
        if db_stats.get('top_resources'):
            report += "**Top 5 Resources (by chunk count):**\n"
            for r in db_stats['top_resources']:
                report += f"- `{r['uri']}` ({r['chunks']} chunks)\n"
            report += "\n"
        report += "**AI Models Quota (Model Juggler):**\n"
        for m in model_stats:
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
async def gce_create_debug_session(project_path: str, symptoms: str) -> str:
    """Tworzy plik .debug.md metodą naukową GSD do śledzenia skomplikowanych błędów."""
    try:
        debug_dir = os.path.join(project_path, ".planning/debug")
        os.makedirs(debug_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        file_name = f"debug_{ts}.md"
        full_path = os.path.join(debug_dir, file_name)
        content = f"# 🔍 Debug Session: {ts}\nstatus: investigating\nsymptoms: {symptoms}\n\n## 📋 Symptoms\n- Expected: \n- Actual: {symptoms}\n\n## 🧪 Hypotheses\n1. [Hipoteza 1] - Test: [Jak sprawdzić] - Result: [Oczekiwanie]\n\n## ✅ Resolution\n- Root Cause: \n- Fix Applied: \n- Verification: \n"
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"🛠️ **Debug Session Started**: `{full_path}`"
    except Exception as e:
        return f"Błąd tworzenia sesji debug: {e}"

@mcp.tool()
async def gce_init_spec(project_path: str, description: str) -> str:
    """Generuje ustrukturyzowaną dokumentację projektu (PROJECT, REQUIREMENTS, ROADMAP)."""
    try:
        os.makedirs(project_path, exist_ok=True)
        prompt = f"Jesteś architektem GSD. Przygotuj 3 dokumenty (PROJECT.md, REQUIREMENTS.md, ROADMAP.md) w formacie XML <files><file name='...'>...</file></files> dla: {description}"
        response = await quota_manager.generate_content(prompt, thinking=True)
        files = re.findall(r'<file name="(.*?)">(.*?)</file>', response, re.DOTALL)
        if not files: return f"Błąd generowania specyfikacji."
        results = []
        for name, content in files:
            full_path = os.path.join(project_path, name.strip())
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            results.append(full_path)
        return f"🚀 **GSD Spec Initialized** w {project_path}:\n" + "\n".join([f"- {r}" for r in results])
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_init_spec", f"Path: {project_path}")

@mcp.tool()
async def gce_add_relation(subject_uri: str, predicate: str, object_uri: str) -> str:
    """Tworzy relację między dwoma zasobami w GCE."""
    try:
        doc = vector_store.get_by_uri(subject_uri)
        if not doc: return f"Błąd: Podmiot {subject_uri} nie istnieje."
        current_meta = json.loads(doc.get('metadata', '{}'))
        relations = current_meta.get('relations', [])
        if not any(r['predicate'] == predicate and r['object_uri'] == object_uri for r in relations):
            relations.append({"predicate": predicate, "object_uri": object_uri})
            current_meta['relations'] = relations
            vector_store.update_metadata(subject_uri, current_meta)
            return f"Sukces: Utworzono relację {subject_uri} --({predicate})--> {object_uri}"
        return f"Relacja już istnieje."
    except Exception as e:
        return f"Błąd tworzenia relacji: {e}"

@mcp.tool()
async def gce_analyze_session(context: str) -> str:
    """Analizuje kontekst rozmowy i sugeruje listę atomowych faktów do zapamiętania."""
    prompt = f"Jesteś analitykiem pamięci GCE. Wyodrębnij fakty z kontekstu: {context}"
    try:
        suggestions = await quota_manager.generate_content(prompt)
        return f"### Sugestie do zapamiętania w GCE:\n\n{suggestions}"
    except Exception as e:
        return await gce_guardian_diagnostic(e, "gce_analyze_session")

@mcp.tool()
async def gce_consolidate_memories(content: str, category: str = "general") -> str:
    """Wyodrębnia atomowe fakty i zapisuje je seryjnie."""
    prompt = f"Wyodrębnij atomowe fakty z tekstu: {content}"
    try:
        response = await quota_manager.generate_content(prompt)
        facts = [line.strip("- ").strip() for line in response.split('\n') if line.strip("- ").strip()]
        if not facts: return "Brak faktów."
        doc_chunks = []
        for fact in facts:
            label = "_".join(re.sub(r'[^a-z0-9\s]', '', fact.lower()).split()[:4])
            uri = f"gce://user/memories/{category}_{label}"
            vector = await embedding_engine.embed_text(f"Memory: {label}\n\n{fact}")
            doc_chunks.append({"uri": uri, "text": fact, "abstract": f"Memory: {label}", "vector": vector, "metadata": "{}", "namespace": "memories"})
        vector_store.add_documents(doc_chunks)
        return f"Sukces: Zapisano {len(doc_chunks)} faktów w kategorii '{category}'."
    except Exception as e:
        return f"Błąd konsolidacji: {e}"

@mcp.tool()
async def gce_mine_patterns(context: str) -> str:
    """Wykrywa powtarzające się wzorce i proponuje zasady."""
    try:
        extraction_prompt = f"Zidentyfikuj kluczowe tematy: {context[:1000]}"
        topics = await quota_manager.generate_content(extraction_prompt)
        query_vector = await embedding_engine.embed_text(topics)
        past_memories = vector_store.hybrid_search(query=topics, query_vector=query_vector, limit=5)
        memories_text = "\n".join([f"- {m['uri']}: {m['text']}" for m in past_memories])
        mining_prompt = f"Jesteś GCE Pattern Miner. Analizuj: {context}\nHistoria: {memories_text}"
        report = await quota_manager.generate_content(mining_prompt)
        return f"🔍 **GCE PATTERN MINING REPORT**\n\n{report}"
    except Exception as e:
        return f"Błąd mining'u: {e}"

@mcp.tool()
async def gce_cleanup() -> str:
    """Usuwa nieistniejące zasoby z bazy."""
    try:
        results = vector_store.table.search().to_list()
        all_uris = list(set([res['uri'].split('#')[0] for res in results]))
        removed_count = 0
        for uri in all_uris:
            if uri.startswith("/") and not os.path.exists(uri):
                vector_store.table.delete(f"uri LIKE '{uri}%'")
                removed_count += 1
        return f"🧹 **GCE Cleanup Complete**: Usunięto {removed_count} zasobów."
    except Exception as e:
        return f"Błąd czyszczenia: {e}"

@mcp.tool()
async def gce_init_project_context(path: str, description: str) -> str:
    """Inicjalizuje ustrukturyzowaną bazę wiedzy .gce."""
    try:
        ctx_dir = os.path.join(path, settings.PROJECT_CONTEXT_DIR)
        os.makedirs(ctx_dir, exist_ok=True)
        prompt = f"Opis projektu PROJECT.md dla: {description}"
        project_md = await quota_manager.generate_content(prompt)
        files = {"PROJECT.md": project_md, "DECISIONS.md": "# Decyzje", "KNOWLEDGE.md": "# Wiedza", "REQUIREMENTS.md": "# Wymagania"}
        results = []
        for name, content in files.items():
            full_path = os.path.join(ctx_dir, name)
            if not os.path.exists(full_path):
                with open(full_path, 'w', encoding='utf-8') as f: f.write(content.strip())
                await gce_add_resource(full_path, namespace="project_context")
                results.append(name)
        return f"🌟 **Project Wisdom Initialized**: {', '.join(results)}"
    except Exception as e:
        return f"Błąd inicjalizacji: {e}"

@mcp.tool()
async def gce_log_decision(project_path: str, decision: str, context: str = "") -> str:
    """Zapisuje decyzję architektoniczną."""
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        ctx_dir = os.path.join(project_path, settings.PROJECT_CONTEXT_DIR)
        dec_file = os.path.join(ctx_dir, "DECISIONS.md")
        entry = f"\n\n### [{ts}] {decision}\n**Context:** {context}\n"
        os.makedirs(ctx_dir, exist_ok=True)
        with open(dec_file, 'a', encoding='utf-8') as f: f.write(entry)
        await gce_add_memory(content=f"DECISION: {decision}\nCONTEXT: {context}", label=f"dec_{int(time.time())}", namespace="decisions")
        return f"🏛 **Decision Logged**"
    except Exception as e:
        return f"Błąd zapisu: {e}"

@mcp.tool()
async def gce_query_project_health(path: str) -> str:
    """Analizuje spójność bazy wiedzy."""
    try:
        results = vector_store.table.search().where(f"uri LIKE '{path}%'").to_list()
        if not results: return f"Brak zasobów."
        uris = {res['uri'].split('#')[0] for res in results}
        report = f"📋 **GCE Project Health**: Indexed {len(uris)} resources."
        return report
    except Exception as e:
        return f"Błąd zdrowia: {e}"

@mcp.tool()
async def gce_doctor(fix: bool = False) -> str:
    """Diagnozuje stan zdrowia GCE oraz wykonuje analizę regresji (Forensics v2.0)."""
    report = "🩺 **GCE DOCTOR REPORT v2.0 (Regression Forensics)**\n\n"
    
    # 1. Sprawdzenie infrastruktury (Vital Signs)
    vitals = []
    try:
        await embedding_engine.embed_text("check")
        vitals.append("✅ Ollama iGPU (Vulkan) OK")
    except Exception as e: vitals.append(f"❌ Ollama ERROR: {e}")
    
    try:
        stats = vector_store.get_stats()
        vitals.append(f"✅ LanceDB OK ({stats['total_chunks']} chunks)")
    except Exception as e: vitals.append(f"❌ Database ERROR: {e}")
    
    report += "### 🩺 Vital Signs\n" + "\n".join(vitals) + "\n\n"

    # 2. Skanowanie logów (System Logs)
    log_files = ["/root/logs/error.log", "/root/gce-mcp/debug_server.log"]
    recent_errors = []
    for log in log_files:
        if os.path.exists(log):
            with open(log, "r") as f:
                lines = f.readlines()[-20:]
                errors = [l for l in lines if "ERROR" in l or "Exception" in l or "Traceback" in l]
                if errors:
                    recent_errors.append(f"📄 {log}:\n" + "".join(errors))
    
    # 3. Pobieranie kontekstu zmian (Recent Decisions/Patterns)
    try:
        query_vector = await embedding_engine.embed_text("recent changes architecture patterns")
        recent_changes = vector_store.hybrid_search(query="recent changes", query_vector=query_vector, limit=5, namespace="patterns")
        changes_text = "\n".join([f"- {c['uri']}: {c['text']}" for c in recent_changes])
    except:
        changes_text = "Brak dostępnych wzorców w pamięci."

    # 4. Analiza Regresji (Thinking Analysis)
    analysis_prompt = f"""
    Jesteś 'GCE Forensic Doctor'. Przeanalizuj stan zdrowia systemu.
    
    BŁĘDY W LOGACH:
    {recent_errors if recent_errors else 'Brak wykrytych błędów.'}
    
    OSTATNIE ZMIANY ARCHITEKTONICZNE (GCE Memories):
    {changes_text}
    
    ZADANIE:
    1. Oceń ryzyko regresji (High/Medium/Low).
    2. Czy błędy w logach mogą wynikać z ostatnich zmian?
    3. Co należy sprawdzić lub naprawić?
    """
    
    try:
        diagnosis = await quota_manager.generate_content(analysis_prompt, thinking=True)
        report += f"### 🧠 AI Forensics (Thinking Mode)\n{diagnosis}\n"
    except Exception as e:
        report += f"⚠️ Błąd analizy forensics: {e}\n"

    # 5. Self-Healing (jeśli fix=True)
    if fix:
        report += "\n### 🛠️ Self-Healing Mode\n"
        if os.path.exists(settings.INDEX_CACHE_PATH):
            os.remove(settings.INDEX_CACHE_PATH)
            report += "- ✅ MD5 Index Cache wyczyszczony (wymusi re-indeksowanie przy zmianach).\n"
        report += "- ✅ System Doctor sugeruje restart sesji CLI po wprowadzeniu poprawek.\n"

    return report

@mcp.tool()
async def gce_add_rule(scope: str, rule: str, project_path: Optional[str] = None) -> str:
    """Dodaje trwałą zasadę."""
    try:
        if scope == "project" and project_path:
            ctx_dir = os.path.join(project_path, settings.PROJECT_CONTEXT_DIR)
            know_file = os.path.join(ctx_dir, "KNOWLEDGE.md")
            with open(know_file, 'a', encoding='utf-8') as f: f.write(f"\n- **RULE:** {rule}")
            await gce_add_resource(know_file, namespace="rules")
            return f"🧠 Rule added to project."
        elif scope == "global":
            await gce_add_memory(content=f"GLOBAL RULE: {rule}", label=f"rule_{int(time.time())}", namespace="global_rules")
            return "🌍 Global rule added."
        return "Błąd parametrów."
    except Exception as e: return f"Błąd: {e}"

@mcp.tool()
async def gce_verify_requirement(project_path: str, req_id: str, status: str, evidence: str = "") -> str:
    """Aktualizuje status wymagania."""
    try:
        ctx_dir = os.path.join(project_path, settings.PROJECT_CONTEXT_DIR)
        req_file = os.path.join(ctx_dir, "REQUIREMENTS.md")
        with open(req_file, 'a', encoding='utf-8') as f: f.write(f"\n- [ {status} ] {req_id}: {evidence}")
        await gce_add_resource(req_file, namespace="requirements")
        return f"✅ Verified: {req_id}"
    except Exception as e: return f"Błąd: {e}"

# ==================== Dziennik Sesji (Session Diary) ====================

@mcp.tool()
async def gce_diary_write(agent_name: str, entry: str, topic: str = "general") -> str:
    """Zapisuje wpis w dzienniku sesyjnym w LanceDB."""
    try:
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        safe_name = re.sub(r'[^a-z0-9]', '_', agent_name.lower())
        uri = f"gce://agent/diaries/{safe_name}/{int(time.time())}"
        
        abstract = f"Diary Entry ({agent_name}) - Topic: {topic}"
        diary_content = f"Session Log - {agent_name} - {topic}\nDate: {timestamp}\n\n{entry}"
        
        metadata = {
            "agent_name": agent_name,
            "topic": topic,
            "timestamp": timestamp
        }
        
        vector = await embedding_engine.embed_text(diary_content)
        vector_store.add_documents([{
            "uri": uri, "text": diary_content, "abstract": abstract,
            "vector": vector, "metadata": json.dumps(metadata),
            "namespace": "diaries"
        }])
        return f"📖 Zapisano w dzienniku sesyjnym dla {agent_name} (URI: {uri})"
    except Exception as e:
        return f"Błąd zapisu w dzienniku: {e}"

@mcp.tool()
async def gce_diary_read(agent_name: str, limit: int = 5) -> str:
    """Odczytuje najnowsze wpisy z dziennika sesyjnego."""
    try:
        safe_name = re.sub(r'[^a-z0-9]', '_', agent_name.lower())
        
        # LanceDB pozwala na wyszukiwanie przez SQL, pobieramy wpisy z namespace="diaries"
        results = vector_store.table.search().where(
            f"namespace = 'diaries' AND uri LIKE 'gce://agent/diaries/{safe_name}/%'"
        ).to_list()
        
        if not results:
            return f"Brak wpisów w dzienniku sesyjnym dla '{agent_name}'."
            
        # Sortowanie po URI alfabetycznie (co daje chronologicznie, gdyż na końcu URI jest timestamp) od najnowszego
        results.sort(key=lambda x: x['uri'], reverse=True)
        results = results[:limit]
        
        report = f"📖 **Dziennik Sesji: {agent_name}** (Ostatnie {len(results)} wpisów)\n\n"
        for res in results:
            report += f"--- \n"
            report += f"{res['text']}\n\n"
            
        return report
    except Exception as e:
        return f"Błąd odczytu dziennika: {e}"

# ==================== TEMPORAL KNOWLEDGE GRAPH (Pomysł 2) ====================

@mcp.tool()
async def gce_kg_add(subject: str, predicate: str, object: str, 
                     valid_from: Optional[str] = None, 
                     valid_to: Optional[str] = None) -> str:
    """Dodaje fakt do temporalnego grafu wiedzy w SQLite (np. Max -> works_on -> SOR App)."""
    try:
        success = knowledge_graph.add_triple(
            subject=subject, 
            predicate=predicate, 
            object=object, 
            valid_from=valid_from, 
            valid_to=valid_to
        )
        if success:
            return f"✅ Dodano fakt do grafu: ({subject}) --[{predicate}]--> ({object})"
        return "Błąd podczas dodawania faktu."
    except Exception as e:
        return f"Błąd KG: {e}"

@mcp.tool()
async def gce_kg_invalidate(subject: str, predicate: str, object: str, 
                            ended: Optional[str] = None) -> str:
    """Oznacza fakt w grafie jako nieaktualny (ustawia datę valid_to)."""
    try:
        count = knowledge_graph.invalidate_triple(
            subject=subject, 
            predicate=predicate, 
            object=object, 
            ended=ended
        )
        return f"🚫 Oznaczono fakt jako nieaktualny. Zaktualizowano {count} rekord(ów)."
    except Exception as e:
        return f"Błąd KG: {e}"

@mcp.tool()
async def gce_kg_query(entity: str, as_of: Optional[str] = None, direction: str = "both") -> str:
    """Przeszukuje powiązania encji z uwzględnieniem czasu (as_of w formacie YYYY-MM-DD HH:MM:SS)."""
    try:
        results = knowledge_graph.query_entity(entity=entity, as_of=as_of, direction=direction)
        if not results:
            return f"Brak powiązań dla encji '{entity}'" + (f" na dzień {as_of}" if as_of else "") + "."
            
        report = f"🕸️ **Graf Wiedzy: {entity}**"
        if as_of:
            report += f" (stan na: {as_of})"
        report += "\n\n"
        
        for res in results:
            status = "🟢 Aktywny" if not res['valid_to'] else f"🔴 Wygasł ({res['valid_to']})"
            report += f"- ({res['subject']}) --[{res['predicate']}]--> ({res['object']})  [{status}, od: {res['valid_from']}]\n"
            
        return report
    except Exception as e:
        return f"Błąd KG: {e}"

@mcp.tool()
async def gce_kg_timeline(entity: Optional[str] = None) -> str:
    """Zwraca chronologiczną oś czasu faktów dla encji (lub całego homelaba)."""
    try:
        results = knowledge_graph.get_timeline(entity=entity)
        if not results:
            return "Brak historii faktów."
            
        report = f"🕒 **Oś Czasu: " + (entity if entity else "Homelab / Projekty") + "**\n\n"
        for res in results:
            status = "wciąż aktualne" if not res['valid_to'] else f"do: {res['valid_to']}"
            report += f"- **[{res['valid_from']}]**: ({res['subject']}) --[{res['predicate']}]--> ({res['object']}) ({status})\n"
        return report
    except Exception as e:
        return f"Błąd KG: {e}"

@mcp.tool()
async def gce_kg_stats() -> str:
    """Pobiera statystyki temporalnego grafu wiedzy SQLite."""
    try:
        stats = knowledge_graph.get_stats()
        return (
            f"📊 **Statystyki Temporalnego Grafu GCE**\n\n"
            f"- Wszystkich faktów (trójek): {stats['total_facts']}\n"
            f"- Aktywnych faktów: {stats['active_facts']}\n"
            f"- Wygasłych faktów: {stats['expired_facts']}\n"
            f"- Unikalnych encji (szacunkowo): {stats['unique_entities']}\n"
        )
    except Exception as e:
        return f"Błąd statystyk KG: {e}"

if __name__ == "__main__":
    mcp.run()
