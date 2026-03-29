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

@mcp.tool()
async def gce_add_resource(uri: str, content: str = "", abstract: str = "") -> str:
    """Indeksuje nowy zasób w bazie GCE (podział na fragmenty i wektoryzacja)."""
    try:
        # Jeśli content jest pusty, spróbuj odczytać plik z dysku (traktując uri jako ścieżkę)
        if not content:
            if os.path.exists(uri):
                with open(uri, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                return f"Błąd: Nie podano treści, a plik '{uri}' nie istnieje lokalnie."

        # Jeśli abstract jest pusty, wygeneruj go automatycznie (L0 Context)
        if not abstract:
            logger.info(f"Generowanie technicznego abstraktu dla {uri}...")
            try:
                # Prompt zoptymalizowany pod kątem gęstości informacji (L0 Context)
                prompt = f"""Wygeneruj ultrazwięzły, techniczny abstrakt (max 150 znaków) dla zasobu: {uri}
                Format: [Typ/Technologia] Główny cel, kluczowe parametry lub funkcje.
                
                TREŚĆ (początek):
                {content[:2500]}"""
                
                abstract = await quota_manager.generate_content(prompt)
                abstract = abstract.strip().replace("\n", " ")
                logger.info(f"Abstrakt wygenerowany: {abstract}")
            except Exception as e:
                logger.warning(f"Nie udało się wygenerować abstraktu: {e}")
                abstract = f"Zasób: {uri}"

        # Inteligentne dzielenie tekstu (OpenSpace style)
        logger.info(f"Dzielenie {uri} na fragmenty (Recursive Markdown-Aware)...")
        chunks = text_splitter.split_text(content)
        
        doc_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_uri = f"{uri}#chunk{i}"
            # Wektoryzujemy Abstrakt + Fragment dla lepszej retencji semantycznej
            vector = await embedding_engine.embed_text(f"{abstract}\n\n{chunk}")
            
            doc_chunks.append({
                "uri": chunk_uri,
                "text": chunk,
                "abstract": abstract,
                "vector": vector,
                "metadata": "{}"
            })
        
        vector_store.add_documents(doc_chunks)
        return f"Sukces. Zasób {uri} dodany z abstraktem ({len(doc_chunks)} fragmentów)."
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
        report += f"- DB Path: `{db_stats['db_path']}`\n\n"
        
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
