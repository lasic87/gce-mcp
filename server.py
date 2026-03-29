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
    
    # Przechwycenie śladu stosu i kontekstu
    import traceback
    tb = traceback.format_exc()
    
    mining_context = f"Błąd w narzędziu: {tool_name}\nBłąd: {str(error)}\nTraceback:\n{tb}\nDodatkowy kontekst: {context}"
    
    try:
        # Wywołanie logiki Mining Patterns dla błędu
        report = await gce_mine_patterns(mining_context)
        return f"🚨 **GCE GUARDIAN DIAGNOSTIC**\n\n{report}\n\n*Wskazówka: Powyższa analiza bazuje na Twojej historii błędów w GCE.*"
    except Exception as e:
        return f"Błąd krytyczny w Guardianie: {e}\nOryginalny błąd: {error}"

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
async def gce_add_memory(content: str, label: str) -> str:
    """Zapisuje fakt lub preferencję użytkownika bezpośrednio w GCE."""
    try:
        safe_label = re.sub(r'[^a-z0-9]', '_', label.lower())
        uri = f"gce://user/memories/{safe_label}"
        
        try:
            prompt = f"Wygeneruj bardzo krótką, merytoryczną etykietę (max 8 słów) dla faktu:\n{content[:500]}"
            abstract = await quota_manager.generate_content(prompt)
            abstract = abstract.strip().strip('"').replace("\n", " ")
        except:
            abstract = f"Memory: {label}"

        vector = await embedding_engine.embed_text(f"{abstract}\n\n{content}")
        
        vector_store.add_documents([{
            "uri": uri,
            "text": content,
            "abstract": abstract,
            "vector": vector,
            "metadata": "{}"
        }])
        
        return f"Zapamiętano: {uri} (Label: {abstract})"
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
            status = "🔴 BLOCKED" if m['is_blocked'] else "🟢 ACTIVE"
            report += f"- **{m['name']}** [{status}]\n"
            report += f"  RPM: {m['rpm']}/{m['rpm_limit']} | RPD: {m['rpd']}/{m['rpd_limit']}\n"
            
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
