import os
import lancedb
from lancedb.pydantic import Vector, LanceModel
import logging
from config import settings
from typing import List

from lancedb.rerankers import RRFReranker
from typing import List, Optional

logger = logging.getLogger("VectorStore")

class ContextDocument(LanceModel):
    uri: str
    text: str
    abstract: str = ""
    vector: Vector(768)
    metadata: str = "{}"

class VectorStore:
    def __init__(self):
        os.makedirs(settings.GCE_DB_PATH, exist_ok=True)
        self.db = lancedb.connect(settings.GCE_DB_PATH)
        self.table_name = "context_store"
        
        if self.table_name not in self.db.table_names():
            self.table = self.db.create_table(self.table_name, schema=ContextDocument)
            logger.info(f"Created new LanceDB table: {self.table_name}")
        else:
            self.table = self.db.open_table(self.table_name)
            logger.info(f"Opened LanceDB table: {self.table_name}")
        
        # Inicjalizacja rerankera RRF (Reciprocal Rank Fusion)
        self.reranker = RRFReranker()
        
        # Tworzenie indeksu FTS dla wyszukiwania pełnotekstowego
        try:
            self.table.create_fts_index("text", replace=True)
            logger.info("FTS index created/refreshed on 'text' column.")
        except Exception as e:
            logger.warning(f"Could not create FTS index: {e}")

    def add_documents(self, documents: List[dict]):
        """Dodaje listę fragmentów dokumentów do bazy."""
        if not documents:
            return
            
        base_uri = documents[0]['uri'].split('#')[0]
        try:
            self.table.delete(f"uri LIKE '{base_uri}%'")
        except Exception as e:
            logger.debug(f"No existing documents to delete for {base_uri}: {e}")
            
        self.table.add(documents)
        logger.info(f"Added/Updated {len(documents)} chunks for: {base_uri}")

    def hybrid_search(self, query: str, query_vector: List[float], limit: int = 5, where: Optional[str] = None) -> List[dict]:
        """
        Wyszukiwanie hybrydowe: natywne połączenie wyników wektorowych i FTS przy użyciu RRF.
        Obsługuje opcjonalne filtrowanie po metadanych (SQL-like syntax).
        """
        try:
            # LanceDB Hybrid wymaga jawnego podania .vector() i .text()
            search_builder = self.table.search(query_type="hybrid") \
                .vector(query_vector) \
                .text(query) \
                .rerank(self.reranker) \
                .limit(limit)
            
            if where:
                search_builder = search_builder.where(where)
                
            results = search_builder.to_list()
            
            # Oznaczamy źródło dla celów diagnostycznych (LanceDB hybrid nie dodaje go automatycznie w ten sposób)
            for res in results:
                res['_source'] = 'hybrid_rrf'
                
            return results
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback do zwykłego wyszukiwania wektorowego w razie błędu FTS/Hybrid
            return self.table.search(query_vector).limit(limit).to_list()


    def get_by_uri(self, uri: str) -> dict:
        """Pobiera pojedynczy dokument po jego unikalnym URI."""
        results = self.table.search().where(f"uri = '{uri}'").to_list()
        return results[0] if results else None

vector_store = VectorStore()
