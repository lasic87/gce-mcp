import os
import re
import logging
from typing import List, Dict, Optional, Any
from mcp.server.fastmcp import FastMCP
from config import settings
from vector_store import vector_store
from embedding_engine import embedding_engine
from quota_manager import quota_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GCE-MCP")

mcp = FastMCP("GCE-MCP")

@mcp.tool()
async def gce_add_resource(uri: str, content: str, abstract: str = "") -> str:
    """Indeksuje nowy zasób w bazie GCE (podział na fragmenty i wektoryzacja)."""
    try:
        # TODO: przejść na RecursiveCharacterTextSplitter
        chunks = [content[i:i+2000] for i in range(0, len(content), 1800)]
        
        doc_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_uri = f"{uri}#chunk{i}"
            vector = await embedding_engine.embed_text(f"{abstract}\n\n{chunk}")
            
            doc_chunks.append({
                "uri": chunk_uri,
                "text": chunk,
                "abstract": abstract,
                "vector": vector,
                "metadata": "{}"
            })
        
        vector_store.add_documents(doc_chunks)
        return f"OK. Zindeksowano {len(doc_chunks)} fragmentów dla {uri}"
    except Exception as e:
        logger.error(f"Index error: {e}")
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
