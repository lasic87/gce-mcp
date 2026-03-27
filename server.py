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
            logger.info(f"Generowanie abstraktu dla {uri}...")
            try:
                # Prompt inspirowany OpenSpace dla lepszego kontekstu L0
                prompt = f"Wygeneruj bardzo krótki, techniczny abstrakt (max 2 zdania) dla pliku: {uri}\n\nTREŚĆ:\n{content[:2000]}"
                abstract = await quota_manager.generate_content(prompt)
                logger.info(f"Abstrakt wygenerowany: {abstract[:100]}...")
            except Exception as e:
                logger.warning(f"Nie udało się wygenerować abstraktu: {e}")
                abstract = f"Zasób: {uri}"

        # Inteligentne dzielenie tekstu (OpenSpace style)
        logger.info(f"Dzielenie {uri} na fragmenty (Recursive)...")
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
        logger.error(f"Index error for {uri}: {e}")
        return f"Błąd indeksowania: {e}"

@mcp.tool()
async def gce_add_memory(content: str, label: str) -> str:
    """Zapisuje fakt lub preferencję użytkownika bezpośrednio w GCE."""
    try:
        safe_label = re.sub(r'[^a-z0-9]', '_', label.lower())
        uri = f"gce://user/memories/{safe_label}"
        
        try:
            abstract = await quota_manager.generate_content(f"Krótka etykieta dla: {content[:500]}")
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
        
        return f"Zapamiętano: {uri}"
    except Exception as e:
        logger.error(f"Memory error: {e}")
        return f"Błąd zapisu wspomnienia: {e}"

@mcp.tool()
async def gce_consolidate_memories(content: str, category: str = "general") -> str:
    """Wyodrębnia atomowe fakty z tekstu i zapisuje je jako osobne wspomnienia."""
    prompt = f"""
    Wyodrębnij atomowe fakty (preferencje, parametry, rozwiązania) z tekstu. 
    Krótkie, konkretne zdania od '-' bez dodatkowego komentarza.

    TEKST:
    {content}
    """
    
    try:
        response = await quota_manager.generate_content(prompt)
        facts = [line.strip("- ").strip() for line in response.split('\n') if line.strip("- ").strip()]
        
        if not facts:
            return "Brak istotnych faktów."
            
        count = 0
        for fact in facts:
            label_words = re.sub(r'[^a-z0-9\s]', '', fact.lower()).split()
            label = "_".join(label_words[:4])
            await gce_add_memory(content=fact, label=f"{category}_{label}")
            count += 1
            
        return f"Zapisano {count} faktów w kategorii '{category}'."
    except Exception as e:
        logger.error(f"Consolidation error: {e}")
        return f"Błąd konsolidacji: {e}"

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
        logger.error(f"Search error: {e}")
        return f"Błąd wyszukiwania: {e}"

if __name__ == "__main__":
    mcp.run()
